from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from advanced_alchemy.base import UUIDBase
from sqlalchemy.orm import Mapped, relationship

from step6.common import BaseModel
from step6.model.book import BookModel, BookWithOutAuthor


class AuthorModel(UUIDBase):
    # we can optionally provide the table name instead of auto-generating it
    __tablename__ = "author"
    name: Mapped[str]
    dob: Mapped[date | None]

    books: Mapped[list[BookModel]] = relationship(back_populates="author", lazy="selectin")

    def __str__(self):
        return str({'name': self.name, 'dob': self.dob, 'id': self.id})


class Author(BaseModel):
    id: UUID | None
    name: str
    dob: date | None = None


class AuthorCreate(BaseModel):
    name: str
    dob: date | str | None = None


class AuthorUpdate(BaseModel):
    name: str | None = None
    dob: date | str | None = None


class AuthorAndBooks(BaseModel):
    id: UUID | None
    name: str
    dob: date | None = None
    books: list[BookWithOutAuthor] | None = None

# select * from book where lower(hex(author_id)) = "7beb930003c64466a7c07fd598806539"

