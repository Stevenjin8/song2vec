"""Tests the datasets."""
import os

from click.testing import CliRunner
from torch import tensor, testing

from song2vec import db
from song2vec.cli.__main__ import load_playlists
from song2vec.data.datasets import MillionPlaylistDataset

from ..db.utils import AbstractDbTestCase


class MillionPlaylistDatasetTestCase(AbstractDbTestCase):
    """Tests for the mpd dataset."""

    cli_runner: CliRunner
    db_path: str = "tests/data/test.db"

    @classmethod
    def setUpClass(cls):
        # Create a fresh db.
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
        cls.db_url = f"sqlite:///{cls.db_path}"

        super().setUpClass()

        db.Base.metadata.create_all(cls.engine)

        cls.cli_runner = CliRunner()
        cls.cli_runner.invoke(
            load_playlists, ["--raw-data-dir", "tests/data", "--db-url", cls.db_url]
        )

    def setUp(self) -> None:
        self.dataset = MillionPlaylistDataset(self.db_url)
        return super().setUp()

    def test_keys(self):
        """Test that the `keys` method works."""
        self.assertCountEqual(
            self.dataset.keys, (x for x, in self.session.query(db.Playlist.pid).all())
        )

    def test_length(self):
        """Test that the len method works as expected."""
        self.assertEqual(self.session.query(db.Playlist).count(), len(self.dataset))

    def test_single_getitem(self):
        """Tests that we can get items from the db."""
        key = "0"
        item = self.dataset[key]
        self.assertEqual(
            list(item.shape)[0], len(self.dataset.multi_hot_encoder.indices)
        )
        self.assertTrue(item.is_sparse)
        self.assertTrue(item.is_coalesced)
        self.assertGreater(item.values().sum().item(), 0)
        self.assertTrue(all(item.values() == 1.0))

    def test_indices(self):
        """Test that the indices are the correct ones."""
        key = "0"
        item = self.dataset[key]
        expected_indices = [
            self.dataset.multi_hot_encoder.indices[x]
            for x, in self.session.query(db.Association.track_uri)
            .where(db.Association.playlist_id == key)
            .all()
        ]
        testing.assert_equal(item.indices()[0].sort(), tensor(expected_indices).sort())

    def test_multiple_indices(self):
        """Test that we can query by multiple indices."""
        key = "0"

        expected = self.dataset[key].to_dense()
        actual = self.dataset[key, key].to_dense()
        testing.assert_equal(expected, actual[0])
        testing.assert_equal(expected, actual[1])
