"""
Tests for the CompaniesHouseClient class.
"""
import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys

# Add the parent directory to the path so we can import the src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api_client import CompaniesHouseClient


class TestCompaniesHouseClient(unittest.TestCase):
    """Test cases for the CompaniesHouseClient class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "test_api_key"
        self.client = CompaniesHouseClient(self.api_key)
    
    @patch('requests.Session.get')
    def test_search_companies(self, mock_get):
        """Test searching for companies."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [
                {"company_number": "12345678", "title": "Test Company"},
                {"company_number": "87654321", "title": "Another Company"}
            ],
            "items_per_page": 2,
            "total_results": 2
        }
        mock_response.headers = {'X-Ratelimit-Remain': '599'}
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Call the method
        result = self.client.search_companies("test")
        
        # Check the result
        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(result["items"][0]["company_number"], "12345678")
        self.assertEqual(result["items"][1]["company_number"], "87654321")
        
        # Check that the request was made correctly
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertIn("search/companies", args[0])
        self.assertEqual(kwargs["params"]["q"], "test")
    
    @patch('requests.Session.get')
    def test_get_company_profile(self, mock_get):
        """Test getting a company profile."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "company_number": "12345678",
            "company_name": "Test Company Ltd",
            "company_status": "active"
        }
        mock_response.headers = {'X-Ratelimit-Remain': '599'}
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Call the method
        result = self.client.get_company_profile("12345678")
        
        # Check the result
        self.assertEqual(result["company_number"], "12345678")
        self.assertEqual(result["company_name"], "Test Company Ltd")
        
        # Check that the request was made correctly
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertIn("company/12345678", args[0])
    
    @patch('requests.Session.get')
    def test_rate_limit_handling(self, mock_get):
        """Test handling of rate limits."""
        # First call hits rate limit
        mock_response_429 = MagicMock()
        mock_response_429.raise_for_status.side_effect = [
            requests.exceptions.HTTPError("Rate limit exceeded"),
            None
        ]
        mock_response_429.status_code = 429
        
        # Second call succeeds
        mock_response_ok = MagicMock()
        mock_response_ok.json.return_value = {"status": "ok"}
        mock_response_ok.headers = {'X-Ratelimit-Remain': '599'}
        mock_response_ok.status_code = 200
        
        # Set up mock to return the error first, then success
        mock_get.side_effect = [mock_response_429, mock_response_ok]
        
        # Patch sleep to avoid waiting during test
        with patch('time.sleep') as mock_sleep:
            # Call the method
            with self.assertRaises(requests.exceptions.HTTPError):
                self.client._make_request("https://api.example.com")
            
            # Verify sleep was called
            mock_sleep.assert_called_once()


if __name__ == '__main__':
    unittest.main() 