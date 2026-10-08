"""Site pages. Importing this module registers the routes with NiceGUI."""

from fastapi import Request
from nicegui import ui

from insightshub import auth
from insightshub.config import settings
from insightshub.layout import standard_page


@ui.page("/")
async def home(request: Request) -> None:

    async with standard_page(title="Apps", request=request) as user:

        ui.label(f'Welcome: {user.display_name}')
        ui.label(f'Is Authenticated: {user.is_authenticated}')

@ui.page("/settings")
async def settings(request: Request) -> None:

    async with standard_page(title="Settings", request=request) as user:
        ui.label('Settings')