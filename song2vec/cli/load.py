"""Functions to load data into the db. I think a functional approach makes more sense
when processing data.
"""
import json
import os
from typing import Callable, Generator, Iterable, List, Set

import sqlalchemy
from tqdm import tqdm
from song2vec import models

from . import settings


def get_slices(raw_data_dir: str) -> List[str]:
    """Get files names containing the slices of the data."""
    return [
        os.path.join(raw_data_dir, filename)
        for filename in os.listdir(raw_data_dir)
        if settings.DATA_FILE_RE.match(filename)
    ]


def create_artists(
    playlists: List[dict], artist_uris: Set[str]
) -> Generator[models.Artist, None, None]:
    """Create objects representing the artists in the database.

    Arguments:
        playlists: A list of playlists as stored in the Spotify dataset.
        artist_uris: URI of artists that have already been inserted. We need this
            because the data is denormalized.

    Yields:
        The next new artist.
    """
    for playlist in playlists:
        for track in playlist["tracks"]:
            uri = track["artist_uri"].split(":")[-1]
            name = track["artist_name"]
            if uri not in artist_uris:
                artist_uris.add(uri)
                yield models.Artist(uri=uri, name=name)


def create_albums(
    playlists: List[dict], album_uris: Set[str]
) -> Generator[models.Album, None, None]:
    """Create objects representing the albums in the database.

    Arguments:
        playlists: A list of playlists as stored in the Spotify dataset.
        album_uris: URI of albums that have already been inserted. We need this because
            the data is denormalized.

    Yields:
        The next new album.
    """
    for playlist in playlists:
        for track in playlist["tracks"]:
            uri = track["album_uri"].split(":")[-1]
            name = track["album_name"]
            if uri not in album_uris:
                album_uris.add(uri)
                yield models.Album(uri=uri, name=name)


def create_tracks(
    playlists: List[dict], track_uris: Set[str]
) -> Generator[models.Track, None, None]:
    """Create objects representing the tracks (i.e. songs) in the database.

    Arguments:
        playlists: A list of playlists as stored in the Spotify dataset.
        track_uris: URI of tracks that have already been inserted. We need this because
            the data is denormalized.

    Yields:
        The next new track.
    """
    for playlist in playlists:
        for track in playlist["tracks"]:
            uri = track["track_uri"].split(":")[-1]
            name = track["track_name"]
            album_uri = track["album_uri"]
            artist_uri = track["artist_uri"]
            if uri not in track_uris:
                track_uris.add(uri)
                yield models.Track(
                    uri=uri, name=name, album_uri=album_uri, artist_uri=artist_uri
                )


def create_playlists(
    playlists: List[dict], *_
) -> Generator[models.Playlist, None, None]:
    """Create objects representing playlists in the dabase. No need to worry about
    duplicate playlists.

    Arguments:
        playlists: A list of playlists as storefd in the Spotify dataset.
    """
    for playlist in playlists:
        name = playlist["name"]
        pid = playlist["pid"]
        yield models.Playlist(name=name, pid=pid)


def load_objects(
    db_url: str,
    filenames: List[str],
    create_objects: Callable[[List[dict], Set[str]], Iterable[models.Base]],
) -> None:
    """Load objects into the database. This function is mostly here to get rid of
    boilerplate for multiprocessing.

    Arguments:
        db_url: the url of the database (e.g. "sqlite:///data/db").
        filenames: list of file paths that contain the dataset.
        create_objects: a callable like `create_albums`. Must take two arguments:
            a list of playlists and a set of strings (usually ids of already-created
            objects), and return Sqlalchemy ORM objects.
    """
    ids = set()
    engine = sqlalchemy.create_engine(db_url)
    # pylint: disable=invalid-name
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    for slice_path in tqdm(filenames):
        session = Session()
        with open(slice_path) as file:
            data_slice = json.load(file)
        session.add_all(create_objects(data_slice["playlists"], ids))
        session.commit()
        session.close()


def load_playlist_track_association(db_url: str, filenames: List[str]) -> None:
    """Load relationships between playlists and tracks to the intermediate table. We
    have to do this a bit differently because the intermediate table is not an ORM.

    Arguments:
        db_url: the url of the database (e.g. "sqlite:///data/db").l
        filenames: list of file paths that contain the dataset.
    """
    ins = models.track_playlist_association.insert()
    engine = sqlalchemy.create_engine(db_url)
    ins.bind = engine
    conn = engine.connect()

    for filename in tqdm(filenames):
        with open(filename) as file:
            data_slice = json.load(file)
        relationships = []
        for playlist in data_slice["playlists"]:
            for track in playlist["tracks"]:
                relationships.append(
                    {"track_uri": track["track_uri"], "playlist_id": playlist["pid"]}
                )
        conn.execute(ins, relationships)
