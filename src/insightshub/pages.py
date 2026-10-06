"""Site pages. Importing this module registers the routes with NiceGUI."""

from fastapi import Request
from nicegui import ui

#from insightshub.auth import sign_in_url
from insightshub.config import settings
#from insightshub.layout import frame, page_title

# Dictionary to hold our simple authentication state
user_state = {'logged_in': False}

@ui.refreshable
def auth_ui():
    """This component re-renders whenever auth_ui.refresh() is called."""
    if user_state['logged_in']:
        ui.label('Welcome back, admin!').classes('text-xl font-bold')
        # Show a red 'Log Out' button
        ui.button('Log Out', on_click=logout, color='negative').classes('mt-4 px-6')
    else:
        ui.label('Please log in to access the cluster.').classes('text-xl')
        # Show a blue 'Log In' button
        ui.button('Log In', on_click=login, color='primary').classes('mt-4 px-6')

def login():
    user_state['logged_in'] = True
    ui.notify('Logged in successfully!', type='positive')
    auth_ui.refresh()  # Trigger the UI update

def logout():
    user_state['logged_in'] = False
    ui.notify('Logged out successfully.', type='info')
    auth_ui.refresh()  # Trigger the UI update

@ui.page("/")
async def home(request: Request) -> None:
    ui.label(settings.server_name)
    with ui.card().classes('absolute-center items-center p-8 shadow-lg'):
        auth_ui()
    # async with frame(request) as user:
    #     with ui.column().classes("undp-hero"):
    #         ui.label("CareAtlas").classes("undp-hero__title")
    #         ui.label(
    #             "Interactive notebooks and maps on care, gender and development, "
    #             "published by the UNDP Gender Team."
    #         ).classes("undp-hero__lead")
    #         if user:
    #             ui.label(f"Signed in as {user.display_name}").classes("undp-hero__meta")
    #         elif settings.auth_enabled:
    #             url = sign_in_url(request)
    #             ui.button("Sign in with GitHub", on_click=lambda: ui.navigate.to(url)) \
    #                 .props("unelevated no-wrap color=secondary").classes("undp-btn")
    #
    #     page_title("Apps")
    #     with ui.card().classes("undp-card w-full"):
    #         ui.label("No apps published yet.").classes("text-grey-7")