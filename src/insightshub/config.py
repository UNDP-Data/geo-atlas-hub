from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    # Pydantic expects a STORAGE_SECRET in your .env file
    storage_secret: SecretStr
    server_name: str
    # oauth2-proxy base URL reachable from the app's network, used for
    # server-side session checks, e.g. http://auth-proxy:4180/oauth2
    #auth_internal_url: str
    # oauth2-proxy base URL as seen by the browser, used for sign-in/sign-out
    # redirects, e.g. https://auth.undpgeohub.org/oauth2
    #auth_public_url: str
    # Public origin of this app, e.g. https://careatlas.undpgeohub.org.
    # When empty it is derived from the request (forwarded headers first).

    # This tells Pydantic to look for a file named .env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def auth_enabled(self) -> bool:
        return bool(self.auth_internal_url and self.auth_public_url)

# Instantiate it once to use throughout your app
settings = Settings()