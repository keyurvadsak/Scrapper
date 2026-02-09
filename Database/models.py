from Database.db import Base
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

class Website(Base):
    __tablename__ = "websites"

    id = Column(Integer, primary_key=True)
    base_url = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    links = relationship("Links", back_populates="website", cascade="all, delete-orphan")
    pages = relationship("Page", back_populates="website", cascade="all, delete-orphan")


class Links(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    website_id = Column(Integer, ForeignKey("websites.id", ondelete="CASCADE"), nullable=False)

    website = relationship("Website", back_populates="links")

class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False)
    title = Column(String)
    website_id = Column(Integer, ForeignKey("websites.id", ondelete="CASCADE"), nullable=False)

    website = relationship("Website", back_populates="pages")
    tags = relationship(
        "Tag",
        back_populates="page",
        cascade="all, delete-orphan"
    )


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)

    page_id = Column(
        Integer,
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    h1 = Column(JSONB, nullable=True)
    h2 = Column(JSONB, nullable=True)
    h3 = Column(JSONB, nullable=True)
    h4 = Column(JSONB, nullable=True)
    h5 = Column(JSONB, nullable=True)
    h6 = Column(JSONB, nullable=True)
    p = Column(JSONB, nullable=True)
    th = Column(JSONB, nullable=True)
    td = Column(JSONB, nullable=True)
    li = Column(JSONB, nullable=True)
    a = Column(JSONB, nullable=True)
    img = Column(JSONB, nullable=True)
    audio = Column(JSONB, nullable=True)
    video = Column(JSONB, nullable=True)
    
    page = relationship("Page", back_populates="tags")
