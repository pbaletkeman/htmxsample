from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

import litestar
from advanced_alchemy import SQLAlchemyAsyncRepository
from litestar.response import Template
from pydantic import TypeAdapter

from litestar import get
from litestar.controller import Controller
from litestar.di import Provide
from litestar.handlers.http_handlers.decorators import delete, patch, post, put
from litestar.pagination import OffsetPagination
from litestar.params import Parameter
from litestar.repository.filters import LimitOffset
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from step6.model.author import AuthorModel, Author, AuthorCreate, AuthorUpdate, AuthorAndBooks
from datetime import datetime

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class AuthorRepository(SQLAlchemyAsyncRepository[AuthorModel]):
    """Author repository."""

    model_type = AuthorModel


async def provide_authors_repo(db_session: AsyncSession) -> AuthorRepository:
    """This provides the default Authors repository."""
    return AuthorRepository(session=db_session)


async def provide_author_details_repo(db_session: AsyncSession) -> AuthorRepository:
    """This provides a simple example demonstrating how to override the join options for the repository."""
    return AuthorRepository(
        statement=select(AuthorModel).options(selectinload(AuthorModel.books)),
        session=db_session,
    )


class AuthorUIController(Controller):
    dependencies = {"authors_repo": Provide(provide_authors_repo)}
    path = "/authors"
    tags = ["Author UI"]

    @get(path="/delete/{author_id:uuid}")
    async def delete_author(
            self,
            authors_repo: AuthorRepository,
            author_id: UUID = Parameter(
                title="Author ID",
                description="The author to retrieve.",
            ),
    ) -> Template:
        """
        """
        obj = await authors_repo.get(author_id)
        return Template(template_name='author.delete.mako.html', context={'author': obj})

    @post('/new')
    async def create_author(
            self,
            authors_repo: AuthorRepository,
            data: AuthorCreate,
    ) -> Template:
        """
        ### Create Author ###
        Create a new **author**.
        ```Example Data:
        {
          "name": "John Q Public",
          "dob": "2020-01-04"
        }
        ===================
        {
          "name": "Joe Doe"
        }
        ```
        """
        # handle empty date values
        if data.dob:
            if 'mm' in data.dob or 'dd' in data.dob or 'yy' in data.dob or data.dob == '':
                data.dob = None
            else:
                data.dob = datetime.strptime(data.dob, '%Y-%m-%d')

        obj = await authors_repo.add(
            AuthorModel(**data.model_dump(exclude_unset=True, exclude_none=True)),
        )
        await authors_repo.session.commit()
        return Template(template_name='author.edit-row.mako.html', context={'author': Author.model_validate(obj)})

    @put(
        path="/update/{author_id:uuid}",
    )
    async def put_author(
            self,
            authors_repo: AuthorRepository,
            data: AuthorUpdate,
            author_id: UUID = Parameter(
                title="Author ID",
                description="The author to update.",
            ),
    ) -> Template:
        """
        ### Put Author
        Update an **author**, including empty values.
        ```Example Data:
        {
          "name": "John Q Public",
          "dob": "2020-01-04"
        }
        ===================
        {
          "name": "Joe Doe"
        }
        ```
        """
        obj = await author_put_helper(author_id, authors_repo, data)

        return Template(template_name='author.edit-row.mako.html', context={'author': obj})

    @get(path="/edit/{author_id:uuid}")
    async def edit_author(
            self,
            authors_repo: AuthorRepository,
            author_id: UUID = Parameter(
                title="Author ID",
                description="The author to retrieve.",
            ),
    ) -> Template:
        """
        """
        obj = await authors_repo.get(author_id)
        return Template(template_name='author.edit.mako.html', context={'author': obj})

    @get('/listing')
    async def index(self, authors_repo: AuthorRepository,
                    limit_offset: LimitOffset, ) -> Template:
        results, total = await authors_repo.list_and_count(limit_offset)
        type_adapter = TypeAdapter(list[Author])
        site_data = OffsetPagination[Author](
            items=type_adapter.validate_python(results),
            total=total,
            limit=limit_offset.limit,
            offset=limit_offset.offset,
        )
        return Template(template_name='author.index.mako.html', context={'site_data': site_data})


async def author_put_helper(author_id: UUID, authors_repo: AuthorRepository, data: AuthorUpdate):
    # handle empty date values
    if data.dob:
        if 'mm' in data.dob or 'dd' in data.dob or 'yy' in data.dob or data.dob == '':
            data.dob = None
        else:
            data.dob = datetime.strptime(data.dob, '%Y-%m-%d')
    raw_obj = data.model_dump(exclude_unset=False, exclude_none=False)
    raw_obj.update({"id": author_id})
    obj = await authors_repo.update(AuthorModel(**raw_obj))
    await authors_repo.session.commit()
    return Author.model_validate(obj)


class AuthorController(Controller):
    """Author CRUD"""

    dependencies = {"authors_repo": Provide(provide_authors_repo)}
    path = "/authors"
    tags = ["Author CRUD"]

    @get()
    async def list_authors(
            self,
            authors_repo: AuthorRepository,
            limit_offset: LimitOffset,
    ) -> OffsetPagination[Author]:
        """
        ### List authors ###
        List all the **author** records in paginated form with the *total* record count.
        """
        results, total = await authors_repo.list_and_count(limit_offset)
        type_adapter = TypeAdapter(list[Author])
        return OffsetPagination[Author](
            items=type_adapter.validate_python(results),
            total=total,
            limit=limit_offset.limit,
            offset=limit_offset.offset,
        )

    @post()
    async def create_author(
            self,
            authors_repo: AuthorRepository,
            data: AuthorCreate,
    ) -> Author:
        """
        ### Create Author ###
        Create a new **author**.
        ```Example Data:
        {
          "name": "John Q Public",
          "dob": "2020-01-04"
        }
        ===================
        {
          "name": "Joe Doe"
        }
        ```
        """
        obj = await authors_repo.add(
            AuthorModel(**data.model_dump(exclude_unset=True, exclude_none=True)),
        )
        await authors_repo.session.commit()
        return Author.model_validate(obj)

    @get(path="with-books/{author_id:uuid}")
    async def get_author_and_books(
            self,
            authors_repo: AuthorRepository,
            author_id: UUID = Parameter(
                title="Author ID",
                description="The author to retrieve.",
            ),
    ) -> AuthorAndBooks:
        """
        ### Get Author And Their Books
        Get an existing **author** with all of their **books**.
        """
        obj = await authors_repo.get(author_id)
        return AuthorAndBooks.model_validate(obj)

    @get(path="/{author_id:uuid}")
    async def get_author(
            self,
            authors_repo: AuthorRepository,
            author_id: UUID = Parameter(
                title="Author ID",
                description="The author to retrieve.",
            ),
    ) -> Author:
        """
        ### Get Author ###
        Get an existing **author**.
        """
        obj = await authors_repo.get(author_id)
        return Author.model_validate(obj)

    @put(
        path="/{author_id:uuid}"
    )
    async def put_author(
            self,
            authors_repo: AuthorRepository,
            data: AuthorUpdate,
            author_id: UUID = Parameter(
                title="Author ID",
                description="The author to update.",
            ),
    ) -> Author:
        """
        ### Put Author
        Update an **author**, including empty values.
        ```Example Data:
        {
          "name": "John Q Public",
          "dob": "2020-01-04"
        }
        ===================
        {
          "name": "Joe Doe"
        }
        ```
        """
        return await author_put_helper(author_id, authors_repo, data)

    @patch(
        path="/{author_id:uuid}"

    )
    async def patch_author(
            self,
            authors_repo: AuthorRepository,
            data: AuthorUpdate,
            author_id: UUID = Parameter(
                title="Author ID",
                description="The author to update.",
            ),
    ) -> Author:
        """
        ### Patch Author ###
        Update an **author**, ignoring empty values.
        ```Example Data:
        {
          "name": "John Q Public",
          "dob": "2020-01-04"
        }
        ===================
        {
          "name": "Joe Doe"
        }
        ```
        """
        raw_obj = data.model_dump(exclude_unset=True, exclude_none=True)
        raw_obj.update({"id": author_id})
        obj = await authors_repo.update(AuthorModel(**raw_obj))
        await authors_repo.session.commit()
        return Author.model_validate(obj)

    @delete(path="/{author_id:uuid}")
    async def delete_author(
            self,
            authors_repo: AuthorRepository,
            author_id: UUID = Parameter(
                title="Author ID",
                description="The author to delete.",
            ),
    ) -> None:
        """
        ### Delete Author ###
        Delete an **author** from the system.
        """
        _ = await authors_repo.delete(author_id)
        await authors_repo.session.commit()
