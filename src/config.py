"""
Configuration module for Companies House API scraper.
"""
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file if it exists
load_dotenv()

# API key handling
# 1. First, try to get from environment variable
# 2. If not found, use the default value provided in the text file
# 3. API key can be overridden at runtime via command line argument
API_KEY = os.getenv("COMPANIES_HOUSE_API_KEY")

# Set whether we're using a test/sandbox environment 
# Environment variable should be either "live" or "test"
API_ENV = os.getenv("COMPANIES_HOUSE_API_ENV", "live").lower()

# If API key wasn't found in environment, use the default value
if not API_KEY:
    # This is a placeholder - you should replace it with your actual API key
    # or better, set it via environment variable
    API_KEY = "YOUR_API_KEY_HERE"
    logger.info("Using API key from default config. For better security, set the COMPANIES_HOUSE_API_KEY environment variable.")
else:
    # Trim any whitespace that might have been included in the environment variable
    API_KEY = API_KEY.strip()
    logger.info("Using API key from environment variable.")

# API settings - choose the correct base URL based on environment
if API_ENV == "test":
    # Sandbox/test environment URL
    BASE_URL = "https://api-sandbox.company-information.service.gov.uk"
    logger.info("Using TEST/SANDBOX environment")
else:
    # Production/live environment URL
    BASE_URL = "https://api.company-information.service.gov.uk"
    logger.info("Using LIVE environment")

# Search endpoints
COMPANY_SEARCH_URL = f"{BASE_URL}/search/companies"
OFFICER_SEARCH_URL = f"{BASE_URL}/search/officers"
DISQUALIFIED_OFFICER_SEARCH_URL = f"{BASE_URL}/search/disqualified-officers"

# Company details endpoints
COMPANY_PROFILE_URL = f"{BASE_URL}/company"
OFFICERS_URL = f"{BASE_URL}/company"
FILING_HISTORY_URL = f"{BASE_URL}/company"

# Rate limiting settings
MAX_REQUESTS_PER_MINUTE = 600  # Companies House API limit

# File paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# A well-known company registration number that can be used for testing API access
TEST_COMPANY_NUMBER = "00000006"  # ROYAL MAIL GROUP PLC 