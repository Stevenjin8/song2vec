"""Tests for ORM models. See
https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
"""
# pylint: disable=invalid-name
from song2vec import models
from .utils import AbstractDbTestCase


class TestModelsTestCase(AbstractDbTestCase):
    """Tests for the orm."""

    def setUp(self):
        """Create the db, add the models and create a session."""
        self.session = self.Session()
        models.Base.metadata.create_all(self.engine)

        self.artist_kwargs = {
            "uri": "spotify:artist:3V2paBXEoZIAhfZRJmo2jL",
            "name": "Degiheugi",
        }
        self.artist = models.Artist(**self.artist_kwargs)

        self.album_kwargs = {
            "uri": "spotify:album:3lUSlvjUoHNA8IkNTqURqd",
            "name": "Endless Smile",
        }
        self.album = models.Album(**self.album_kwargs)

        self.track0_kwargs = {
            "uri": "spotify:track:7vqa3sDmtEaVJ2gcvxtRID",
            "name": "Betty",
            "duration": 235534,
            "album": self.album,
            "artist": self.artist,
        }
        self.track0 = models.Track(**self.track0_kwargs)

        self.track1_kwargs = {
            "uri": "spotify:track:23EOmJivOZ88WJPUbIPjh6",
            "name": "Finalement",
            "duration": 166264,
            "album": self.album,
            "artist": self.artist,
        }
        self.track1 = models.Track(**self.track1_kwargs)

        self.tracks = [self.track0, self.track1]

        self.playlist_kwargs = {"pid": 5, "name": "musical", "tracks": self.tracks}
        self.playlist = models.Playlist(**self.playlist_kwargs)

        self.session.add_all((self.artist, self.album, *self.tracks, self.playlist))
        self.session.commit()

    def tearDown(self):
        """Delete all the tables."""
        models.Base.metadata.drop_all(self.engine)

    def test_query(self):
        """Test that we can query the objects as expected."""
        # Check the correct number of objects were created
        self.assertEqual(1, self.session.query(models.Artist).count())
        self.assertEqual(1, self.session.query(models.Album).count())
        self.assertEqual(1, self.session.query(models.Playlist).count())
        self.assertEqual(2, self.session.query(models.Track).count())

        # Test item contents
        self.assertDictObjEqual(
            self.album_kwargs, self.session.query(models.Album).first()
        )
        self.assertDictObjEqual(
            self.artist_kwargs, self.session.query(models.Artist).first()
        )
        # This one is a bit sketch as the order of the tracks might be in different.
        self.assertDictObjEqual(
            self.playlist_kwargs, self.session.query(models.Playlist).first()
        )

        for track_kwargs in (self.track0_kwargs, self.track1_kwargs):
            uri = track_kwargs["uri"]
            track = (
                self.session.query(models.Track).filter(models.Track.uri == uri).one()
            )
            self.assertDictObjEqual(track_kwargs, track)

    def test_delete(self):
        """Test that objects are being deleted correctly."""
        # Deleting an an artist should delete all tracks
        self.session.delete(self.album)
        self.assertEqual(0, self.session.query(models.Album).count())
        self.assertEqual(0, self.session.query(models.Track).count())
        self.assertEqual(1, self.session.query(models.Artist).count())
        self.assertEqual(1, self.session.query(models.Playlist).count())
        self.session.rollback()

        self.session.delete(self.artist)
        self.assertEqual(1, self.session.query(models.Album).count())
        self.assertEqual(0, self.session.query(models.Track).count())
        self.assertEqual(0, self.session.query(models.Artist).count())
        self.assertEqual(1, self.session.query(models.Playlist).count())
        self.session.rollback()

        self.session.delete(self.track1)
        self.assertEqual(1, self.session.query(models.Album).count())
        self.assertEqual(1, self.session.query(models.Track).count())
        self.assertEqual(1, self.session.query(models.Artist).count())
        self.assertEqual(1, self.session.query(models.Playlist).count())
        self.session.rollback()

        self.session.delete(self.playlist)
        self.assertEqual(1, self.session.query(models.Album).count())
        self.assertEqual(2, self.session.query(models.Track).count())
        self.assertEqual(1, self.session.query(models.Artist).count())
        self.assertEqual(0, self.session.query(models.Playlist).count())
