"""
Search provider implementation for scientific papers.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request, Body
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import logging
import sys
import os
from datetime import datetime

# Add the parent directory to sys.path to allow imports from the root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from models.schemas import SearchResponse
from services.search.service import SearchService
from pydantic import BaseModel, Field, validator
from api_responses import SEARCH_RESPONSES
from models.search_query import SearchQuery
from routes.auth import get_current_user_for_template, csrf_protect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.auth import get_current_user

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()

# Authentication scheme
security = HTTPBearer(auto_error=False)

# Authentication dependency
async def get_authenticated_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """Get authenticated user from token or session"""
    token = None
    
    # First try from Authorization header
    if credentials:
        token = credentials.credentials
        logger.debug("Token found in Authorization header")
    
    # If no token in header, check cookies
    if not token and "token" in request.cookies:
        token = request.cookies.get("token")
        logger.debug("Token found in cookies")
        
    # If no token found, check if user is authenticated via session
    if not token and request.session.get("authenticated"):
        logger.debug("User authenticated via session")
        # Return a basic user context for session authentication
        return {"authenticated": True, "role": "user", "source": "session"}
    elif not token:
        # No authentication found, return error
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for this endpoint",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # If we have a token, decode it to get user information
    try:
        # Import the decoding function to avoid circular imports
        from security import decode_access_token
        
        # Decode the token
        user_info = decode_access_token(token)
        logger.debug(f"User authenticated via token: {user_info}")
        return user_info
    except Exception as e:
        logger.error(f"Error decoding token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

class SearchRequest(BaseModel):
    query: str = Field(
        ..., 
        min_length=2, 
        description="Search query string",
        example="genomics cancer"
    )
    collection_type: str = Field(
        default="scientific_paper",
        description="Type of collection to search",
        example="scientific_paper"
    )
    schema_type: str = Field(
        default="default",
        description="Response schema type",
        example="default"
    )
    page: int = Field(
        default=1, 
        ge=1, 
        description="Page number",
        example=1
    )
    per_page: int = Field(
        default=10, 
        ge=1, 
        le=100, 
        description="Items per page",
        example=10
    )
    filters: Dict[str, Any] = Field(
        default_factory=dict,
        description="""
        Optional filters for the search:
        - journal: Filter by specific journal (e.g., "Nature Medicine", "Science")
        - date_range: Filter by publication date ("last_week", "last_month", "last_year")
        - citations: Filter by citation count ("0-10", "11-50", "51-100", "100+")
        """,
        example={
            "journal": "Nature Medicine",
            "date_range": "last_month",
            "citations": "11-50"
        }
    )

    @validator('collection_type')
    def validate_collection_type(cls, v):
        allowed_types = ['clinical_study', 'scientific_paper', 'data_domain']
        if v not in allowed_types:
            raise ValueError(f"Collection type must be one of: {', '.join(allowed_types)}")
        return v

    @validator('schema_type')
    def validate_schema_type(cls, v):
        allowed_types = ['default', 'compact', 'detailed', 'scientific_paper', 'data_domain', 'clinical_study_custom']
        if v not in allowed_types:
            raise ValueError(f"Schema type must be one of: {', '.join(allowed_types)}")
        return v

@router.post("/search", 
    # Don't use a fixed response_model to allow custom formats
    # response_model=SearchResponse,
    summary="Search across collections",
    description="""
    Execute a search across specified collections with configurable output schema and filters.

    Supports searching in:
    - Scientific Papers (titles, abstracts, keywords)
    - Clinical Studies
    - Data Domains

    For scientific papers, you can filter by:
    - Journal name
    - Publication date range
    - Citation count range

    The response includes pagination information and can be formatted according to different schema types.
    
    ## Authentication
    This endpoint requires authentication. You can provide authentication in one of these ways:
    
    1. **Bearer Token** - Include an Authorization header with a JWT token:
       `Authorization: Bearer your_token_here`
       
       When using Swagger UI, enter your Bearer token in the token field at the top of the page.
       
    2. **Cookie Authentication** - If you're logged in through the browser interface, 
       the session cookie will be used automatically.
       
    ## CSRF Protection
    When using cookie-based authentication, a CSRF token must be provided in the X-CSRF-Token header.
    This is not required when using Bearer token authentication.
    
    ## Example Request
    ```
    curl -X 'POST' \\
      'http://localhost:8001/api/search' \\
      -H 'accept: application/json' \\
      -H 'Content-Type: application/json' \\
      -H 'X-CSRF-Token: 47ec88c12d16ccb7bee99a9287ec6a0d' \\
      -H 'Authorization: Bearer aasddf' \\
      -d '{
      "query": "cancer",
      "collection_type": "clinical_study",
      "schema_type": "default",
      "page": 1,
      "per_page": 10
    }'
    ```
    """
)
async def search(
    search_request: SearchRequest,
    user_info: Dict = Depends(get_authenticated_user),
    csrf_check: bool = Depends(csrf_protect),
    db: Session = Depends(get_db)
):
    """
    Search across collections with configurable output schema and filters.
    Authentication is required.
    """
    try:
        logger.debug(f"Search request received: {search_request}")
        logger.debug(f"User info: {user_info}")
        logger.debug(f"Schema type requested: {search_request.schema_type!r}")
        logger.debug(f"Collection type: {search_request.collection_type!r}")

        # Create search service
        search_service = SearchService(db)

        # Apply user context for filtering if available
        filters = search_request.filters.copy()
        if user_info:
            # Apply user-specific filters here based on roles
            user_role = user_info.get("role", "user")
            if user_role != "admin" and "restricted_content" in filters:
                # Non-admins can't access restricted content
                filters.pop("restricted_content")

        # Execute search with user context if available
        terms = []
        if search_request.query:
            terms = search_request.query.split(' OR ')
            # Remove empty terms
            terms = [term.strip() for term in terms if term.strip()]
        
        logger.debug(f"Search terms after processing: {terms}")
        logger.debug(f"Final schema_type being used: {search_request.schema_type!r}")
        
        results = search_service.search(
            collection_type=search_request.collection_type,
            terms=terms,
            filters=filters,
            page=search_request.page,
            per_page=search_request.per_page,
            schema_type=search_request.schema_type,
            user_context=user_info  # Pass user context to search service if needed
        )
        
        # Log the search to the user's search history if user is authenticated
        if user_info and "id" in user_info:
            try:
                from models.database_models import SearchHistory
                
                # Count the total results to save in history
                results_count = 0
                if isinstance(results, dict) and 'pagination' in results:
                    results_count = results['pagination'].get('total', 0)
                
                # Create a new search history entry
                search_history = SearchHistory(
                    user_id=user_info["id"],
                    query=" ".join(terms) if terms else "",
                    category=search_request.collection_type,
                    filters=search_request.filters,
                    results_count=results_count,
                    created_at=datetime.utcnow(),
                    last_used=datetime.utcnow(),
                    use_count=1
                )
                
                # Add and commit to the database
                db.add(search_history)
                db.commit()
                logger.debug(f"Search history logged for user {user_info['id']}")
                
            except Exception as e:
                # If logging history fails, just log the error but don't interrupt the search
                logger.error(f"Failed to log search history: {str(e)}", exc_info=True)
                db.rollback()
        
        if isinstance(results, dict):
            logger.debug(f"Result keys: {list(results.keys())}")
            if 'results' in results and results['results']:
                logger.debug(f"First result keys: {list(results['results'][0].keys())}")
        
        return results

    except ValueError as e:
        logger.error(f"Validation error in search: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        logger.error(f"Search operation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Search operation failed: {str(e)}"
        )

@router.get("/filters", response_model=Dict[str, Any])
async def get_filters(
    collection_type: str = Query("scientific_paper", description="Type of collection"),
    db: Session = Depends(get_db)
):
    """
    Get available filters for a collection type
    """
    try:
        search_service = SearchService(db)
        provider = search_service.get_provider(collection_type)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported collection type: {collection_type}"
            )
        
        filters = provider.get_available_filters()
        return filters
    except Exception as e:
        logger.error(f"Error getting filters: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching filters"
        )

@router.get("/suggest",
    summary="Get search suggestions",
    description="""
    Get search suggestions based on partial input
    
    ## Authentication
    This endpoint requires authentication. You can provide authentication in one of these ways:
    
    1. **Bearer Token** - Include an Authorization header with a JWT token
    2. **Cookie Authentication** - If you're logged in through the browser interface
    """
)
async def get_suggestions(
    q: str = Query(
        ..., 
        min_length=2,
        description="Search query for suggestions",
        example="genom"
    ),
    collection_type: str = Query(
        'scientific_paper', 
        description="Type of collection for suggestions"
    ),
    user_info: Dict = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """
    Get search suggestions based on partial input
    """
    try:
        logger.debug(f"Suggestion request received for query: {q}, collection: {collection_type}")

        # Create search service
        search_service = SearchService(db)

        # Execute search with compact schema for suggestions
        results = search_service.search(
            collection_type=collection_type,
            terms=[q],
            filters={},
            per_page=5,
            schema_type='compact'
        )
        
        logger.debug(f"Suggestion results type: {type(results)}")
        
        # Handle different result formats
        suggestions = []
        if isinstance(results, dict) and 'results' in results:
            # Format from transformer
            for r in results['results']:
                try:
                    suggestions.append({
                        "text": r.get('title', 'Untitled'),
                        "type": r.get('type', collection_type)
                    })
                except Exception as err:
                    logger.error(f"Error processing suggestion result: {str(err)}")
        elif isinstance(results, list):
            # Direct results list
            for r in results:
                try:
                    if hasattr(r, 'title') and hasattr(r, 'type'):
                        suggestions.append({
                            "text": r.title,
                            "type": r.type
                        })
                    elif isinstance(r, dict):
                        suggestions.append({
                            "text": r.get('title', 'Untitled'),
                            "type": r.get('type', collection_type)
                        })
                except Exception as err:
                    logger.error(f"Error processing suggestion result: {str(err)}")

        return {"suggestions": suggestions}

    except Exception as e:
        logger.error(f"Failed to get suggestions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suggestions: {str(e)}"
        )

@router.get("/debug/transformers")
async def debug_transformers():
    """Debug endpoint to see registered transformers"""
    from services.search.base import SchemaRegistry
    import importlib
    
    # Try to import the initialization module again
    try:
        importlib.reload(importlib.import_module('services.search.init_registry'))
        logger.debug("Reloaded initialization module")
    except Exception as e:
        logger.error(f"Error reloading initialization module: {str(e)}")
    
    # Check if transformers are registered
    transformers = list(SchemaRegistry._transformers.keys())
    logger.debug(f"Found transformers: {transformers}")
    
    # Register them manually for this request if needed
    if not transformers:
        from services.search.transformers import (
            DefaultSchemaTransformer,
            CompactSchemaTransformer,
            DetailedSchemaTransformer,
            ScientificPaperSchemaTransformer,
            DataDomainSchemaTransformer,
            ClinicalStudyCustomTransformer
        )
        
        SchemaRegistry._transformers = {
            'default': DefaultSchemaTransformer,
            'compact': CompactSchemaTransformer,
            'detailed': DetailedSchemaTransformer, 
            'scientific_paper': ScientificPaperSchemaTransformer,
            'data_domain': DataDomainSchemaTransformer,
            'clinical_study_custom': ClinicalStudyCustomTransformer
        }
        
        transformers = list(SchemaRegistry._transformers.keys())
        logger.debug(f"Registered transformers manually: {transformers}")
    
    return {
        "transformers": transformers,
        "manually_registered": not transformers
    }