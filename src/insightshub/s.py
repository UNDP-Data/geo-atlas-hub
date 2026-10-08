import httpx
import logging
from nicegui import ui, app
from fastapi import Request

logger = logging.getLogger(__name__)


# --- Your Auth Helper Functions ---

def is_authenticated(identity: dict):
    return identity.get("email") and identity["email"] != "Guest User"


def get_user_identity(request: Request):
    h = request.headers
    email = h.get("x-auth-request-email") or h.get("x-forwarded-email")
    user = h.get("x-auth-request-user") or h.get("x-forwarded-user")
    groups_raw = h.get("x-auth-request-groups") or h.get("x-forwarded-groups") or ""
    groups = [g.strip() for g in groups_raw.split(",") if g.strip()]

    return {
        "email": email or "Guest User",
        "user": user or "Guest",
        "groups": groups
    }


def check_auth(url: str, request: Request, forward_headers=False):
    with httpx.Client(timeout=3.0) as client:
        try:
            headers = {
                "X-Forwarded-Proto": request.headers.get("x-forwarded-proto", request.url.scheme),
                "X-Forwarded-Host": request.headers.get("x-forwarded-host", request.headers.get("host", "")),
                "X-Forwarded-Uri": request.url.path + (("?" + request.url.query) if request.url.query else ""),
            }
            ua = request.headers.get("user-agent")
            if ua:
                headers["User-Agent"] = ua

            # Ask the proxy to validate the browser's cookies
            response = client.get(url, cookies=request.cookies, headers=headers)

            if response.status_code in (200, 202):
                email = response.headers.get("x-auth-request-email", "Guest")
                groups_raw = response.headers.get("x-auth-request-groups", "")
                groups = [g.strip() for g in groups_raw.split(",")] if groups_raw else []
                username = response.headers.get("x-auth-request-user", "")

                if forward_headers:
                    auth_headers = {
                        "x-auth-request-email": response.headers.get("x-auth-request-email", "Guest"),
                        "x-auth-request-user": response.headers.get("x-auth-request-user", ""),
                        "x-auth-request-groups": response.headers.get("x-auth-request-groups", ""),
                    }
                    current_headers = dict(request.headers)
                    current_headers.update(auth_headers)
                    request.scope["headers"] = [
                        (k.lower().encode("latin-1"), v.encode("latin-1"))
                        for k, v in current_headers.items()
                    ]
                    if hasattr(request, "_headers"):
                        delattr(request, "_headers")

                return {"is_authenticated": True, "email": email, "groups": groups, "user": username}

        except Exception as e:
            logger.error(f"Auth Service unreachable: {e}")

    return {"is_authenticated": False}


# --- NiceGUI Application ---

# The internal Kubernetes DNS address to your proxy service's /oauth2/auth endpoint
AUTH_URL = "http://github-oauth-oauth2-proxy.auth.svc.cluster.local/oauth2/auth"


@ui.page('/')
def home_page(request: Request):
    # 1. Check if the gateway already injected headers
    identity = get_user_identity(request)

    # 2. If no headers, manually validate the cookies against the proxy
    if not is_authenticated(identity):
        auth_result = check_auth(AUTH_URL, request, forward_headers=True)
        if auth_result.get("is_authenticated"):
            identity["email"] = auth_result.get("email")
            identity["user"] = auth_result.get("user")

    with ui.column().classes('w-full items-center mt-12'):
        ui.label('Insights Hub').classes('text-4xl font-bold')

        if is_authenticated(identity):
            ui.label(f'Logged in as: {identity["email"]}').classes('text-lg text-green-600 mt-4')
            ui.button('Log Out', color='red').on(
                'click',
                js_handler='() => window.location.href="https://auth.undpgeohub.org/oauth2/sign_out?rd=https://insights.undpgeohub.org"'
            ).classes('mt-4')
        else:
            ui.label('You are browsing as a guest.').classes('text-lg text-gray-500 mt-4')
            ui.button('Log In with GitHub', color='blue').on(
                'click',
                js_handler='() => window.location.href="https://auth.undpgeohub.org/oauth2/start?rd=https://insights.undpgeohub.org"'
            ).classes('mt-4')


ui.run(fastapi_app=app, title='Dev test server')