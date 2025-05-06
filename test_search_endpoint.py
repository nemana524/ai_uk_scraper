#!/usr/bin/env python
"""
Test the Companies House search API endpoint which might have different permissions.
"""
import requests
from requests.auth import HTTPBasicAuth
import sys
import json

def test_search_api(api_key):
    """Test the API key with the search endpoint."""
    print(f"Testing API key with search endpoint: {api_key}")

    # Try the search endpoint instead
    url = "https://api.company-information.service.gov.uk/search/companies"
    params = {"q": "tech", "items_per_page": 5}
    
    print(f"Making request to: {url} with params: {params}")
    
    try:
        # Using HTTPBasicAuth directly
        response = requests.get(
            url, 
            params=params,
            auth=HTTPBasicAuth(api_key, ''),
            headers={"Accept": "application/json"}
        )
        
        print(f"Response status code: {response.status_code}")
        
        # Print headers for debugging
        print("\nResponse headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        # Print response for debugging
        print("\nResponse content:")
        if response.status_code == 200:
            try:
                # Pretty print JSON but limit output size
                data = response.json()
                formatted_json = json.dumps(data, indent=2)
                print(formatted_json[:500] + "..." if len(formatted_json) > 500 else formatted_json)
                print(f"\nFound {data.get('total_results', 0)} results")
                print("\nAPI key is valid and working correctly!")
                return True
            except json.JSONDecodeError:
                print(response.text)
        else:
            print(response.text)
            print("\nAPI key validation failed!")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        api_key = sys.argv[1].strip()
    else:
        # Default key from config
        api_key = "fa01873c-28b6-450b-ad3c-11a2e66acfeb"
    
    success = test_search_api(api_key)
    if not success:
        sys.exit(1) 