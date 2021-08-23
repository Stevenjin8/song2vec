"""Utility functions for testing the db."""
# pylint: disable=invalid-name
from unittest import TestCase

from sqlalchemy import create_engine, engine, orm

from song2vec import db


class AbstractDbTestCase(TestCase):
    """Abstract test case for tests involving the database."""

    engine: engine.Engine
    session: orm.session.Session
    db_url: str = "sqlite:///:memory:"

    def assertDictObjEqual(self, dict_: dict, obj: db.Base):
        """Assert that `dict_` and `obj` have  similar key/attribute-value pairs."""
        for key, value in dict_.items():
            self.assertTrue(hasattr(obj, key))
            self.assertEqual(getattr(obj, key), value)

    @classmethod
    def setUpClass(cls):
        """Create a db in memory."""
        cls.engine = create_engine(cls.db_url)
        cls.Session = orm.sessionmaker(bind=cls.engine)

    def setUp(self) -> None:
        self.session = self.Session()
        db.Base.metadata.create_all(self.engine)
