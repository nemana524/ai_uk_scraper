"""
API client for the Companies House API.
"""
import time
import requests
from requests.auth import HTTPBasicAuth
import json
import logging
from typing import Dict, Any, Optional, List, Union
from src.config import API_KEY, COMPANY_SEARCH_URL, COMPANY_PROFILE_URL, OFFICERS_URL, FILING_HISTORY_URL

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompaniesHouseClient:
    """Client for interacting with the Companies House API."""
    
    def __init__(self, api_key: str = API_KEY) -> None:
        """Initialize the API client.
        
        Args:
            api_key: The API key for Companies House
        """
        self.api_key = api_key.strip() if api_key else ""
        self.session = requests.Session()
        
        # Set up Basic Authentication - Companies House API requires the API key as 
        # the username with an empty password
        self.session.auth = HTTPBasicAuth(self.api_key, '')
        
        # Set default headers
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        
        self.last_request_time = 0
        self._rate_limit_remaining = 600  # default starting value
        
        logger.info("API client initialized")
        logger.debug(f"Using API key: {self.api_key[:5]}...{self.api_key[-5:] if len(self.api_key) > 10 else ''}")
    
    def _rate_limit(self) -> None:
        """Implement rate limiting to avoid hitting API limits."""
        # Ensure at least 0.1 seconds between requests
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < 0.1:
            time.sleep(0.1 - time_since_last)
        
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a request to the Companies House API.
        
        Args:
            url: The API endpoint URL
            params: Optional query parameters
            
        Returns:
            The JSON response as a dictionary
        """
        self._rate_limit()
        
        try:
            logger.debug(f"Making request to: {url} with params: {params}")
            
            # Use the session with pre-configured auth
            response = self.session.get(url, params=params)
            
            # Log response status for debugging
            logger.debug(f"Response status: {response.status_code}")
            
            # Update rate limit info from headers if available
            if 'X-Ratelimit-Remain' in response.headers:
                self._rate_limit_remaining = int(response.headers['X-Ratelimit-Remain'])
            
            # For debugging
            if response.status_code != 200:
                logger.debug(f"Response headers: {response.headers}")
                logger.debug(f"Response content: {response.text}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            
            # More detailed error information when available
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                logger.error(f"Response content: {e.response.text}")
                
            if e.response.status_code == 429:
                logger.warning("Rate limit exceeded. Sleeping for 60 seconds.")
                time.sleep(60)
                return self._make_request(url, params)
            elif e.response.status_code == 401:
                logger.error("Authentication error. Check your API key.")
                logger.error(f"Using API key: {self.api_key[:5]}...{self.api_key[-5:] if len(self.api_key) > 10 else ''}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise
    
    def search_companies(self, query: str, items_per_page: int = 100, 
                        start_index: int = 0) -> Dict[str, Any]:
        """Search for companies by name or number.
        
        Args:
            query: The search query
            items_per_page: Number of results per page
            start_index: Starting index for pagination
            
        Returns:
            Search results as a dictionary
        """
        params = {
            "q": query,
            "items_per_page": items_per_page,
            "start_index": start_index
        }
        return self._make_request(COMPANY_SEARCH_URL, params)
    
    def get_company_profile(self, company_number: str) -> Dict[str, Any]:
        """Get detailed information about a company.
        
        Args:
            company_number: The company's registration number
            
        Returns:
            Company profile data as a dictionary
        """
        url = f"{COMPANY_PROFILE_URL}/{company_number}"
        return self._make_request(url)
    
    def get_company_officers(self, company_number: str, 
                           items_per_page: int = 100,
                           start_index: int = 0) -> Dict[str, Any]:
        """Get officers of a company.
        
        Args:
            company_number: The company's registration number
            items_per_page: Number of results per page
            start_index: Starting index for pagination
            
        Returns:
            Officers data as a dictionary
        """
        url = f"{OFFICERS_URL}/{company_number}/officers"
        params = {
            "items_per_page": items_per_page,
            "start_index": start_index
        }
        return self._make_request(url, params)
    
    def get_filing_history(self, company_number: str,
                          items_per_page: int = 100,
                          start_index: int = 0) -> Dict[str, Any]:
        """Get the filing history of a company.
        
        Args:
            company_number: The company's registration number
            items_per_page: Number of results per page
            start_index: Starting index for pagination
            
        Returns:
            Filing history data as a dictionary
        """
        url = f"{FILING_HISTORY_URL}/{company_number}/filing-history"
        params = {
            "items_per_page": items_per_page,
            "start_index": start_index
        }
        return self._make_request(url, params) 