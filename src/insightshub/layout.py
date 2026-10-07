
from nicegui import ui
from pathlib import Path
from fastapi import Request
from insightshub.auth import User, sign_in_url, sign_out_url, authenticate, page_url
from insightshub.config import settings
from contextlib import asynccontextmanager
import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)

UNDP_BLUE = "#006eb5"
UNDP_RED = "#d12800"
STATIC_DIR = Path(__file__).parent / "static"
ASSETS = "/static/undp"
REPO_URL = "https://github.com/UNDP-Data/geo-careatlas"

NAV_ITEMS = [
    ("Apps", "/"),
    ("Gender Equality", "https://www.undp.org/gender-equality"),

]

FOOTER_LINKS = [
    ("About UNDP", "https://www.undp.org/about-us"),
    ("Terms of use", "https://www.undp.org/copyright-terms-use"),
    ("Source code", REPO_URL),
]

def _is_external(url: str) -> bool:
    return url.startswith("http")


def _is_active(path: str, current: str) -> bool:
    if _is_external(path):
        return False
    return current == path if path == "/" else current.startswith(path)


def _link(label: str, url: str) -> ui.link:
    return ui.link(label, url, new_tab=_is_external(url))

def _img(src: str, alt: str) -> ui.element:
    return ui.element("img").props(f'src="{src}" alt="{alt}"')


def _asset_url(name: str) -> str:
    """URL of a static file, versioned by its modification time.

    Checked on every render so an edited file gets a new URL even when the
    server has not restarted, and browsers never serve a stale cached copy.
    """
    version = int((STATIC_DIR / name).stat().st_mtime)
    return f"/static/{name}?v={version}"


def _account_old(request: Request, user: User | None) -> None:
    if not user.is_authenticated:
        url = sign_in_url(request)
        #ui.label(url)
        ui.button(f"Sign in", ) \
            .props(f'href="{url}" unelevated no-wrap color=secondary').classes("undp-btn undp-btn--small")

        return

    url = sign_out_url(request)
    with ui.button(icon="account_circle").props("flat round"):
        with ui.menu().props('anchor="bottom right" self="top right"'):
            with ui.column().classes("px-4 py-3 gap-0"):
                ui.label(user.display_name).classes("font-semibold")
                ui.label(user.email).classes("text-xs text-grey-7")
            ui.separator()
            ui.menu_item("Sign out", on_click=lambda: ui.navigate.to(url)).classes("bg-secondary text-white font-bold uppercase text-center ")





def _account(request: Request, user: User | None) -> None:
    is_authenticated = user.is_authenticated
    target_host = settings.public_auth_url
    rd = page_url(request)

    # Dynamically determine the action based on auth status
    action = "sign_out" if is_authenticated else "start"
    final_url = f"{target_host}/{action}?rd={quote(rd, safe=':/%?=&')}"

    with ui.row().classes("items-center gap-1"):
        # --- BUTTON 1: THE IDENTITY BUTTON ---
        with ui.element('div'):
            identity_btn = ui.button(icon='account_circle') \
                .props(f'flat round dense color="{"secondary" if is_authenticated else "grey"}"') \
                .classes('w-9 h-9 hover:scale-110 transition') \
                .tooltip(f'Connected as {user.email}' if is_authenticated else 'Sign In')

            async def go_auth():
                identity_btn.props('loading icon=sync')
                identity_btn.classes(add='animate-spin')
                await ui.run_javascript('await new Promise(r => requestAnimationFrame(r))')
                ui.navigate.to(final_url)

            identity_btn.on('click', go_auth)

        # --- BUTTON 2: MANAGEMENT ICONS (Only visible when authenticated) ---
        if is_authenticated:
            # Subtle vertical divider
            ui.element('div').classes('w-[1px] h-6 bg-gray-300 mx-1')

            # Session Manager Icon
            ui.button(icon='dns').props('color="secondary"') \
                .props('flat round dense') \
                .classes('w-9 h-9 hover:scale-110 transition') \
                .tooltip('Session Manager') \
                .on('click', lambda: ui.navigate.to('/sessions'))

            # System Settings Icon
            ui.button(icon='tune').props('color="secondary"') \
                .props('flat round dense') \
                .classes('w-9 h-9 hover:scale-110 transition') \
                .tooltip('System Settings') \
                .on('click', lambda: ui.navigate.to('/settings'))
def _account_mixed(request: Request, user: User | None) -> None:
    is_auth = user.is_authenticated

    # Use your theme's secondary color (UNDP_RED) if authenticated, else grey
    btn_color = "secondary" if is_auth else "grey"
    tooltip_text = f'Connected as {user.email}' if is_auth else 'Sign In'

    with ui.element('div'):
        # The Fancy Identity Button
        identity_btn = ui.button(icon='account_circle') \
            .props(f'flat round dense color="{btn_color}"') \
            .classes('w-9 h-9 hover:scale-110 transition') \
            .tooltip(tooltip_text)

        if not is_auth:
            # UNAUTHENTICATED: Play the spin animation and navigate to sign in
            sign_in = sign_in_url(request)

            async def go_auth():
                identity_btn.props('loading icon=sync')
                identity_btn.classes(add='animate-spin')
                await ui.run_javascript('await new Promise(r => requestAnimationFrame(r))')
                ui.navigate.to(sign_in)

            identity_btn.on('click', go_auth)

        else:
            # AUTHENTICATED: Open the user profile dropdown menu
            sign_out = sign_out_url(request)

            with identity_btn:
                with ui.menu().props('anchor="bottom right" self="top right"'):
                    with ui.column().classes("px-4 py-3 gap-0"):
                        ui.label(user.display_name).classes("font-semibold")
                        ui.label(user.email).classes("text-xs text-grey-7")
                    ui.separator()

                    # Your customized red, bold, centered Sign Out item
                    ui.menu_item("Sign out", on_click=lambda: ui.navigate.to(sign_out)) \
                        .classes("bg-secondary text-white font-bold uppercase text-center")

def _hamburger() -> None:
    with ui.element("button").classes("undp-hamburger") \
            .props('type="button" aria-label="Open menu" aria-expanded="false" aria-controls="undp-mobile-nav"') \
            .on("click", js_handler="() => undpToggleNav()"):
        for position in ("top", "middle", "bottom"):
            ui.element("span").classes(f"undp-hamburger__line undp-hamburger__line--{position}")


def load_theme() -> None:
    ui.colors(primary=UNDP_BLUE, secondary=UNDP_RED)
    ui.add_head_html(
        f'<link rel="stylesheet" href="{_asset_url("theme.css")}">'
        f'<script src="{_asset_url("nav.js")}"></script>'
    )

def _header(request: Request, user: User | None ) -> None:
    current = request.url.path

    with ui.header().classes("undp-header"):
        with ui.element("div").classes("undp-header__inner"):
            with ui.link(target="/").classes("undp-header__logo"):
                _img(f"{ASSETS}/undp-logo-blue.svg", "UNDP logo")
            with ui.link(target="/").classes("undp-site-title"):
                ui.label(settings.header_label).classes("undp-site-title__region")
                ui.label(settings.app_name).classes("undp-site-title__name")

            with ui.element("nav").classes("undp-menu gt-sm"):
                for label, url in NAV_ITEMS:
                    link = _link(label, url).classes("undp-menu__link")
                    if _is_active(url, current):
                        link.classes("undp-menu__link--active").props('aria-current="page"')

            with ui.element("div").classes("undp-header__actions"):
                with ui.element("div").classes("gt-sm"):
                    _account(request, user)
                _hamburger()
        #_mobile_nav(request, user, current)

def _footer() -> None:
    with ui.footer(fixed=False).classes("undp-footer"):
        with ui.element("div").classes("undp-footer__inner"):
            with ui.element("div").classes("undp-footer__top"):
                with ui.element("div").classes("undp-footer__brand"):
                    with ui.link(target="https://www.undp.org", new_tab=True).classes("undp-footer__logo"):
                        _img(f"{ASSETS}/undp-logo-white.svg", "UNDP logo")
                    ui.html("United Nations<br>Development Programme").classes("undp-footer__name")
                # with ui.element("div").classes("undp-footer__social"):
                #     for name, url, icon in SOCIAL_LINKS:
                #         with ui.link(target=url, new_tab=True).props(f'aria-label="{name}" title="{name}"'):
                #             _img(f"{ASSETS}/{icon}", name)

            with ui.element("div").classes("undp-footer__bottom"):
                ui.label("© United Nations Development Programme").classes("undp-footer__copyright")
                with ui.element("nav").classes("undp-footer__links"):
                    for label, url in FOOTER_LINKS:
                        _link(label, url).classes("undp-footer__link")


def page_title(title: str) -> None:
    with ui.column().classes("gap-2"):
        ui.element("div").classes("undp-title__bar")
        ui.label(title).classes("undp-title")

@asynccontextmanager
async def standard_page(title: str=None, request:Request = None):
    """A reusable layout with a header, main content area, and footer."""
    # Instantaneously grab the user from the proxy headers
    user = await authenticate(url=settings.private_auth_url,request=request,forward_headers=True)
    logger.info(f'HAHA {user}')
    load_theme()
    _header(request=request, user=user)
    with ui.column().classes("undp-container undp-main"):
        if title:
            page_title(title)
        yield user
    _footer()