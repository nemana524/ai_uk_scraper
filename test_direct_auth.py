#!/usr/bin/env python
"""
Direct test using requests.auth.HTTPBasicAuth to test Companies House API access.
"""
import requests
from requests.auth import HTTPBasicAuth
import sys
import json

def test_api_key(api_key):
    """Test the API key directly using HTTPBasicAuth."""
    print(f"Testing API key: {api_key}")

    # Make a simple request using direct HTTPBasicAuth
    url = "https://api.company-information.service.gov.uk/company/00000006"
    
    print(f"Making request to: {url}")
    print(f"Using HTTPBasicAuth with API key as username")
    
    try:
        # Using the API key as username with empty password
        response = requests.get(
            url, 
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
                # Pretty print JSON
                formatted_json = json.dumps(response.json(), indent=2)
                print(formatted_json[:500] + "..." if len(formatted_json) > 500 else formatted_json)
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
    
    success = test_api_key(api_key)
    if not success:
        sys.exit(1) 