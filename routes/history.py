import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import sys
import os
from datetime import datetime
from pydantic import BaseModel, Field

# Add the parent directory to sys.path to allow imports from the root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from routes import auth

# Configure logging
logger = logging.getLogger(__name__)

# Define models
class HistoryEntryBase(BaseModel):
    query: str
    category: str = None
    filters: Dict[str, Any] = None
    
class HistoryEntry(HistoryEntryBase):
    id: int
    results_count: int = 0
    created_at: datetime
    is_saved: bool = False
    last_used: datetime
    use_count: int = 0
    
    class Config:
        from_attributes = True

class HistoryResponse(BaseModel):
    success: bool
    message: str

# Create router
router = APIRouter()

# Define endpoints
@router.get("/search-history", 
    response_model=List[Dict[str, Any]],
    summary="Get search history",
    description="""
    Retrieve the search history for the authenticated user.
    
    ## Authentication
    This endpoint requires authentication. You can provide authentication using:
    
    1. **Bearer Token** - Include an Authorization header with a JWT token:
       `Authorization: Bearer your_token_here`
       
    2. **Cookie Authentication** - If you're logged in through the browser interface.
    """
)
async def get_search_history(db: Session = Depends(get_db), user_info: Dict = Depends(auth.get_current_user)):
    """
    Get the search history for the current user
    """
    try:
        from models.database_models import SearchHistory
        
        # Get user ID from authentication
        user_id = user_info.get("id")
        
        if not user_id:
            logger.warning("User not authenticated properly or missing ID")
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
        
        # Query search history for the current user
        history_entries = db.query(SearchHistory)\
            .filter(SearchHistory.user_id == user_id)\
            .order_by(SearchHistory.created_at.desc())\
            .all()
        
        # Convert to response format
        result = []
        for entry in history_entries:
            result.append({
                "id": entry.id,
                "query": entry.query,
                "category": entry.category,
                "filters": entry.filters if entry.filters else {},
                "results_count": entry.results_count,
                "created_at": entry.created_at,
                "is_saved": entry.is_saved,
                "last_used": entry.last_used,
                "use_count": entry.use_count
            })
        
        return result
    except Exception as e:
        logger.error(f"Failed to retrieve search history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve search history: {str(e)}"
        )

@router.post("/search-history", 
    response_model=HistoryResponse,
    summary="Save search to history",
    description="""
    Save a search query to the user's search history.
    
    ## Authentication
    This endpoint requires authentication via Bearer token or session cookie.
    """
)
async def save_search(search_data: HistoryEntryBase, db: Session = Depends(get_db), user_info: Dict = Depends(auth.get_current_user)):
    """
    Save a search to history
    """
    try:
        from models.database_models import SearchHistory
        
        # Get user ID from authentication
        user_id = user_info.get("id")
        
        if not user_id:
            logger.warning("User not authenticated properly or missing ID")
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
        
        # Create a new search history entry
        search_history = SearchHistory(
            user_id=user_id,
            query=search_data.query,
            category=search_data.category,
            filters=search_data.filters,
            results_count=0,  # This will be updated when search is performed
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow(),
            use_count=1
        )
        
        # Add and commit to the database
        db.add(search_history)
        db.commit()
        
        return {"success": True, "message": "Search saved to history successfully"}
    except Exception as e:
        logger.error(f"Failed to save search: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save search: {str(e)}"
        )