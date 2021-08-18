"""Functions to load data into the db."""
import os
from typing import List

import sqlalchemy
from song2vec import models

from . import settings


def get_slices(raw_data_dir: str) -> List[str]:
    """Get files names containing the slices of the data."""
    return [
        os.path.join(raw_data_dir, filename)
        for filename in os.listdir(raw_data_dir)
        if settings.DATA_FILE_RE.match(filename)
    ]


def create_artists(session: sqlalchemy.orm.Session, playlists: List[dict]) -> None:
    """There is probably a more efficient way to do this (without loading everything
    into memory)."""
    for playlist in playlists:
        for track in playlist["tracks"]:
            uri = track["artist_uri"]
            name = track["artist_name"]
            exists = bool(
                session.query(models.Artist.uri)
                .filter(models.Artist.uri == uri)
                .count()
            )
            if not exists:
                artist = models.Artist(uri=uri, name=name)
                session.add(artist)
    session.commit()
