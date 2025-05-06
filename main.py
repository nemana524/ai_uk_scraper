"""
Main script for the Companies House scraper.

Example usage:
    - Search and scrape companies by query:
      python main.py --query "tech london"
    
    - Export collected data to CSV:
      python main.py --export
"""
import argparse
import logging
import sys
import os
import requests
import base64

from src.scraper import CompaniesHouseScraper
from src.config import API_KEY, TEST_COMPANY_NUMBER

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def validate_api_key(api_key):
    """Validate the API key by making a simple test request."""
    if not api_key:
        logger.error("No API key found. Set the COMPANIES_HOUSE_API_KEY environment variable or update config.py")
        return False
    
    # Ensure key is trimmed of any whitespace
    api_key = api_key.strip()
    
    logger.info("Validating API key...")
    
    # Check which environment to use for validation
    api_env = os.getenv("COMPANIES_HOUSE_API_ENV", "live").lower()
    base_url = "https://api-sandbox.company-information.service.gov.uk" if api_env == "test" else "https://api.company-information.service.gov.uk"
    test_url = f"{base_url}/company/{TEST_COMPANY_NUMBER}"
    
    try:
        # Use requests.auth.HTTPBasicAuth for authentication
        logger.debug(f"Sending request to {test_url}")
        logger.debug(f"Using API key: {api_key[:5]}...{api_key[-5:] if len(api_key) > 10 else ''}")
        
        response = requests.get(
            test_url,
            auth=requests.auth.HTTPBasicAuth(api_key, ''),
            headers={"Accept": "application/json"}
        )
        
        logger.debug(f"Validation response status: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("API key validation successful")
            return True
        elif response.status_code == 401:
            logger.error(f"API key invalid or unauthorized. Please check your API key.")
            if hasattr(response, 'text'):
                logger.error(f"Response content: {response.text}")
                
            # Common reasons and solutions
            logger.error("Common solutions to authentication issues:")
            logger.error("1. Verify the API key is correct and active in the Companies House Developer Portal")
            logger.error("2. Ensure you're using the correct environment (live vs. test/sandbox)")
            logger.error("3. For test/sandbox API keys, use the API_ENV=test environment variable")
            logger.error("4. For live API keys, use the API_ENV=live environment variable or don't set it")
            logger.error("5. Check if the API key has any IP restrictions and ensure your IP is allowed")
            
            return False
        else:
            logger.warning(f"API returned unexpected status code during validation: {response.status_code}")
            if hasattr(response, 'text'):
                logger.error(f"Response content: {response.text}")
            # Allow to continue even with a warning
            return True
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to validate API key: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Companies House API Scraper")
    
    # Add arguments
    parser.add_argument("--query", type=str, help="Search query for companies")
    parser.add_argument("--max-pages", type=int, default=10, 
                       help="Maximum number of pages to retrieve (default: 10)")
    parser.add_argument("--export", action="store_true", 
                       help="Export collected data to CSV")
    parser.add_argument("--company-number", type=str,
                       help="Scrape a specific company by number")
    parser.add_argument("--api-key", type=str, 
                       help="API key for Companies House (overrides config and env var)")
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug logging")
    
    # Add new argument for scraping all companies
    parser.add_argument("--scrape-all", action="store_true",
                       help="Scrape all UK companies alphabetically")
    parser.add_argument("--max-companies", type=int, default=None,
                       help="Maximum number of companies to scrape (default: no limit)")
    parser.add_argument("--resume-from-index", type=int, default=0,
                       help="Resume scraping from a specific index")
    parser.add_argument("--resume-from-company", type=str,
                       help="Resume scraping from a specific company name")
    parser.add_argument("--save-interval", type=int, default=1000,
                       help="Save progress after processing this many companies (default: 1000)")
    
    # Add argument to specify API environment
    parser.add_argument("--env", type=str, choices=["live", "test"], default=None,
                       help="API environment to use (live or test). Overrides environment variable.")
    
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Set API environment if specified
    if args.env:
        os.environ["COMPANIES_HOUSE_API_ENV"] = args.env
        logger.info(f"Using {args.env.upper()} environment specified via command line")
    
    # Use API key from command line if provided, otherwise use from config
    api_key = args.api_key
    if api_key:
        logger.info("Using API key from command line argument")
    else:
        api_key = API_KEY
        if os.getenv("COMPANIES_HOUSE_API_KEY"):
            logger.info("Using API key from environment variable")
        else:
            logger.info("Using API key from config file")
    
    logger.debug(f"API key being used: {api_key}")
    
    # Validate the API key before proceeding
    if not validate_api_key(api_key):
        logger.error("API key validation failed. Please check your API key and try again.")
        sys.exit(1)
    
    # Initialize scraper with the validated API key
    scraper = CompaniesHouseScraper(api_key)
    
    # Handle scrape all companies
    if args.scrape_all:
        try:
            logger.info("Starting comprehensive scrape of all UK companies")
            scraper.scrape_all_companies(
                max_companies=args.max_companies,
                resume_from_index=args.resume_from_index,
                resume_from_company=args.resume_from_company,
                save_interval=args.save_interval
            )
        except KeyboardInterrupt:
            logger.warning("Scraping process interrupted by user")
        except Exception as e:
            logger.error(f"Error during comprehensive scraping: {e}")
            sys.exit(1)
    
    # Handle search query
    if args.query:
        try:
            logger.info(f"Starting search for companies with query: {args.query}")
            results = scraper.scrape_companies_by_query(args.query, args.max_pages)
            logger.info(f"Completed scraping. Found {len(results)} companies.")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error occurred during scraping: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            sys.exit(1)
    
    # Handle specific company scraping
    if args.company_number:
        try:
            logger.info(f"Scraping specific company: {args.company_number}")
            company_data = scraper.get_all_company_data(args.company_number)
            scraper.save_company_data(company_data)
            logger.info(f"Completed scraping company {args.company_number}.")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error occurred while scraping company {args.company_number}: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            sys.exit(1)
    
    # Export data if requested
    if args.export:
        try:
            logger.info("Exporting data to CSV...")
            scraper.export_to_csv()
            logger.info("Export complete.")
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            sys.exit(1)
    
    # If no arguments, show help
    if not (args.query or args.export or args.company_number):
        parser.print_help()

if __name__ == "__main__":
    main() 