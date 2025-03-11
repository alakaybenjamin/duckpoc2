# Example request for search endpoint
SEARCH_REQUEST_EXAMPLE = {
    "query": "diabetes OR hypertension",
    "collection_type": "clinical_study",
    "page": 1,
    "per_page": 10,
    "filters": {
        "status": ["Recruiting", "Active"],
        "phase": ["Phase 2", "Phase 3"],
        "condition": ["Type 2 Diabetes"]
    },
    "schema_type": "default"
}

# Example successful response
SEARCH_SUCCESS_EXAMPLE = {
    "results": [
        {
            "id": "NCT04545072",
            "title": "Study of Tirzepatide in Participants With Type 2 Diabetes",
            "status": "Recruiting",
            "phase": "Phase 3",
            "conditions": ["Type 2 Diabetes Mellitus"],
            "interventions": ["Drug: Tirzepatide", "Drug: Placebo"],
            "sponsors": ["Eli Lilly and Company"],
            "enrollment": 1500,
            "start_date": "2020-09-15",
            "completion_date": "2023-06-30"
        },
        {
            "id": "NCT04509791",
            "title": "Comparison of Blood Pressure Control Methods in Hypertension",
            "status": "Active, not recruiting", 
            "phase": "Phase 2",
            "conditions": ["Hypertension"],
            "interventions": ["Procedure: Standard care", "Device: Remote monitoring"],
            "sponsors": ["Mayo Clinic"],
            "enrollment": 250,
            "start_date": "2020-08-01",
            "completion_date": "2022-12-31"
        }
    ],
    "page": 1,
    "per_page": 10,
    "total": 2
}

# Example error responses
UNAUTHORIZED_EXAMPLE = {
    "detail": "Authentication required"
}

SERVER_ERROR_EXAMPLE = {
    "detail": "Search operation failed: Database connection error"
}