from fastapi import FastAPI, Depends, HTTPException, status, Request, Response, Body
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import uvicorn
import logging
import os
from starlette.middleware.sessions import SessionMiddleware
from search_examples import (
    SEARCH_REQUEST_EXAMPLE, 
    SEARCH_SUCCESS_EXAMPLE,
    UNAUTHORIZED_EXAMPLE,
    SERVER_ERROR_EXAMPLE
)
from api_responses import SEARCH_RESPONSES  # Import the response patterns
from routes.auth import generate_csrf_token, csrf_protect, CurrentUser, get_current_user_for_template

# Configure logging first thing
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Custom OpenAPI to add security schemes
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    # Generate OpenAPI schema
    openapi_schema = get_openapi(
        title="BioMed Search API",
        version="1.0.0",
        description="""
        A comprehensive biomedical search service API providing advanced search capabilities 
        for clinical studies, scientific papers, and data domains.

        ## Features
        * Search across different medical data collections
        * Save and manage search queries
        * View search history
        * Filter results by various criteria
        
        ## Authentication
        This API supports two authentication methods:
        
        1. **Bearer Token** - For programmatic API access:
           ```
           Authorization: Bearer your_token_here
           ```
           
        2. **OAuth2** - For web-based authentication flows
        """,
        routes=app.routes,
    )
    
    # Remove static files path from paths
    if "/static" in openapi_schema.get("paths", {}):
        del openapi_schema["paths"]["/static"]
    
    # Initialize components if it doesn't exist
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2": {
            "type": "oauth2",
            "flows": {
                "authorizationCode": {
                    "authorizationUrl": "/auth/login",
                    "tokenUrl": "/api/auth/token",
                    "scopes": {
                        "openid": "OpenID Connect",
                        "profile": "User profile",
                        "email": "User email"
                    }
                }
            }
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    # Make sure schemas are included in components
    if "schemas" not in openapi_schema["components"]:
        openapi_schema["components"]["schemas"] = {}
    
    # Define tag ordering and descriptions
    openapi_schema["tags"] = [
        {
            "name": "Search",
            "description": "Endpoints for searching across different medical data collections"
        },
        {
            "name": "Saved Searches",
            "description": "Endpoints for managing saved search queries"
        },
        {
            "name": "Search History",
            "description": "Endpoints for viewing and managing search history"
        },
        {
            "name": "Collections",
            "description": "Endpoints for managing collections of data items"
        },
        {
            "name": "Authentication",
            "description": "Endpoints for user authentication and authorization"
        }
    ]
    
    # Apply security globally - include both OAuth2 and Bearer options
    openapi_schema["security"] = [
        {"OAuth2": ["openid", "profile", "email"]},
        {"BearerAuth": []}
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Set environment variables for Google OAuth if not already set
os.environ.setdefault("OAUTH_ISSUER", "https://accounts.google.com")
os.environ.setdefault("OAUTH_CLIENT_ID", "your-google-client-id")
os.environ.setdefault("OAUTH_CLIENT_SECRET", "your-google-client-secret")
os.environ.setdefault("BASE_URL", "http://localhost:8001")

from database import get_db, init_db
#from models.database_models import User, ClinicalStudy, DataProduct, Collection, CollectionItem
#from models.schemas import SearchQuery, SearchResponse, CollectionSchema

# Import routes one-by-one with try/except
# to avoid cascading import failures
try:
    logger.info("Importing auth router...")
    from routes.auth import router as auth_router
except Exception as e:
    logger.error(f"Failed to import auth_router: {e}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
    auth_router = None

try:
    from routes.search import router as search_router
except Exception as e:
    logger.error(f"Failed to import search_router: {e}")
    search_router = None

try:
    from routes.collections import router as collections_router
except Exception as e:
    logger.error(f"Failed to import collections_router: {e}")
    collections_router = None

try:
    from routes.saved_searches import router as saved_searches_router
except Exception as e:
    logger.error(f"Failed to import saved_searches_router: {e}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
    saved_searches_router = None

try:
    from routes.history import router as history_router
except Exception as e:
    logger.error(f"Failed to import history_router: {e}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
    history_router = None

app = FastAPI(
    title="BioMed Search API",
    description="""
    A comprehensive biomedical search service API providing advanced multi-index search capabilities 
    with robust collection management and data product selection.

    ## Features
    * Advanced search across:
      - Clinical Studies (status, phase, categories)
      - Scientific Papers
      - Data Domains
    * Search history tracking
    * Saved searches
    * Collection management
    """,
    docs_url=None,  # Disable default docs URL
    redoc_url=None  # Disable default redoc URL
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware for cookie-based sessions
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET", "my-super-secret-key-for-sessions"),
    max_age=86400  # 24 hours
)

# Set custom OpenAPI schema generator
app.openapi = custom_openapi

# Mount static files (not included in schema)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure templates
templates = Jinja2Templates(directory="templates")

# Include routers with API prefix
if auth_router:
    logger.info("Mounting auth_router at /api/auth")
    app.include_router(
        auth_router,
        prefix="/api/auth",
        tags=["Authentication"],
        responses={401: {"description": "Unauthorized"}}
    )
    # Note: We mount at root level for auth callback handling but don't include in schema
    app.include_router(
        auth_router,
        tags=["Authentication-Root"],
        responses={401: {"description": "Unauthorized"}},
        include_in_schema=False
    )
else:
    logger.warning("auth_router is None, skipping mount")

if search_router:
    logger.info("Mounting search_router at /api")
    app.include_router(
        search_router,
        prefix="/api",
        tags=["Search"],
        responses={401: {"description": "Unauthorized"}}
    )
else:
    logger.warning("search_router is None, skipping mount")

if collections_router:
    app.include_router(
        collections_router,
        prefix="/api",
        tags=["Collections"],
        responses={401: {"description": "Unauthorized"}}
    )
else:
    logger.warning("collections_router is None, skipping mount")

if saved_searches_router:
    app.include_router(
        saved_searches_router,
        prefix="/api",
        tags=["Saved Searches"],
        responses={401: {"description": "Unauthorized"}}
    )
else:
    logger.warning("saved_searches_router is None, skipping mount")

if history_router:
    app.include_router(
        history_router,
        prefix="/api",
        tags=["Search History"],
        responses={401: {"description": "Unauthorized"}}
    )
else:
    logger.warning("history_router is None, skipping mount")

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request):
    """Serve the main search page"""
    try:
        csrf_token = generate_csrf_token(request)
        current_user = await get_current_user_for_template(request)
        return templates.TemplateResponse("index.html", {
            "request": request,
            "csrf_token": lambda: csrf_token,
            "current_user": current_user
        })
    except Exception as e:
        logger.error(f"Error rendering home page: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.get("/auth/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request):
    """Serve the login page"""
    try:
        # Generate CSRF token and add to template context
        csrf_token = generate_csrf_token(request)
        current_user = await get_current_user_for_template(request)
        
        # If user is already authenticated, redirect to the requested page or home
        if current_user.is_authenticated:
            next_url = request.query_params.get("next", "/")
            logger.info(f"User already authenticated, redirecting to: {next_url}")
            return RedirectResponse(url=next_url, status_code=302)
        
        return templates.TemplateResponse(
            "auth/login.html", 
            {
                "request": request,
                "csrf_token": lambda: csrf_token,
                "current_user": current_user
            }
        )
    except Exception as e:
        logger.error(f"Error rendering login page: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.get("/auth/register", response_class=HTMLResponse, include_in_schema=False)
async def register_page(request: Request):
    """Serve the registration page"""
    try:
        csrf_token = generate_csrf_token(request)
        current_user = await get_current_user_for_template(request)
        return templates.TemplateResponse("auth/register.html", {
            "request": request,
            "csrf_token": lambda: csrf_token,
            "current_user": current_user
        })
    except Exception as e:
        logger.error(f"Error rendering register page: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.get("/clinical-studies", response_class=HTMLResponse, include_in_schema=False)
async def clinical_studies(
    request: Request,
    q: Optional[str] = None
):
    """Serve the clinical studies search page"""
    try:
        logger.debug("Accessing clinical-studies route")
        csrf_token = generate_csrf_token(request)
        current_user = await get_current_user_for_template(request)
        
        # Check if user is authenticated
        if not current_user.is_authenticated:
            logger.warning("User not authenticated, redirecting to login")
            return RedirectResponse(url="/auth/login?next=/clinical-studies", status_code=302)
        
        logger.debug("Rendering clinical studies template")
        return templates.TemplateResponse(
            "clinical_studies.html",
            {
                "request": request,
                "results": None,
                "query": q or "",
                "csrf_token": lambda: csrf_token,
                "current_user": current_user
            }
        )
    except Exception as e:
        logger.error(f"Error in clinical_studies route: {str(e)}", exc_info=True)
        return templates.TemplateResponse(
            "clinical_studies.html",
            {
                "request": request,
                "results": None,
                "query": q or "",
                "csrf_token": lambda: generate_csrf_token(request),
                "current_user": await get_current_user_for_template(request),
                "error": "An error occurred while loading the page"
            }
        )

@app.get("/collections", response_class=HTMLResponse, include_in_schema=False)
async def collections_page(request: Request):
    """Serve the collections page"""
    try:
        logger.debug("Accessing collections route")
        csrf_token = generate_csrf_token(request)
        current_user = await get_current_user_for_template(request)
        
        # Check if user is authenticated
        if not current_user.is_authenticated:
            logger.warning("User not authenticated, redirecting to login")
            return RedirectResponse(url="/auth/login?next=/collections", status_code=302)
            
        logger.debug("Rendering collections template")
        return templates.TemplateResponse("collections.html", {
            "request": request,
            "csrf_token": lambda: csrf_token,
            "current_user": current_user
        })
    except Exception as e:
        logger.error(f"Error rendering collections page: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.get("/saved-searches", response_class=HTMLResponse, include_in_schema=False)
async def saved_searches_page(request: Request):
    """Serve the saved searches page"""
    try:
        logger.debug("Accessing saved-searches route")
        
        # Log request headers and cookies for debugging
        logger.debug(f"Request headers: {request.headers}")
        logger.debug(f"Request cookies: {request.cookies}")
        
        csrf_token = generate_csrf_token(request)
        current_user = await get_current_user_for_template(request)
        
        logger.debug(f"Authentication status: {current_user.is_authenticated}")
        
        # Check if user is authenticated
        if not current_user.is_authenticated:
            logger.warning("User not authenticated, redirecting to login")
            logger.debug(f"Redirect URL: /auth/login?next=/saved-searches")
            return RedirectResponse(url="/auth/login?next=/saved-searches", status_code=302)
        
        logger.debug("User is authenticated, rendering saved searches template")
        return templates.TemplateResponse("saved_searches.html", {
            "request": request,
            "csrf_token": lambda: csrf_token,
            "current_user": current_user
        })
    except Exception as e:
        logger.error(f"Error rendering saved searches page: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.get("/search-history", response_class=HTMLResponse, include_in_schema=False)
async def search_history_page(request: Request):
    """Serve the search history page"""
    try:
        logger.debug("Accessing search-history route")
        csrf_token = generate_csrf_token(request)
        current_user = await get_current_user_for_template(request)
        
        # Check if user is authenticated
        if not current_user.is_authenticated:
            logger.warning("User not authenticated, redirecting to login")
            return RedirectResponse(url="/auth/login?next=/search-history", status_code=302)
            
        logger.debug("Rendering search history template")
        return templates.TemplateResponse("search_history.html", {
            "request": request,
            "csrf_token": lambda: csrf_token,
            "current_user": current_user
        })
    except Exception as e:
        logger.error(f"Error rendering search history page: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.get("/data-domains", response_class=HTMLResponse, include_in_schema=False)
async def data_domains(
    request: Request,
    q: Optional[str] = None
):
    """
    Data domains browsing page
    """
    try:
        # Get current user
        current_user = await get_current_user_for_template(request)
        
        # Generate CSRF token
        csrf_token = generate_csrf_token(request)
        
        # Render template with context
        return templates.TemplateResponse(
            "data_domains.html", 
            {
                "request": request,
                "csrf_token": lambda: csrf_token,
                "current_user": current_user,
                "search_query": q or ""
            }
        )
    except Exception as e:
        logger.error(f"Error rendering data domains page: {str(e)}", exc_info=True)
        return templates.TemplateResponse(
            "error.html", 
            {"request": request, "error": "Error rendering data domains page"}
        )

@app.get("/scientific-papers", response_class=HTMLResponse, include_in_schema=False)
async def scientific_papers(
    request: Request,
    q: Optional[str] = None,
    journal: Optional[str] = None,
    date_range: Optional[str] = None,
    citations: Optional[str] = None
):
    """
    Scientific papers browsing page
    """
    try:
        # Get current user
        current_user = await get_current_user_for_template(request)
        
        # Generate CSRF token
        csrf_token = generate_csrf_token(request)
        
        # Render template with context
        return templates.TemplateResponse(
            "scientific_papers.html", 
            {
                "request": request,
                "csrf_token": lambda: csrf_token,
                "current_user": current_user,
                "search_query": q or "",
                "journal": journal or "",
                "date_range": date_range or "",
                "citations": citations or ""
            }
        )
    except Exception as e:
        logger.error(f"Error rendering scientific papers page: {str(e)}", exc_info=True)
        return templates.TemplateResponse(
            "error.html", 
            {"request": request, "error": "Error rendering scientific papers page"}
        )

@app.get("/api/health", include_in_schema=False)
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """
    Initialize database connection pool and tables
    """
    # Create tables if they don't exist
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialization complete.")
    
    # Initialize search registries
    logger.info("Initializing search registries...")
    import services.search.init_registry
    logger.info("Search registries initialized.")

@app.get("/api/debug/routes", include_in_schema=False)
async def debug_routes():
    """
    Debug endpoint to list all registered routes
    """
    routes = []
    for route in app.routes:
        path = getattr(route, "path", "")
        methods = [method for method in getattr(route, "methods", set())]
        name = getattr(route, "name", None)
        
        routes.append({
            "path": path,
            "methods": methods,
            "name": name
        })
    
    # Also check for router routes
    if auth_router:
        for route in auth_router.routes:
            full_path = f"/api/auth{route.path}"
            methods = [method for method in getattr(route, "methods", set())]
            name = getattr(route, "name", None)
            
            routes.append({
                "path": full_path,
                "methods": methods,
                "name": name,
                "router": "auth_router"
            })
    
    return {"routes": routes}

@app.get("/api/docs", response_class=HTMLResponse, include_in_schema=False)
async def custom_swagger_ui(request: Request):
    """Custom Swagger UI that requires authentication"""
    try:
        # Check if user is authenticated
        current_user = await get_current_user_for_template(request)
        if not current_user.is_authenticated:
            logger.warning("User not authenticated, redirecting to login")
            return RedirectResponse(url="/auth/login?next=/api/docs", status_code=302)
        
        # Generate CSRF token
        csrf_token = generate_csrf_token(request)
        
        # Get JWT token from cookie if available
        jwt_token = request.cookies.get("token", "")
        
        # Render the Swagger UI template
        return templates.TemplateResponse(
            "swagger.html", 
            {
                "request": request,
                "csrf_token": lambda: csrf_token,
                "current_user": current_user,
                "openapi_url": app.openapi_url,
                "title": app.title + " - Swagger UI",
                "jwt_token": jwt_token
            }
        )
    except Exception as e:
        logger.error(f"Error rendering Swagger UI: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.get("/api/redoc", response_class=HTMLResponse, include_in_schema=False)
async def custom_redoc(request: Request):
    """Custom ReDoc UI that requires authentication"""
    try:
        # Check if user is authenticated
        current_user = await get_current_user_for_template(request)
        if not current_user.is_authenticated:
            logger.warning("User not authenticated, redirecting to login")
            return RedirectResponse(url="/auth/login?next=/api/redoc", status_code=302)
        
        # Generate CSRF token
        csrf_token = generate_csrf_token(request)
        
        # Render the ReDoc template
        return templates.TemplateResponse(
            "redoc.html", 
            {
                "request": request,
                "csrf_token": lambda: csrf_token,
                "current_user": current_user,
                "openapi_url": app.openapi_url,
                "title": app.title + " - ReDoc"
            }
        )
    except Exception as e:
        logger.error(f"Error rendering ReDoc: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)