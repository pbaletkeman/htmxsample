from __future__ import annotations

from typing import Optional

from litestar import Litestar, get
from litestar.config.compression import CompressionConfig
from litestar.contrib.htmx.request import HTMXRequest
from litestar.contrib.mako import MakoTemplateEngine
from litestar.contrib.sqlalchemy.base import UUIDBase
from litestar.contrib.sqlalchemy.plugins import AsyncSessionConfig, SQLAlchemyAsyncConfig, SQLAlchemyInitPlugin
from litestar.di import Provide
from litestar.openapi import OpenAPIController, OpenAPIConfig
from litestar.params import Parameter
from litestar.repository.filters import LimitOffset
from litestar.response import Template
from litestar.static_files import StaticFilesConfig
from litestar.template.config import TemplateConfig
from dataclasses import dataclass

from step6.controller.author import AuthorController, AuthorUIController
from step6.controller.book import BookController, BookUIController
import logging

logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


def provide_limit_offset_pagination(
        current_page: int = Parameter(ge=1, query="currentPage", default=1, required=False),
        page_size: int = Parameter(
            query="pageSize",
            ge=1,
            default=30,
            required=False,
        ),
) -> LimitOffset:
    """Add offset/limit pagination.

    Return type consumed by `Repository.apply_limit_offset_pagination()`.

    Parameters
    ----------
    current_page : int
        LIMIT to apply to select.
    page_size : int
        OFFSET to apply to select.
    """
    return LimitOffset(page_size, page_size * (current_page - 1))


session_config = AsyncSessionConfig(expire_on_commit=False)
sqlalchemy_config = SQLAlchemyAsyncConfig(
    connection_string="sqlite+aiosqlite:///test.sqlite", session_config=session_config
)  # Create 'db_session' dependency.
sqlalchemy_plugin = SQLAlchemyInitPlugin(config=sqlalchemy_config)


async def on_startup() -> None:
    """Initializes the database."""
    async with sqlalchemy_config.get_engine().begin() as conn:
        await conn.run_sync(UUIDBase.metadata.create_all)


@get(path='/', sync_to_thread=False)
def index(name: Optional[str]) -> Template:
    return Template(template_name='index.mako.html', context={"name": name})


class OpenAPIControllerExtra(OpenAPIController):
    favicon_url = '/static-files/favicon.ico'


app = Litestar(
    route_handlers=[AuthorUIController, AuthorController, BookController, BookUIController, index],
    on_startup=[on_startup],
    openapi_config=OpenAPIConfig(
        title='My API', version='1.0.0',
        root_schema_site='elements',  # swagger, elements, redoc, rapidoc
        path='/docs',
        create_examples=False,
        openapi_controller=OpenAPIControllerExtra,
        use_handler_docstrings=True,
    ),
    static_files_config=[StaticFilesConfig(
        path='static-files',  # path used in links
        directories=['step6/static-files']  # path on the server
    )],
    request_class=HTMXRequest,
    template_config=TemplateConfig(engine=MakoTemplateEngine, directory="step6/templates"),
    plugins=[SQLAlchemyInitPlugin(config=sqlalchemy_config)],
    dependencies={"limit_offset": Provide(provide_limit_offset_pagination, sync_to_thread=False)},
    compression_config=CompressionConfig(backend="brotli", brotli_gzip_fallback=True, brotli_quality=5),
)
