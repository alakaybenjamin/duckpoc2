from search_examples import (
    SEARCH_SUCCESS_EXAMPLE,
    UNAUTHORIZED_EXAMPLE,
    SERVER_ERROR_EXAMPLE
)

# Standard response patterns for search endpoints
SEARCH_RESPONSES = {
    200: {
        "description": "Successful search results",
        "content": {
            "application/json": {
                "example": SEARCH_SUCCESS_EXAMPLE
            }
        }
    },
    401: {
        "description": "Unauthorized: Authentication required",
        "content": {
            "application/json": {
                "example": UNAUTHORIZED_EXAMPLE
            }
        }
    },
    500: {
        "description": "Internal server error",
        "content": {
            "application/json": {
                "example": SERVER_ERROR_EXAMPLE
            }
        }
    }
}

# You can add more response patterns for other endpoint types
COLLECTION_RESPONSES = {
    200: {
        "description": "Collection successfully retrieved",
        "content": {
            "application/json": {
                "example": {
                    "id": 1,
                    "name": "Important Studies",
                    "description": "Collection of key clinical studies",
                    "items": [
                        {"id": "NCT04545072", "title": "Study of Tirzepatide in Participants With Type 2 Diabetes"},
                        {"id": "NCT04509791", "title": "Comparison of Blood Pressure Control Methods in Hypertension"}
                    ],
                    "created_at": "2023-05-15T10:30:00Z",
                    "updated_at": "2023-06-20T14:45:00Z"
                }
            }
        }
    },
    401: {
        "description": "Unauthorized: Authentication required",
        "content": {
            "application/json": {
                "example": UNAUTHORIZED_EXAMPLE
            }
        }
    },
    404: {
        "description": "Collection not found",
        "content": {
            "application/json": {
                "example": {"detail": "Collection with ID 123 not found"}
            }
        }
    },
    500: {
        "description": "Internal server error",
        "content": {
            "application/json": {
                "example": SERVER_ERROR_EXAMPLE
            }
        }
    }
} 