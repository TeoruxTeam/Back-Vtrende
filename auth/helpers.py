import uuid

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, HTTPException
from starlette.requests import Request

from .providers import OAUTH_PROVIDERS

oauth = OAuth()

google = oauth.register(
    name="google",
    client_id=OAUTH_PROVIDERS["google"]["client_id"],
    client_secret=OAUTH_PROVIDERS["google"]["client_secret"],
    authorize_url=OAUTH_PROVIDERS["google"]["authorize_url"],
    authorize_params=None,
    access_token_url=OAUTH_PROVIDERS["google"]["access_token_url"],
    client_kwargs={"scope": "openid profile email"},
    save_token=False,
)

facebook = oauth.register(
    name="facebook",
    client_id=OAUTH_PROVIDERS["facebook"]["client_id"],
    client_secret=OAUTH_PROVIDERS["facebook"]["client_secret"],
    authorize_url=OAUTH_PROVIDERS["facebook"]["authorize_url"],
    access_token_url=OAUTH_PROVIDERS["facebook"]["access_token_url"],
    client_kwargs={"scope": "email"},
    save_token=False,
)
