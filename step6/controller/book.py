from __future__ import annotations

import random
from typing import TYPE_CHECKING
from uuid import UUID

from advanced_alchemy import SQLAlchemyAsyncRepository
from faker import Faker
from pydantic import TypeAdapter

from litestar import get
from litestar.controller import Controller
from litestar.di import Provide
from litestar.handlers.http_handlers.decorators import delete, patch, post, put
from litestar.pagination import OffsetPagination
from litestar.params import Parameter
from litestar.repository.filters import LimitOffset

from step6.model.book import BookModel, Book, BookCreate, BookUpdate, BulkBookCreate

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class BookRepository(SQLAlchemyAsyncRepository[BookModel]):
    """Author repository."""

    model_type = BookModel


async def provide_book_repo(db_session: AsyncSession) -> BookRepository:
    """This provides the default Authors repository."""
    return BookRepository(session=db_session)


class BookController(Controller):
    """Book CRUD"""

    dependencies = {"book_repo": Provide(provide_book_repo)}
    path = "/book"
    tags = ["Book CRUD"]

    class Helper:
        @staticmethod
        def convert_books(data: BulkBookCreate) -> list[dict[str, UUID]]:
            # transform the list of strings to a list of BookCreate objects
            # because this is a simple model we can use this one line
            # this is instead of `data.model_dump`
            return [{"title": title, "author_id": data.author_id} for title in data.title]

    @get()
    async def list_books(
            self,
            book_repo: BookRepository,
            limit_offset: LimitOffset,
    ) -> OffsetPagination[Book]:
        """
        ### List All ###
        List, **book** records, paginated
        """
        results, total = await book_repo.list_and_count(limit_offset)
        type_adapter = TypeAdapter(list[Book])
        return OffsetPagination[Book](
            items=type_adapter.validate_python(results),
            total=total,
            limit=limit_offset.limit,
            offset=limit_offset.offset,
        )

    @post()
    async def create_book(
            self,
            book_repo: BookRepository,
            data: BookCreate,
    ) -> Book:
        """
        ### Create Book ###
        Create a new **book**.
        ```Example Data:
        {
          "title": "Book Title",
          "author_id": "78424c75-5c41-4b25-9735-3c9f7d05c59e"
        }
        ```
        """
        obj = await book_repo.add(
            BookModel(**data.model_dump(exclude_unset=True, exclude_none=True)),
        )
        await book_repo.session.commit()
        return Book.model_validate(obj)

    @post("/bulk")
    async def bulk_create_book(
            self,
            book_repo: BookRepository,
            data: BulkBookCreate,
    ) -> list[Book]:
        """
        ### Bulk Create New Book ###
        Create many new **book** records.
        ```Example Data:
        {
          "title": [
            "Book Title 1", "Book Title 2", "Book Title 3"
          ],
          "author_id": "78424c75-5c41-4b25-9735-3c9f7d05c59e"
        }
        ```
        """
        new_data = self.Helper.convert_books(data)
        obj = await book_repo.add_many(
            [BookModel(**d) for d in new_data]
        )
        await book_repo.session.commit()
        return [Book.model_validate(o) for o in obj]

    @get(path="/{book_id:uuid}")
    async def get_book(
            self,
            book_repo: BookRepository,
            book_id: UUID = Parameter(
                title="Book ID",
                description="The book to retrieve.",
            ),
    ) -> Book:
        """
        ### Get Book ###
        Get an existing **book**.
        """
        obj = await book_repo.get(book_id)
        return Book.model_validate(obj)

    @put(path="/{book_id:uuid}", )
    async def put_book(
            self,
            book_repo: BookRepository,
            data: BookUpdate,
            book_id: UUID = Parameter(
                title="Book ID",
                description="The book to update.",
            ),
    ) -> Book:
        """
        ### Put Book ###
        Update a **book**, including empty values.
        ```Example Data:
        {
          "title": "new book title",
          "author_id": "78424c75-5c41-4b25-9735-3c9f7d05c59e"
        }
        ```
        """
        raw_obj = data.model_dump(exclude_unset=False, exclude_none=False)
        raw_obj.update({"id": book_id})
        obj = await book_repo.update(BookModel(**raw_obj))
        await book_repo.session.commit()
        return Book.model_validate(obj)

    @patch(path="/{book_id:uuid}", )
    async def patch_book(
            self,
            book_repo: BookRepository,
            data: BookUpdate,
            book_id: UUID = Parameter(
                title="Book ID",
                description="The book to update.",
            ),
    ) -> Book:
        """
        ### Patch Book ###
        Update a **book**, ignoring empty values.
        ```Example Data:
        {
          "title": "new book title",
          "author_id": "78424c75-5c41-4b25-9735-3c9f7d05c59e"
        }
        ```
        """
        raw_obj = data.model_dump(exclude_unset=True, exclude_none=True)
        raw_obj.update({"id": book_id})
        obj = await book_repo.update(BookModel(**raw_obj))
        await book_repo.session.commit()
        return Book.model_validate(obj)

    @delete(path="/{book_id:uuid}")
    async def delete_book(
            self,
            book_repo: BookRepository,
            book_id: UUID = Parameter(
                title="Book ID",
                description="The book to delete.",
            ),
    ) -> None:
        """
        ### Delete Book ###
        Delete a **book** from the system.
        """
        _ = await book_repo.delete(book_id)
        await book_repo.session.commit()

    @post(path='/faker/{author_ids:str}')
    async def create_fake_books_per_author(
            self,
            book_repo: BookRepository,
            author_ids: str = Parameter(
                title='Author Ids',
                description='List Of Author Ids'
            ),
    ) -> list[Book]:
        book_authors: list[str] = []
        if len(author_ids) > 30:
            book_authors = author_ids.split(',')
        else:
            book_authors = [author_ids]
        fake = Faker()
        returned_list: list[Book] = []
        for author in book_authors:
            title: list[str] = []
            for x in range(random.randint(1, 7)):
                title.append(str(fake.sentence(nb_words=4)).title()[:-1])
            data: BulkBookCreate = BulkBookCreate(title=title, author_id=author)
            books = await self.bulk_book_add_helper(book_repo, data)
            returned_list.extend(books)

        return returned_list
