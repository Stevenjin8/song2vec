"""Run the cli when running the module."""
# This is a Click convention
# pylint: disable=import-outside-toplevel
import multiprocessing

import click
from sqlalchemy.orm.session import sessionmaker
from song2vec.cli.load import (
    create_albums,
    create_artists,
    create_associations,
    create_playlists,
    create_tracks,
    load_objects,
    remove_unique_tracks,
)
from sqlalchemy import inspect


@click.group()
def cli():
    """Main cli group."""


@click.command()
@click.option(
    "--raw-data-dir",
    type=str,
    default="data/raw/data",
    help="Path to folder containing the json files with the Spotify dataset.",
)
@click.option(
    "--db-url",
    type=str,
    default="sqlite:///data/db",
    help="URL to the database for Sqlalchemy (e.g. sqlite:///data/db)",
)
@click.option(
    "--remove-unique/--no-remove-unique",
    type=bool,
    default=False,
    help="Make sure all tracks appear in multiple playlists and that all playlists have multiple tracks.",
)
def load_playlists(raw_data_dir: str, db_url: str, remove_unique: bool):
    """Load the Million Playlist Dataset into a SQLite database."""
    import sqlalchemy
    from song2vec import db

    from . import load

    # Set up connection
    engine = sqlalchemy.create_engine(db_url)
    db.Base.metadata.create_all(engine)

    # Create processes to read files and upload objects. Note that SQLite allows for
    # nonexistent foreign keys, which is why we can upload everything at the same time
    # without integrity errors.
    filenames = load.get_slices(raw_data_dir)
    processes = []
    processes.append(
        multiprocessing.Process(
            target=load_objects,
            args=(db.Artist, db_url, filenames, create_artists),
        )
    )
    processes.append(
        multiprocessing.Process(
            target=load_objects, args=(db.Album, db_url, filenames, create_albums)
        )
    )
    processes.append(
        multiprocessing.Process(
            target=load_objects, args=(db.Track, db_url, filenames, create_tracks)
        )
    )
    processes.append(
        multiprocessing.Process(
            target=load_objects,
            args=(db.Playlist, db_url, filenames, create_playlists),
        )
    )
    processes.append(
        multiprocessing.Process(
            target=load_objects,
            args=(db.Association, db_url, filenames, create_associations),
        )
    )

    for process in processes:
        process.start()

    for process in processes:
        process.join()

    playlist_id_index = sqlalchemy.Index("playlist_id", db.Association.playlist_id)
    track_uri_index = sqlalchemy.Index("track_uri", db.Association.track_uri)
    playlist_id_index.create(bind=engine)
    track_uri_index.create(bind=engine)

    if remove_unique:
        remove_unique_tracks(sessionmaker(bind=engine)())  # add this as an option.


cli.add_command(load_playlists)


if __name__ == "__main__":
    cli()
