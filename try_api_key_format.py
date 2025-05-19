#!/usr/bin/env python
"""
Test script that tries different authentication formats for Companies House API.
"""
import requests
import base64
import sys
import json

def test_all_formats(api_key):
    """Try all possible authentication formats with the API key."""
    print(f"Testing API key with all possible formats: {api_key}")
    
    # Remove any whitespace
    api_key = api_key.strip()
    
    # Test URLs - try both a company profile and search
    urls = [
        "https://api.company-information.service.gov.uk/company/00000006",
        "https://api.company-information.service.gov.uk/search/companies?q=tech&items_per_page=1"
    ]
    
    # Method 1: HTTPBasicAuth from requests
    def method1(url):
        print("\n--- Method 1: Using requests.auth.HTTPBasicAuth ---")
        print(f"Requesting URL: {url}")
        try:
            response = requests.get(
                url,
                auth=requests.auth.HTTPBasicAuth(api_key, ''),
                headers={"Accept": "application/json"}
            )
            return response
        except Exception as e:
            print(f"Error: {e}")
            return None

    # Method 2: Manual Basic Auth header (properly encoded)
    def method2(url):
        print("\n--- Method 2: Manual Basic Auth header ---")
        print(f"Requesting URL: {url}")
        try:
            # Encode as base64: "api_key:"
            auth_string = f"{api_key}:"
            auth_bytes = auth_string.encode('ascii')
            base64_bytes = base64.b64encode(auth_bytes)
            base64_string = base64_bytes.decode('ascii')
            
            response = requests.get(
                url,
                headers={
                    "Authorization": f"Basic {base64_string}",
                    "Accept": "application/json"
                }
            )
            return response
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    # Method 3: Try with just the plain API key
    def method3(url):
        print("\n--- Method 3: API key directly in Authorization header ---")
        print(f"Requesting URL: {url}")
        try:
            response = requests.get(
                url,
                headers={
                    "Authorization": api_key,
                    "Accept": "application/json"
                }
            )
            return response
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    # Print response from test method
    def print_response(response):
        if response is None:
            return False
            
        print(f"Response status: {response.status_code}")
        print("Response headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        print("\nResponse content:")
        print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
        
        return response.status_code == 200
    
    # Try all methods with all URLs
    any_success = False
    
    for url in urls:
        print(f"\n\n=== Testing URL: {url} ===")
        
        # Try method 1
        response = method1(url)
        success = print_response(response)
        any_success = any_success or success
        
        # Try method 2
        response = method2(url)
        success = print_response(response)
        any_success = any_success or success
        
        # Try method 3
        response = method3(url)
        success = print_response(response)
        any_success = any_success or success
    
    if any_success:
        print("\n✅ API key works with at least one method!")
        return True
    else:
        print("\n❌ All authentication methods failed.")
        print("""
Possible issues:
1. Your API key hasn't been activated yet (can take some time)
2. Your API key may have restrictions (IP, domains, etc.)
3. Your API key may have expired or been revoked
4. You might need to register the application again

Try these steps:
1. Log in to developer.company-information.service.gov.uk
2. Generate a new API key
3. Make sure there are no restrictions
4. Check if your application needs to be registered for specific endpoints
""")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        api_key = sys.argv[1].strip()
    else:
        # Prompt for API key for added security
        api_key = input("Enter your Companies House API Key: ").strip()
        if not api_key:
            # Use default if empty input
            api_key = "fa01873c-28b6-450b-ad3c-11a2e66acfeb"
    
    success = test_all_formats(api_key)
    if not success:
        sys.exit(1) 