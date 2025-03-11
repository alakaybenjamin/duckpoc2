#!/usr/bin/env python3
"""
Example client for the BioMed Search API demonstrating Bearer token authentication.
"""
import requests
import json
import sys
import os

# Base URL for API
API_BASE_URL = "http://localhost:8001/api"

# Obtain a token through login
def get_auth_token(username, password):
    """Get an authentication token using credentials"""
    login_url = f"{API_BASE_URL}/auth/login"
    
    response = requests.post(
        login_url,
        data={
            "username": username,
            "password": password
        }
    )
    
    if response.status_code != 200:
        print(f"Error authenticating: {response.status_code}")
        print(response.text)
        sys.exit(1)
        
    data = response.json()
    return data["access_token"]

# Search using Bearer token authentication
def search_with_token(token, query, collection_type="clinical_study", filters=None):
    """Perform a search with Bearer token authentication"""
    search_url = f"{API_BASE_URL}/search"
    
    # Set up authentication header
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Create search payload
    payload = {
        "query": query,
        "collection_type": collection_type,
        "page": 1,
        "per_page": 10
    }
    
    if filters:
        payload["filters"] = filters
    
    # Make the API call
    response = requests.post(
        search_url,
        headers=headers,
        json=payload
    )
    
    if response.status_code != 200:
        print(f"Error searching: {response.status_code}")
        print(response.text)
        return None
        
    return response.json()

# Get saved searches using Bearer token authentication
def get_saved_searches(token):
    """Get all saved searches with Bearer token authentication"""
    saved_searches_url = f"{API_BASE_URL}/saved-searches"
    
    # Set up authentication header
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Make the API call
    response = requests.get(
        saved_searches_url,
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Error getting saved searches: {response.status_code}")
        print(response.text)
        return None
        
    return response.json()

def main():
    """Main function demonstrating API usage"""
    # Replace with actual credentials
    username = "user@example.com"
    password = "password123"
    
    print("Getting authentication token...")
    token = get_auth_token(username, password)
    print(f"Token obtained: {token[:10]}...")
    
    # Example 1: Simple search
    print("\nPerforming search for 'cancer treatment'...")
    results = search_with_token(token, "cancer treatment")
    if results:
        print(f"Found {len(results.get('results', []))} results")
        
    # Example 2: Search with filters
    print("\nPerforming search with filters...")
    filtered_results = search_with_token(
        token, 
        "diabetes", 
        collection_type="clinical_study",
        filters={"status": "recruiting", "phase": "Phase 3"}
    )
    if filtered_results:
        print(f"Found {len(filtered_results.get('results', []))} filtered results")
    
    # Example 3: Get saved searches
    print("\nGetting saved searches...")
    saved_searches = get_saved_searches(token)
    if saved_searches:
        print(f"Found {len(saved_searches)} saved searches")

if __name__ == "__main__":
    main() 