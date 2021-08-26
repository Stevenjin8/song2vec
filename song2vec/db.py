"""Object realtional mappings."""

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# Intermediate table for many-to-many relationships between tracks and playlists.
class Association(Base):
    __tablename__ = "association"
    id = Column(Integer, primary_key=True)
    track_uri = Column(
        String,
        ForeignKey("track.uri", ondelete="CASCADE"),
        nullable=False,
    )
    playlist_id = Column(
        String,
        ForeignKey("playlist.pid", ondelete="CASCADE"),
        nullable=False,
    )

    track = relationship("Track", back_populates="playlist_associations")
    playlist = relationship("Playlist", back_populates="track_associations")


class Artist(Base):
    """Artists are users that create tracks.

    Fields:
        uri (String): unique identifier.
        name (String): name of the artist.
        tracks (Relationship): the tracks of this artist.
    """

    __tablename__ = "artist"

    uri = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    tracks = relationship(
        "Track",
        back_populates="artist",
        cascade="all, delete",
    )

    def __repr__(self):
        return f"<{self.__class__.__name__} ID: {self.uri}, NAME: {self.name}>"


class Track(Base):
    """Aka a song.

    Fields:
        uri (String): unique identifier.
        name (String): name of this track.
        artist (Relationship): foreign key to the artist of this track. Curiously, each
            track only has one artist.
        album (Relationship): foreign key to the album this track belongs to.
        playlists (Relationship): many to many with the playlists this track is in.
    """

    __tablename__ = "track"

    uri = Column(String, primary_key=True)
    name = Column(String)
    duration = Column(Integer)
    artist_uri = Column(
        String, ForeignKey("artist.uri", ondelete="CASCADE"), nullable=False
    )
    artist = relationship("Artist", back_populates="tracks")
    album_uri = Column(
        String, ForeignKey("album.uri", ondelete="CASCADE"), nullable=False
    )
    album = relationship("Album", back_populates="tracks")

    playlist_associations = relationship(
        "Association", back_populates="track", cascade="all, delete"
    )

    def __repr__(self):
        return f"<{self.__class__.__name__} URI: {self.uri}, NAME: {self.name}>"


class Playlist(Base):
    """A __unordered__ set of tracks.

    Fields:
        pid (Integer): unique identifier.
        name (String): name of this playlist.
        tracks (Relationship): many to many relationships with the tracks in this playlist.
    """

    __tablename__ = "playlist"

    pid = Column(Integer, primary_key=True)
    name = Column(String)
    track_associations = relationship(
        "Association", back_populates="playlist", cascade="all, delete"
    )

    def __repr__(self):
        return f"<{self.__class__.__name__} ID: {self.pid}, NAME: {self.name}>"


class Album(Base):
    """Just what it sounds like.
    No `Artist` field because not sure if all albums have a single artist.

    Fields:
        uri (String): unique identifier.
        name (String): name of this album.
        tracks (Relationship): one to many with the tracks in this album.
    """

    __tablename__ = "album"

    uri = Column(String, primary_key=True)
    name = Column(String)
    tracks = relationship("Track", back_populates="album", cascade="all, delete")
