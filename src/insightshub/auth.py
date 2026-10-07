import httpx
import logging
from fastapi import Request
from dataclasses import dataclass
from urllib.parse import urlencode
from insightshub.config import settings


logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class User:
    name: str = 'Guest'
    email: str = ''
    groups: tuple[str, ...] = ()

    @property
    def display_name(self) -> str:
        return self.name or self.email

    @property
    def is_authenticated(self) -> bool:
        return self.name != 'Guest' and self.email != ''


def page_url(request: Request) -> str:
    """Absolute URL of the current page as the browser sees it."""
    path = request.url.path
    if request.url.query:
        path += f"?{request.url.query}"
    # if settings.public_url:
    #     return settings.public_url + path
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.headers.get("host", ""))
    return f"{scheme}://{host}{path}"

def sign_in_url(request: Request) -> str:
    return f"{settings.public_auth_url}/start?{urlencode({'rd': page_url(request)})}"

def sign_out_url(request: Request) -> str:
    return f"{settings.public_auth_url}/sign_out?{urlencode({'rd': page_url(request)})}"


def user_from_headers(request: Request) -> User:
    h = request.headers
    email = h.get("x-auth-request-email") or h.get("x-forwarded-email") or User.email
    user = h.get("x-auth-request-user") or h.get("x-forwarded-user") or User.name
    groups_raw = h.get("x-auth-request-groups") or h.get("x-forwarded-groups") or ""
    groups = tuple([g.strip() for g in groups_raw.split(",") if g.strip()])

    return User(name=user, email=email, groups=groups)


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
                email = response.headers.get("x-auth-request-email", "")
                groups_raw = response.headers.get("x-auth-request-groups", "")
                groups = tuple([g.strip() for g in groups_raw.split(",")])
                username = response.headers.get("x-auth-request-user", "Guest")

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

                return User(name=username, email=email, groups=groups)

        except Exception as e:
            logger.error(f"Auth Service unreachable: {e}")

    return User()

async def authenticate(url: str, request: Request, forward_headers=False)-> User:

    user = user_from_headers(request=request)
    if user.is_authenticated:
        return user

    # DEBUG 1: Verify the URL and the cookies received from the browser
    logger.info(f"DEBUG 0 - Target URL: {url}")
    logger.info(f"DEBUG 1 - Cookies: {request.cookies}")

    async with httpx.AsyncClient(timeout=3.0) as client:
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
            response = await client.get(url, cookies=request.cookies, headers=headers)
            # DEBUG 2: Verify the proxy's response
            logger.info(f"DEBUG 2 - Proxy Status Code: {response.status_code}")
            logger.info(f"DEBUG 3 - Proxy Headers: {response.headers}")

            if response.status_code in (200, 202):
                email = response.headers.get("x-auth-request-email", "")
                groups_raw = response.headers.get("x-auth-request-groups", "")
                groups = [g.strip() for g in groups_raw.split(",")] if groups_raw else []
                username = response.headers.get("x-auth-request-user", "Guest")

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

                return User(name=username, email=email, groups=groups)

        except Exception as e:
            logger.error(f"Auth Service unreachable: {e}")

    return User()


