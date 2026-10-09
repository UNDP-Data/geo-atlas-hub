"""Site pages. Importing this module registers the routes with NiceGUI."""

from fastapi import Request
from nicegui import ui
import os
import git
from pathlib import Path
from insightshub.config import settings
from insightshub.layout import standard_page, UNDP_RED
from insightshub import marutil as mu

BASE_DIR = Path(__file__).parent.parent.resolve()
NOTEBOOKS_DIR = (BASE_DIR / "notebooks").resolve()
os.environ['NOTEBOOKS_DIR'] = str(NOTEBOOKS_DIR)


@ui.page("/")
@ui.page('/notebooks/{subpath:path}')
async def home(request: Request, subpath: str = "") -> None:

    async with standard_page(title="Apps", request=request) as user:
        repo_url = f'https://oauth2:{settings.github_token}@github.com/UNDP-data/geo-careatlas-notebooks.git'
        # Identify if user has Edit rights (authenticated users)
        can_edit = user.is_authenticated

        # Clone the repository
        if not NOTEBOOKS_DIR.exists():
            repo = git.Repo.clone_from(repo_url, NOTEBOOKS_DIR)
        # 2. Resolve the directory to scan
        current_dir = (NOTEBOOKS_DIR / subpath).resolve()
        # Security: Prevent escaping the root directory
        if not str(current_dir).startswith(str(NOTEBOOKS_DIR)) or not current_dir.exists():
            ui.notify("Directory not found", type='negative')
            return ui.navigate.to('/')

        with ui.column().classes('w-full max-w-7xl mx-auto px-6 lg:px-8'):

            # 3. Breadcrumbs / "Back" Navigation
            if subpath:
                parent_path = Path(subpath).parent
                # Navigate back: if parent is '.', go to root '/'
                back_url = '/' if str(parent_path) == '.' else f'/notebooks/{parent_path}'

                with ui.row().classes('items-center mb-6 cursor-pointer group').on('click',
                                                                                   lambda: ui.navigate.to(back_url)):
                    ui.icon('arrow_back', color='[#006db0]').classes('group-hover:-translate-x-1 transition-transform')
                    ui.label(f"Back to {parent_path if str(parent_path) != '.' else 'Root'}").classes(
                        'text-[#006db0] font-bold text-xs tracking-widest uppercase')
            # 4. The Grid
            with ui.grid(columns='1fr 1fr 1fr').classes('w-full gap-8'):
                # Filter: No hidden files, no __init__.py
                items = [
                    item for item in current_dir.iterdir()
                    if not item.name.startswith('.') and item.name != "__init__.py"
                ]
                # Sort: Folders first, then files
                items.sort(key=lambda x: (not x.is_dir(), x.name))

                for item in items:

                    rel_path = item.relative_to(NOTEBOOKS_DIR)
                    name, _ = os.path.splitext(item.name)
                    item_label = name.replace('_', ' ')

                    if item.is_dir():
                        if '__' in item.name: continue
                        # --- FOLDER CARD ---
                        with ui.card().classes(
                                'undp-card p-0 overflow-hidden bg-white cursor-pointer hover:shadow-lg transition-shadow') \
                                .on('click', lambda p=rel_path: ui.navigate.to(f'/notebooks/{p}')):
                            ui.element('div').classes('w-full h-1 bg-[#006db0]')
                            with ui.column().classes('p-8 w-full'):
                                ui.icon('folder_shared', color='[#006db0]').classes('text-4xl mb-2')
                                ui.label(item_label).classes('text-xl font-bold text-gray-700 capitalize')
                                ui.label('Folder').classes(
                                    'text-gray-400 text-[10px] tracking-widest uppercase font-bold')

                    elif item.suffix == '.py':
                        # --- NOTEBOOK CARD ---
                        with ui.card().classes('undp-card p-0 overflow-hidden bg-white'):
                            # Green accent for notebooks
                            ui.element('div').classes('w-full h-1 bg-green-500')
                            with ui.column().classes('p-8 w-full'):
                                with ui.row().classes('items-center gap-2 mb-2'):
                                    ui.icon('dashboard', color='[#006db0]').classes('text-2xl')
                                    ui.label('Notebook').classes(
                                        'text-[#006db0] text-sm font-bold tracking-widest uppercase')
                                ui.label(item_label).classes('text-xl font-bold text-gray-700 capitalize')

                                # Fetch metadata (description) from the file
                                descr = mu.get_global_metadata(str(item.absolute()))
                                ui.label(descr or "No description available.").classes(
                                    'text-sm mb-6 text-gray-500 line-clamp-2 h-10')
                                # Standard slug: 'folder/name'
                                marimo_slug = str(rel_path).replace('.py', '').replace(os.sep, '/').strip('/')

                                # Calculate relative path jump to root (../../ etc)
                                # This ensures links work regardless of folder depth
                                #depth = str(rel_path).count('/')
                                #r = "../" * (depth + 1)
                                next_uri = f'/apps/{marimo_slug}'
                                with ui.row().classes('w-full justify-center mt-auto'):
                                    # This wrapper defines the “middle” area and width budget for buttons
                                    with ui.row().classes('w-full max-w-[360px] gap-2 flex-nowrap'):
                                        if can_edit:
                                            # 2 buttons, equal widths
                                            ui.button(
                                                'Launch',
                                                on_click=lambda s=marimo_slug, : ui.navigate.to(next_uri)
                                            ).classes('undp-btn primary text-white flex-1 w-1/2 capitalize') \
                                                .tooltip(f'View as interactive app at {next_uri}')

                                            ui.button(
                                                'Edit',
                                                on_click=lambda s=marimo_slug,: ui.navigate.to(f'/edit/open/{s}')
                                            ).props(f'color="{UNDP_RED}"') \
                                                .classes('undp-btn text-white flex-1 w-1/2 capitalize') \
                                                .tooltip(
                                                f'Open in Editor mode (Spawns kernel) to /edit/open/{marimo_slug}')

                                        else:

                                            # 1 button, centered in the same max width wrapper
                                            ui.button(
                                                'Launch',
                                                on_click=lambda: ui.navigate.to(next_uri)
                                            ).classes('undp-btn primary text-white justify w-[180px] capitalize') \
                                                .tooltip(f'View as interactive app at {next_uri}')


@ui.page("/settings")
async def app_settings(request: Request) -> None:

    async with standard_page(title="Settings", request=request) as user:
        ui.label('Settings')