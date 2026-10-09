from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from pydantic import model_validator
from typing import Any

class Settings(BaseSettings):
    # Pydantic expects a STORAGE_SECRET in your .env file
    storage_secret: SecretStr
    app_name: str
    header_label: str
    # oauth2-proxy base URL reachable from the app's network, used for
    # server-side session checks, e.g. http://auth-proxy:4180/oauth2
    #auth_internal_url: str
    # oauth2-proxy base URL as seen by the browser, used for sign-in/sign-out
    # redirects, e.g. https://auth.undpgeohub.org/oauth2
    public_auth_url: str
    private_auth_url: str
    nb_github_token:str
    nb_github_repo:str
    # Public origin of this app, e.g. https://careatlas.undpgeohub.org.
    # When empty it is derived from the request (forwarded headers first).

    # This tells Pydantic to look for a file named .env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def auth_enabled(self) -> bool:
        return bool(self.auth_internal_url and self.auth_public_url)
    @model_validator(mode="before")
    @classmethod
    def strip_double_quotes_from_all_strings(cls, data: Any) -> Any:
        # Ensure the incoming data is a dictionary (it will be for Settings)
        if isinstance(data, dict):
            for key, value in data.items():
                # Check if the value is a string wrapped in literal quotes
                if isinstance(value, str) and value.startswith('"') and value.endswith('"'):
                    data[key] = value.strip('"')
        return data

    @model_validator(mode="before")
    @classmethod
    def strip_quotes_from_all_strings(cls, data: Any) -> Any:
        # Ensure the incoming data is a dictionary (it will be for Settings)
        if isinstance(data, dict):
            for key, value in data.items():
                # Check if the value is a string wrapped in literal quotes
                if isinstance(value, str) and value.startswith("'") and value.endswith("'"):
                    data[key] = value.strip("'")
        return data

# Instantiate it once to use throughout your app
settings = Settings()