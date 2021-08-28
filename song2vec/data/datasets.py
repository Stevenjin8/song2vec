from typing import Dict, List, Tuple

import sqlalchemy
from sqlalchemy import func
from torch import Tensor
from torch.utils.data import Dataset

from song2vec import db
from song2vec.utils import MultiHotEncoder


class MillionPlaylistDataset(Dataset):
    """Dataset to load the million playlist dataset from the database."""

    multi_hot_encoder: MultiHotEncoder
    db_url: str
    engine: sqlalchemy.engine.Engine
    Session: sqlalchemy.orm.Session

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.engine = sqlalchemy.create_engine(db_url)
        self.Session = sqlalchemy.orm.sessionmaker(bind=self.engine)
        session = self.Session()
        self.multi_hot_encoder = MultiHotEncoder(
            x for x, in session.query(db.Track.uri).all()
        )

    def query_db(self, index: List[str]) -> List[List[str]]:
        session = self.Session()
        res = dict(
            session.query(
                db.Association.playlist_id, func.group_concat(db.Association.track_uri)
            )
            .group_by(db.Association.playlist_id)
            .having(db.Association.playlist_id.in_(index))
            .all()
        )
        session.close()
        return [res[key].split(",") for key in index if key in res]

    @property
    def keys(self):
        session = self.Session()
        return [x for x, in session.query(db.Playlist.pid).all()]

    def __getitem__(self, index) -> Tensor:
        """Index should be a string or a list of strings."""
        single = isinstance(index, str)
        if single:
            index = [index]
        ret = self.multi_hot_encoder.encode(token_lists=self.query_db(index))
        if single:
            return ret[0].coalesce()
        return ret.coalesce()

    def __len__(self) -> int:
        """Number of playlists in the db."""
        session = self.Session()
        (length,) = session.query(func.count(db.Playlist.pid)).one()
        return length

    def __iter__(self):
        for key in self.keys:
            yield self[key]
