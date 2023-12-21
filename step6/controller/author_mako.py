from typing import Optional

from litestar import Controller, get
from litestar.response import Template


class AuthorMakoController(Controller):

    @get(path='/', sync_to_thread=False)
    def index(self, name: Optional[str]) -> Template:
        return Template(template_name='hello.mako.html', context={"name": name})
