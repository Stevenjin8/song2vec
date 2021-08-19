"""Run the cli when running the module."""
# This is a Click convention
# pylint: disable=import-outside-toplevel
import multiprocessing

import click
from song2vec.cli.load import (
    create_albums,
    create_artists,
    load_playlist_track_association,
    create_playlists,
    create_tracks,
    load_objects,
)


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
def load_playlists(raw_data_dir: str, db_url: str):
    """Load the Million Playlist Dataset into a SQLite database."""
    import sqlalchemy
    from song2vec import models

    from . import load

    # Set up connection
    engine = sqlalchemy.create_engine(db_url)
    models.Base.metadata.create_all(engine)

    # Create processes to read files and upload objects. Note that SQLite allows for
    # nonexistent foreign keys, which is why we can upload everything at the same time
    # without integrity errors.
    filenames = load.get_slices(raw_data_dir)
    artist_process = multiprocessing.Process(
        target=load_objects,
        args=(db_url, filenames, create_artists),
    )
    album_process = multiprocessing.Process(
        target=load_objects, args=(db_url, filenames, create_albums)
    )
    track_process = multiprocessing.Process(
        target=load_objects, args=(db_url, filenames, create_tracks)
    )
    playlist_process = multiprocessing.Process(
        target=load_objects,
        args=(db_url, filenames, create_playlists),
    )
    association_process = multiprocessing.Process(
        target=load_playlist_track_association, args=(db_url, filenames)
    )

    artist_process.start()
    album_process.start()
    track_process.start()
    playlist_process.start()
    association_process.start()


cli.add_command(load_playlists)


if __name__ == "__main__":
    cli()
