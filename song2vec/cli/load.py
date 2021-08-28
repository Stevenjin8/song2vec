"""Functions to load data into the db. I think a functional approach makes more sense
when processing data.
"""
import json
import os
from typing import Callable, Generator, Iterable, List, Set, Type

import sqlalchemy
from tqdm import tqdm

from song2vec import db

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
) -> Generator[db.Artist, None, None]:
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
                yield {"uri": uri, "name": name}


def create_albums(
    playlists: List[dict], album_uris: Set[str]
) -> Generator[db.Album, None, None]:
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
                yield {"uri": uri, "name": name}


def create_tracks(
    playlists: List[dict], track_uris: Set[str]
) -> Generator[db.Track, None, None]:
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
            album_uri = track["album_uri"].split(":")[-1]
            artist_uri = track["artist_uri"].split(":")[-1]
            if uri not in track_uris:
                track_uris.add(uri)
                yield {
                    "uri": uri,
                    "name": name,
                    "album_uri": album_uri,
                    "artist_uri": artist_uri,
                }


def create_playlists(playlists: List[dict], *_) -> Generator[db.Playlist, None, None]:
    """Create objects representing playlists in the database. No need to worry about
    duplicate playlists.

    Arguments:
        playlists: A list of playlists as stored in the Spotify dataset.
    """
    for playlist in playlists:
        name = playlist["name"]
        pid = playlist["pid"]
        yield {"name": name, "pid": pid}


def create_associations(
    playlists: List[dict], *_
) -> Generator[db.Association, None, None]:
    """Create intermediate objects between artists and playlists.

    Arguments:
        playlists: A list of playlists as stored in the Spotify dataset.
    """
    for playlist in playlists:
        for track in playlist["tracks"]:
            track_uri = track["track_uri"].split(":")[-1]
            playlist_id = playlist["pid"]
            yield {"track_uri": track_uri, "playlist_id": playlist_id}


def load_objects(
    cls: db.Base,
    db_url: str,
    filenames: List[str],
    create_objects: Callable[[List[dict], Set[str]], Iterable[db.Base]],
) -> None:
    """Load objects into the database. This function is mostly here to get rid of
    boilerplate for multiprocessing.

    Arguments:
        db_url: the url of the database (e.g. "sqlite:///data/db").
        filenames: list of file paths that contain the dataset.
        create_objects: a callable like `create_albums`. Must take two arguments:
            a list of playlists and a set of strings (usually ids of already-created
            objects), and return Sqlalchemy ORM objects.
        mapper: the object type.
    """
    ids = set()
    engine = sqlalchemy.create_engine(db_url, connect_args={"timeout": 10})
    # pylint: disable=invalid-name
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    for slice_path in tqdm(filenames):
        session = Session()
        with open(slice_path) as file:
            data_slice = json.load(file)
            # iterate through the generator so we don't keep all the files open.
            objs = create_objects(data_slice["playlists"], ids)
        session.bulk_insert_mappings(sqlalchemy.inspect(cls), objs)
        session.commit()
        session.close()


def remove_unique_tracks(session: sqlalchemy.orm.Session) -> None:
    """Remove tracks that only occur in one playlist and playlists that contain a single track."""

    single_track_query = (
        session.query(db.Association.track_uri)
        .group_by(db.Association.track_uri)
        .having(sqlalchemy.func.count(db.Association.playlist_id) == 1)
    )

    single_playlist_query = (
        session.query(db.Association.playlist_id)
        .group_by(db.Association.playlist_id)
        .having(sqlalchemy.func.count(db.Association.track_uri) <= 1)
    )

    while True:
        session.execute("pragma foreign_keys=on")
        session.query(db.Track).where(
            db.Track.uri.in_(single_track_query.subquery().select())
        ).delete(synchronize_session=False)
        session.query(db.Playlist).where(
            db.Playlist.pid.in_(single_playlist_query.subquery().select())
        ).delete(synchronize_session=False)

        session.commit()
        session.flush()

        if not single_playlist_query.limit(1).all():
            break

    session.query(db.Playlist).where(
        ~db.Playlist.pid.in_(
            session.query(db.Association.playlist_id).distinct().subquery().select()
        )
    ).delete(synchronize_session=False)
    session.query(db.Track).where(
        ~db.Track.uri.in_(
            session.query(db.Association.track_uri).distinct().subquery().select()
        )
    ).delete(synchronize_session=False)
    session.flush()
    session.commit()
