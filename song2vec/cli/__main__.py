# pylint: disable=import-outside-toplevel
import click


@click.group()
def cli():
    pass


@click.command()
def load_playlists():
    from . import load

    raw_data_dir = "data/raw/data"

    print(load.get_slices(raw_data_dir))


cli.add_command(load_playlists)


if __name__ == "__main__":
    cli()
