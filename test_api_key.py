#!/usr/bin/env python
"""
A simple script to test the Companies House API key.
"""
import requests
import base64
import sys
import json

def test_api_key(api_key):
    """Test the API key with a simple request to the Companies House API."""
    print(f"Testing API key: {api_key}")
    
    # Format the API key for Basic Auth
    auth_str = f"{api_key}:"
    auth_header = base64.b64encode(auth_str.encode()).decode()
    
    # Make a simple request
    url = "https://api.company-information.service.gov.uk/company/00000006"
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Accept": "application/json"
    }
    
    print(f"Making request to: {url}")
    print(f"Using headers: {headers}")
    
    try:
        response = requests.get(url, headers=headers)
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
                print(formatted_json)
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
        api_key = sys.argv[1]
    else:
        # Default key from config
        api_key = "fa01873c-28b6-450b-ad3c-11a2e66acfeb"
    
    success = test_api_key(api_key)
    if not success:
        sys.exit(1) 