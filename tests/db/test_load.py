"""Tests for Click data loading commands."""
import os
import sqlite3

from click.testing import CliRunner, Result

from song2vec import db
from song2vec.cli.__main__ import load_playlists

from .utils import AbstractDbTestCase


class LoadTestCase(AbstractDbTestCase):
    """Test that we can load data properly."""

    cli_runner: CliRunner
    result: Result
    db_path: str = "tests/data/test.db"

    @classmethod
    def setUpClass(cls):
        # Create a fresh db.
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
        cls.db_url = f"sqlite:///{cls.db_path}"
        sqlite3.connect(cls.db_path)

        super().setUpClass()

        db.Base.metadata.create_all(cls.engine)

        cls.cli_runner = CliRunner()
        cls.result = cls.cli_runner.invoke(
            load_playlists, ["--raw-data-dir", "tests/data", "--db-url", cls.db_url]
        )

    def test_exit_code(self):
        """Test that the load command ran without errors."""
        self.assertEqual(0, self.result.exit_code)

    def test_db_counts(self):
        """Test that the database was populated correctly."""
        artists_query = self.session.query(db.Artist)
        self.assertGreater(artists_query.count(), 0)
        for artist in artists_query:
            self.assertTrue(artist.tracks)
            self.assertTrue(artist.name)
            self.assertTrue(artist.uri)

        album_query = self.session.query(db.Album)
        self.assertGreater(album_query.count(), 0)
        for album in album_query:
            self.assertTrue(album.tracks)
            self.assertTrue(album.name)
            self.assertTrue(album.uri)

        playlist_query = self.session.query(db.Playlist)
        self.assertGreater(playlist_query.count(), 0)
        for playlist in playlist_query:
            self.assertTrue(playlist.track_associations)
            self.assertTrue(playlist.name)
            self.assertIsNotNone(playlist.pid)

        track_query = self.session.query(db.Track)
        self.assertGreater(track_query.count(), 0)
        for track in track_query:
            self.assertTrue(track.playlist_associations)
            self.assertTrue(track.name)
            self.assertTrue(track.uri)
            self.assertTrue(track.album)
            self.assertTrue(track.artist)

    def test_db_values(self):
        """Test that the values in the db are correct."""
        throwbacks = self.session.query(db.Playlist).filter(db.Playlist.pid == 0).one()
        self.assertEqual(throwbacks.name, "Throwbacks")
        self.assertEqual(len(throwbacks.track_associations), 1)
        toxic = throwbacks.track_associations[0].track
        self.assertEqual(toxic.name, "Toxic")
        self.assertEqual(len(toxic.playlist_associations), 2)
        self.assertEqual(toxic.album.name, "In The Zone")
