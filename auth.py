import os
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.security import OAuth2AuthorizationCodeBearer
from starlette.middleware.sessions import SessionMiddleware
import requests
from oauthlib.oauth2 import WebApplicationClient
import logging
from database import get_db
from models.database_models import User
from extensions import db
import functools

logger = logging.getLogger(__name__)

auth = APIRouter()

# OAuth 2.0 configuration
OAUTH_ISSUER = os.environ.get("OAUTH_ISSUER")
OAUTH_CLIENT_ID = os.environ.get("OAUTH_CLIENT_ID")
OAUTH_CLIENT_SECRET = os.environ.get("OAUTH_CLIENT_SECRET")
OAUTH_DISCOVERY_URL = f"{OAUTH_ISSUER}/.well-known/openid-configuration"

# Determine if we're running locally or in production
BASE_URL = "https://workspace.alexbenjamin198.repl.co"
CALLBACK_PATH = "/auth/callback"
REDIRECT_URI = f"{BASE_URL}{CALLBACK_PATH}"

logger.info(f"OAuth Configuration:")
logger.info(f"OAUTH_ISSUER: {OAUTH_ISSUER}")
logger.info(f"Base URL: {BASE_URL}")
logger.info(f"Redirect URI: {REDIRECT_URI}")

oauth_client = WebApplicationClient(OAUTH_CLIENT_ID)

def setup_oauth(app):
    """Initialize OAuth configuration"""
    async def get_current_user(request: Request, db=Depends(get_db)) -> Optional[User]:
        user_id = request.session.get("user_id")
        if user_id:
            user = db.query(User).get(int(user_id))
            if user:
                request.state.user = user
                return user
        return None

    app.dependency_overrides[get_current_user] = get_current_user

def require_auth(func):
    """Decorator to check auth status and redirect to OAuth if needed"""
    @functools.wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        if "user_id" not in request.session:
            request.session["next"] = str(request.url)
            logger.info(f"Storing next URL in session: {request.session.get('next')}")
            return RedirectResponse(url="/auth/login")

        # Get user and store in request state
        db = next(get_db())
        user = db.query(User).get(int(request.session["user_id"]))
        if not user:
            request.session.clear()
            return RedirectResponse(url="/auth/login")

        request.state.user = user
        return await func(request, *args, **kwargs)
    return wrapper

@auth.get("/login")
async def login(request: Request):
    """Initiate OAuth login flow"""
    try:
        # Store the original URL if not already stored
        if "next" not in request.session:
            request.session["next"] = str(request.url_for("index"))

        logger.info(f"Starting login flow, next URL stored: {request.session.get('next')}")

        # Get OAuth provider configuration
        provider_cfg = requests.get(OAUTH_DISCOVERY_URL).json()
        authorization_endpoint = provider_cfg["authorization_endpoint"]

        logger.info(f"Starting OAuth login flow")
        logger.info(f"Using redirect URI: {REDIRECT_URI}")

        # Generate OAuth request URI
        request_uri = oauth_client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=REDIRECT_URI,
            scope=["openid", "profile", "email"]
        )

        logger.info(f"Generated authorization request URI: {request_uri}")
        return RedirectResponse(url=request_uri)
    except Exception as e:
        logger.error(f"OAuth login error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=503, detail="Authentication service unavailable")

@auth.get("/callback")
async def callback(request: Request, db=Depends(get_db)):
    """Handle OAuth callback"""
    try:
        # Get authorization code
        code = request.query_params.get("code")
        provider_cfg = requests.get(OAUTH_DISCOVERY_URL).json()
        token_endpoint = provider_cfg["token_endpoint"]
        userinfo_endpoint = provider_cfg["userinfo_endpoint"]

        logger.info(f"Processing OAuth callback")
        logger.info(f"Using redirect URI: {REDIRECT_URI}")
        logger.info(f"Request URL: {str(request.url)}")
        logger.info(f"Next URL from session: {request.session.get('next')}")

        # Get tokens
        token_url, headers, body = oauth_client.prepare_token_request(
            token_endpoint,
            authorization_response=str(request.url).replace("http:", "https:"),
            redirect_url=REDIRECT_URI,
            code=code
        )
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET),
        ).json()

        # Parse response
        oauth_client.parse_request_body_response(token_response)

        # Get user info
        uri, headers, body = oauth_client.add_token(userinfo_endpoint)
        userinfo = requests.get(uri, headers=headers).json()

        if userinfo.get("email_verified"):
            # Get or create user
            user = db.query(User).filter_by(email=userinfo["email"]).first()
            if not user:
                user = User(
                    username=userinfo.get("name", userinfo["email"]),
                    email=userinfo["email"]
                )
                db.add(user)
                db.commit()

            # Store user ID in session
            request.session["user_id"] = user.id
            request.state.user = user

            # Get the original URL from session
            next_url = request.session.pop("next", None)
            logger.info(f"Retrieved next URL from session: {next_url}")

            if not next_url or next_url == "None":
                next_url = request.url_for("index")
                logger.info(f"No next URL found, defaulting to index: {next_url}")

            logger.info(f"Redirecting to: {next_url}")
            return RedirectResponse(url=next_url)

        raise HTTPException(status_code=400, detail="Email not verified")

    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail="Authentication failed")

@auth.get("/logout")
async def logout(request: Request):
    """Handle logout"""
    request.session.clear()
    return RedirectResponse(url="/")