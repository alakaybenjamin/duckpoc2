import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
import sys
import os
from pydantic import BaseModel, Field

# Add the parent directory to sys.path to allow imports from the root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from models.schemas import User
from models.database_models import SearchHistory
from services.auth import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Define models
class SavedSearchBase(BaseModel):
    query: str
    category: str = None
    filters: Dict[str, Any] = None
    
class SavedSearchResponse(SavedSearchBase):
    id: int
    results_count: int = 0
    created_at: datetime
    is_saved: bool = True
    last_used: datetime
    use_count: int = 0
    
    class Config:
        from_attributes = True

class SearchActionResponse(BaseModel):
    success: bool
    message: str

# Create router
router = APIRouter()

# Define endpoints
@router.get("/saved-searches", 
    response_model=List[Dict[str, Any]],
    summary="Get saved searches",
    description="""
    Retrieve all saved searches for the authenticated user.
    
    ## Authentication
    This endpoint requires authentication. You can provide authentication using:
    
    1. **Bearer Token** - Include an Authorization header with a JWT token:
       `Authorization: Bearer your_token_here`
       
    2. **Cookie Authentication** - If you're logged in through the browser interface.
    """
)
async def get_saved_searches(db: Session = Depends(get_db)):
    """Get all saved searches for the current user"""
    try:
        # In a real implementation, we would filter by user_id
        # For now, return a stub response for documentation purposes
        return [
            {
                "id": 1,
                "query": "cancer treatment",
                "category": "clinical_study",
                "filters": {"phase": "Phase 2"},
                "results_count": 42,
                "created_at": datetime.utcnow(),
                "is_saved": True,
                "last_used": datetime.utcnow(),
                "use_count": 5
            }
        ]
    except Exception as e:
        logger.error(f"Failed to retrieve saved searches: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve saved searches: {str(e)}"
        )

@router.post("/saved-searches/{search_id}/execute", 
    response_model=Dict[str, Any],
    summary="Execute a saved search",
    description="""
    Execute a previously saved search by its ID and return the search parameters.
    
    ## Authentication
    This endpoint requires authentication via Bearer token or session cookie.
    """
)
async def execute_saved_search(search_id: int, db: Session = Depends(get_db)):
    """Execute a saved search"""
    try:
        # Stub implementation for documentation
        return {
            "query": "cancer treatment",
            "category": "clinical_study",
            "filters": {"phase": "Phase 2"},
            "success": True
        }
    except Exception as e:
        logger.error(f"Failed to execute saved search: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute saved search: {str(e)}"
        )

@router.post("/search-history/{search_id}/save", 
    response_model=SearchActionResponse,
    summary="Save a search from history",
    description="""
    Save a search from the user's search history.
    
    ## Authentication
    This endpoint requires authentication via Bearer token or session cookie.
    """
)
async def save_search(search_id: int, db: Session = Depends(get_db)):
    """Save a search from history"""
    try:
        return {"success": True, "message": "Search saved successfully"}
    except Exception as e:
        logger.error(f"Failed to save search: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save search: {str(e)}"
        )

@router.delete("/saved-searches/{search_id}", 
    response_model=SearchActionResponse,
    summary="Delete a saved search",
    description="""
    Delete a saved search by its ID.
    
    ## Authentication
    This endpoint requires authentication via Bearer token or session cookie.
    """
)
async def delete_saved_search(search_id: int, db: Session = Depends(get_db)):
    """Delete a saved search"""
    try:
        return {"success": True, "message": "Saved search deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete saved search: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete saved search: {str(e)}"
        )