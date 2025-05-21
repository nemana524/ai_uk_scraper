"""
Scraper module for extracting data from the Companies House API.
"""
import os
import json
import time
import pandas as pd
from typing import List, Dict, Any, Optional, Generator
from tqdm import tqdm
import logging
import requests

from src.api_client import CompaniesHouseClient
from src.config import DATA_DIR
try:
    from src.utils import monitor_resources, calculate_eta, get_company_count_estimate, print_resource_report
except ImportError:
    # If utils module is not yet imported, define fallback functions
    def monitor_resources(*args, **kwargs):
        return {"status": "utils module not available"}
    
    def calculate_eta(*args, **kwargs):
        return "Unknown"
    
    def get_company_count_estimate():
        return 4800000
    
    def print_resource_report(*args, **kwargs):
        pass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompaniesHouseScraper:
    """Scraper for extracting data from Companies House API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the scraper.
        
        Args:
            api_key: Optional API key for Companies House. If not provided, 
                    it will be taken from the config.
        """
        self.client = CompaniesHouseClient(api_key)
        self.companies_data_dir = os.path.join(DATA_DIR, "companies")
        self.officers_data_dir = os.path.join(DATA_DIR, "officers")
        self.filings_data_dir = os.path.join(DATA_DIR, "filings")
        self.company_profiles_dir = os.path.join(DATA_DIR, "company_profiles")
        self.company_officers_dir = os.path.join(DATA_DIR, "company_officers")
        
        # Create data directories if they don't exist
        for directory in [self.companies_data_dir, self.officers_data_dir, self.filings_data_dir, 
                         self.company_profiles_dir, self.company_officers_dir]:
            os.makedirs(directory, exist_ok=True)
        
        logger.info("Scraper initialized")
    
    def search_companies_paginated(self, query: str, 
                                max_pages: Optional[int] = None) -> Generator[Dict[str, Any], None, None]:
        """Search for companies and handle pagination.
        
        Args:
            query: The search query
            max_pages: Maximum number of pages to retrieve (None for all pages)
            
        Yields:
            Company data dictionaries
        """
        items_per_page = 100
        start_index = 0
        total_results = None
        current_page = 0
        
        while True:  # Continue until we break
            try:
                response = self.client.search_companies(query, items_per_page, start_index)
                
                if total_results is None:
                    total_results = response.get('total_results', 0)
                    logger.info(f"Found {total_results} results for query: {query}")
                
                items = response.get('items', [])
                if not items:
                    logger.info("No more items found, stopping pagination")
                    break
                    
                for item in items:
                    yield item
                
                start_index += items_per_page
                current_page += 1
                
                # Check if we've reached the maximum number of pages
                if max_pages is not None and current_page >= max_pages:
                    logger.info(f"Reached maximum number of pages ({max_pages})")
                    break
                
                # Check if we've reached the end of results
                if start_index >= total_results:
                    logger.info("Reached end of results")
                    break
                    
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error during pagination: {e}")
                raise
            except Exception as e:
                logger.error(f"Error during pagination: {e}")
                raise
    
    def get_all_company_data(self, company_number: str) -> Dict[str, Any]:
        """Get complete data for a company including profile, officers, and filing history.
        
        Args:
            company_number: The company's registration number
            
        Returns:
            Dictionary containing all company data
        """
        try:
            # Get company profile
            logger.info(f"Getting profile for company {company_number}")
            profile = self.client.get_company_profile(company_number)
            
            # Get officers
            logger.info(f"Getting officers for company {company_number}")
            officers_response = self.client.get_company_officers(company_number)
            officers = officers_response.get('items', [])
            
            # Get more officers if there are more pages
            total_officers = officers_response.get('total_results', 0)
            items_per_page = officers_response.get('items_per_page', 100)
            
            if total_officers > items_per_page:
                logger.info(f"Found {total_officers} officers, retrieving additional pages")
                for start_index in range(items_per_page, total_officers, items_per_page):
                    more_officers = self.client.get_company_officers(
                        company_number, items_per_page, start_index
                    ).get('items', [])
                    officers.extend(more_officers)
            
            # Get filing history
            logger.info(f"Getting filing history for company {company_number}")
            filing_response = self.client.get_filing_history(company_number)
            filings = filing_response.get('items', [])
            
            # Get more filings if there are more pages
            total_filings = filing_response.get('total_count', 0)
            
            if total_filings > items_per_page:
                logger.info(f"Found {total_filings} filings, retrieving additional pages")
                for start_index in range(items_per_page, total_filings, items_per_page):
                    more_filings = self.client.get_filing_history(
                        company_number, items_per_page, start_index
                    ).get('items', [])
                    filings.extend(more_filings)
            
            # Combine all data
            company_data = {
                'profile': profile,
                'officers': officers,
                'filing_history': filings
            }
            
            logger.info(f"Successfully retrieved all data for company {company_number}")
            return company_data
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error getting data for company {company_number}: {e}")
            if hasattr(e, 'response') and e.response.status_code == 404:
                logger.error(f"Company {company_number} not found")
            raise
        except Exception as e:
            logger.error(f"Error getting data for company {company_number}: {e}")
            return {
                'company_number': company_number,
                'error': str(e)
            }
    
    def save_company_data(self, company_data: Dict[str, Any]) -> None:
        """Save company data to appropriate files.
        
        Args:
            company_data: Dictionary containing company data
        """
        profile = company_data.get('profile', {})
        company_number = profile.get('company_number')
        
        if not company_number:
            logger.warning("No company number found, cannot save data")
            return
        
        try:
            # Save raw profile
            profile_path = os.path.join(self.companies_data_dir, f"{company_number}.json")
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2)
            
            # Save raw officers
            officers = company_data.get('officers', [])
            if officers:
                officers_path = os.path.join(self.officers_data_dir, f"{company_number}.json")
                with open(officers_path, 'w', encoding='utf-8') as f:
                    json.dump(officers, f, indent=2)
            
            # Save raw filing history
            filings = company_data.get('filing_history', [])
            if filings:
                filings_path = os.path.join(self.filings_data_dir, f"{company_number}.json")
                with open(filings_path, 'w', encoding='utf-8') as f:
                    json.dump(filings, f, indent=2)
            
            # Save structured company profile
            if profile:
                company_profile = {
                    'company_number': company_number,
                    'company_name': profile.get('company_name'),
                    'company_status': profile.get('company_status'),
                    'date_of_creation': profile.get('date_of_creation'),
                    'type': profile.get('type'),
                    'jurisdiction': profile.get('jurisdiction'),
                    'sic_codes': profile.get('sic_codes', []),
                    'has_insolvency_history': profile.get('has_insolvency_history'),
                    'has_charges': profile.get('has_charges'),
                    'has_super_secure_pscs': profile.get('has_super_secure_pscs'),
                    'can_file': profile.get('can_file'),
                    'registered_office_address': profile.get('registered_office_address', {}),
                    'annual_return': profile.get('annual_return', {}),
                    'accounts': profile.get('accounts', {}),
                    'etag': profile.get('etag')
                }
                
                company_profile_path = os.path.join(self.company_profiles_dir, f"{company_number}.json")
                with open(company_profile_path, 'w', encoding='utf-8') as f:
                    json.dump(company_profile, f, indent=2)
            
            # Save structured officers data
            if officers:
                structured_officers = []
                
                for officer in officers:
                    structured_officer = {
                        'name': officer.get('name'),
                        'officer_role': officer.get('officer_role'),
                        'appointed_on': officer.get('appointed_on'),
                        'resigned_on': officer.get('resigned_on'),
                        'nationality': officer.get('nationality'),
                        'country_of_residence': officer.get('country_of_residence'),
                        'occupation': officer.get('occupation'),
                        'address': officer.get('address', {}),
                        'date_of_birth': officer.get('date_of_birth', {}),
                        'links': officer.get('links', {}),
                        'former_names': officer.get('former_names', []),
                        'identification': officer.get('identification', {})
                    }
                    structured_officers.append(structured_officer)
                
                officers_structured_path = os.path.join(self.company_officers_dir, f"{company_number}.json")
                with open(officers_structured_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'company_number': company_number,
                        'company_name': profile.get('company_name'),
                        'total_officers': len(structured_officers),
                        'officers': structured_officers
                    }, f, indent=2)
            
            logger.info(f"Successfully saved all data for company {company_number}")
        
        except Exception as e:
            logger.error(f"Error saving data for company {company_number}: {e}")
            raise
    
    def scrape_companies_by_query(self, query: str, max_pages: int = 10, 
                                save_results: bool = True) -> List[Dict[str, Any]]:
        """Search and scrape companies based on a query.
        
        Args:
            query: The search query
            max_pages: Maximum number of pages to retrieve
            save_results: Whether to save results to disk
            
        Returns:
            List of company data dictionaries
        """
        logger.info(f"Searching for companies with query: {query}")
        companies = list(self.search_companies_paginated(query, max_pages))
        
        if not companies:
            logger.warning(f"No companies found for query: {query}")
            return []
        
        logger.info(f"Found {len(companies)} companies. Retrieving detailed information...")
        
        results = []
        for company in tqdm(companies, desc="Scraping companies"):
            company_number = company.get('company_number')
            if not company_number:
                logger.warning(f"Skipping company without company number: {company}")
                continue
                
            # Check if we already have data for this company
            profile_path = os.path.join(self.companies_data_dir, f"{company_number}.json")
            if os.path.exists(profile_path):
                logger.info(f"Company {company_number} already scraped, skipping")
                continue
                
            try:
                # Get all company data
                company_data = self.get_all_company_data(company_number)
                results.append(company_data)
                
                if save_results:
                    self.save_company_data(company_data)
                
                # Small delay to be extra nice to the API
                time.sleep(0.2)
                
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error for company {company_number}: {e}")
                if e.response.status_code == 429:  # Rate limit
                    logger.warning("Rate limit hit, sleeping for 60 seconds")
                    time.sleep(60)
                    # Try again
                    try:
                        company_data = self.get_all_company_data(company_number)
                        results.append(company_data)
                        
                        if save_results:
                            self.save_company_data(company_data)
                    except Exception as inner_e:
                        logger.error(f"Failed retry for company {company_number}: {inner_e}")
                continue
            except Exception as e:
                logger.error(f"Error processing company {company_number}: {e}")
                continue
        
        return results
    
    def scrape_all_companies(self, 
                           batch_size: int = 100, 
                           max_companies: Optional[int] = None, 
                           resume_from_index: int = 0,
                           resume_from_company: Optional[str] = None,
                           save_interval: int = 1000,
                           resource_check_interval: int = 100) -> None:
        """Scrape information for all UK companies from Companies House.
        
        This method will systematically retrieve all companies in alphabetical order,
        with the ability to resume from a specific point if the process is interrupted.
        
        Args:
            batch_size: Number of companies to retrieve per API call
            max_companies: Maximum number of companies to retrieve (None = all)
            resume_from_index: Index to resume from if process was interrupted
            resume_from_company: Company name or number to resume from
            save_interval: Number of companies to process before saving progress
            resource_check_interval: Number of companies to process before checking system resources
            
        Returns:
            None
        """
        # Create a progress tracking file
        progress_file = os.path.join(DATA_DIR, "scraping_progress.json")
        
        # Load progress if exists
        if os.path.exists(progress_file) and resume_from_index == 0 and resume_from_company is None:
            try:
                with open(progress_file, 'r') as f:
                    progress = json.load(f)
                    resume_from_index = progress.get('last_index', 0)
                    resume_from_company = progress.get('last_company', None)
                    logger.info(f"Resuming from index {resume_from_index}, company {resume_from_company}")
            except Exception as e:
                logger.error(f"Error loading progress file: {e}")
        
        # Determine the starting points for alphabetical scraping
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        all_starting_chars = list(alphabet)
        
        # If resuming, find the appropriate starting point
        start_idx = 0
        if resume_from_company and resume_from_company[0].upper() in alphabet:
            start_char = resume_from_company[0].upper()
            start_idx = alphabet.index(start_char)
        
        total_companies_processed = resume_from_index
        start_time = time.time()
        estimated_total = get_company_count_estimate()
        current_char = None
        
        # Initial resource check
        resource_report = monitor_resources(DATA_DIR)
        print_resource_report(resource_report)
        
        try:
            # Iterate through starting characters
            for idx in range(start_idx, len(all_starting_chars)):
                start_char = all_starting_chars[idx]
                current_char = start_char
                logger.info(f"Processing companies starting with '{start_char}'")
                
                # Start with this character as a search query
                current_index = 0
                
                while True:
                    try:
                        # Skip results until we reach resume point for the first character
                        should_skip = (idx == start_idx and 
                                     resume_from_company is not None and 
                                     current_index < resume_from_index)
                        
                        if should_skip:
                            # Skip to the resume point
                            current_index = resume_from_index
                        
                        # Search companies starting with this character
                        query = start_char
                        response = self.client.search_companies(
                            query, 
                            items_per_page=batch_size, 
                            start_index=current_index
                        )
                        
                        items = response.get('items', [])
                        if not items:
                            logger.info(f"No more companies starting with '{start_char}'")
                            break
                        
                        # Calculate and display progress
                        total_results = response.get('total_results', 0)
                        eta = calculate_eta(start_time, total_companies_processed, estimated_total)
                        logger.info(f"Progress: {total_companies_processed}/{estimated_total} companies processed (~{total_companies_processed/estimated_total*100:.2f}%). ETA: {eta}")
                        
                        # Process each company
                        for item in tqdm(items, desc=f"Processing '{start_char}' companies"):
                            company_number = item.get('company_number')
                            
                            # Skip if we haven't reached the company to resume from
                            if (resume_from_company is not None and
                                idx == start_idx and
                                item.get('title', '').lower() < resume_from_company.lower() and
                                total_companies_processed < resume_from_index):
                                logger.debug(f"Skipping {company_number}: {item.get('title')}")
                                continue
                            
                            # Reset resume_from_company after we've passed it
                            if (resume_from_company is not None and 
                                item.get('title', '').lower() >= resume_from_company.lower()):
                                resume_from_company = None
                            
                            # Process this company
                            try:
                                logger.info(f"Processing company {total_companies_processed + 1}: "
                                          f"{company_number} - {item.get('title')}")
                                
                                # Get detailed information
                                company_data = self.get_all_company_data(company_number)
                                
                                # Save the data
                                self.save_company_data(company_data)
                                
                                total_companies_processed += 1
                                
                                # Check system resources periodically
                                if total_companies_processed % resource_check_interval == 0:
                                    resource_report = monitor_resources(DATA_DIR)
                                    print_resource_report(resource_report)
                                    
                                    # If disk space is critically low (less than 5GB), pause and alert
                                    if resource_report['disk']['free_gb'] < 5:
                                        logger.critical(f"CRITICALLY LOW DISK SPACE: {resource_report['disk']['free_gb']:.2f} GB remaining")
                                        logger.critical("Scraping paused. Please free up disk space before continuing.")
                                        logger.critical(f"Current progress: {total_companies_processed} companies processed. Last company: {item.get('title')}")
                                        
                                        # Save progress
                                        with open(progress_file, 'w') as f:
                                            json.dump({
                                                'last_index': current_index + items.index(item) + 1,
                                                'last_company': item.get('title'),
                                                'total_processed': total_companies_processed,
                                                'current_char': start_char,
                                                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                                                'status': 'paused_low_disk'
                                            }, f, indent=2)
                                            
                                        # Wait for user to confirm continuation
                                        input("Press Enter to continue once disk space has been freed...")
                                
                                # Check if we've reached the maximum
                                if max_companies and total_companies_processed >= max_companies:
                                    logger.info(f"Reached maximum number of companies: {max_companies}")
                                    return
                                
                                # Save progress at intervals
                                if total_companies_processed % save_interval == 0:
                                    with open(progress_file, 'w') as f:
                                        json.dump({
                                            'last_index': current_index + items.index(item) + 1,
                                            'last_company': item.get('title'),
                                            'total_processed': total_companies_processed,
                                            'current_char': start_char,
                                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                                            'eta': eta
                                        }, f, indent=2)
                                    logger.info(f"Progress saved: {total_companies_processed} companies processed")
                                
                                # Throttle to avoid hitting rate limits
                                time.sleep(0.1)
                                
                            except requests.exceptions.HTTPError as e:
                                logger.error(f"HTTP error processing company {company_number}: {e}")
                                if e.response.status_code == 429:  # Rate limit error
                                    logger.warning("Rate limit reached. Sleeping for 60 seconds")
                                    time.sleep(60)
                                elif e.response.status_code == 404:
                                    logger.warning(f"Company {company_number} not found")
                                    continue
                                else:
                                    # Save progress before raising
                                    with open(progress_file, 'w') as f:
                                        json.dump({
                                            'last_index': current_index + items.index(item),
                                            'last_company': item.get('title'),
                                            'total_processed': total_companies_processed,
                                            'current_char': start_char,
                                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                                        }, f, indent=2)
                                    raise
                            except Exception as e:
                                logger.error(f"Error processing company {company_number}: {e}")
                                # Save progress before continuing
                                with open(progress_file, 'w') as f:
                                    json.dump({
                                        'last_index': current_index + items.index(item),
                                        'last_company': item.get('title'),
                                        'total_processed': total_companies_processed,
                                        'current_char': start_char,
                                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                                    }, f, indent=2)
                        
                        # Move to next page
                        current_index += batch_size
                        
                        # Check if we're at the end of results
                        if current_index >= total_results:
                            logger.info(f"Completed processing companies starting with '{start_char}'")
                            break
                        
                    except requests.exceptions.HTTPError as e:
                        logger.error(f"HTTP error during pagination: {e}")
                        if e.response.status_code == 429:  # Rate limit error
                            logger.warning("Rate limit reached. Sleeping for 60 seconds")
                            time.sleep(60)
                            continue
                        raise
                    except Exception as e:
                        logger.error(f"Error during pagination: {e}")
                        # Save progress before raising
                        with open(progress_file, 'w') as f:
                            json.dump({
                                'last_index': current_index,
                                'last_company': None,
                                'total_processed': total_companies_processed,
                                'current_char': start_char,
                                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                            }, f, indent=2)
                        raise
            
            # Final resource report
            resource_report = monitor_resources(DATA_DIR)
            print_resource_report(resource_report)
            
            # Calculate time taken
            end_time = time.time()
            duration = end_time - start_time
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            seconds = int(duration % 60)
            
            logger.info(f"Completed scraping all companies. Total processed: {total_companies_processed}")
            logger.info(f"Total time taken: {hours}h {minutes}m {seconds}s")
            
        except KeyboardInterrupt:
            logger.warning("Process interrupted by user")
            # Save progress before exiting
            with open(progress_file, 'w') as f:
                json.dump({
                    'last_index': current_index,
                    'last_company': resume_from_company,
                    'total_processed': total_companies_processed,
                    'current_char': current_char,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'interrupted'
                }, f, indent=2)
            logger.info(f"Progress saved: {total_companies_processed} companies processed")
            raise
        
        # Final progress save
        with open(progress_file, 'w') as f:
            json.dump({
                'last_index': 0,
                'last_company': None,
                'total_processed': total_companies_processed,
                'current_char': None,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'completed',
                'time_taken': f"{hours}h {minutes}m {seconds}s"
            }, f, indent=2)

    def export_to_csv(self, output_dir: str = DATA_DIR) -> None:
        """Export collected data to CSV files.
        
        Args:
            output_dir: Directory to save CSV files
        """
        try:
            # Export company profiles with enhanced SIC code information
            profiles = []
            for filename in os.listdir(self.company_profiles_dir):
                if filename.endswith('.json'):
                    with open(os.path.join(self.company_profiles_dir, filename), 'r') as f:
                        profile = json.load(f)
                        # Expand SIC codes into separate columns
                        sic_codes = profile.get('sic_codes', [])
                        profile['sic_code_1'] = sic_codes[0] if len(sic_codes) > 0 else None
                        profile['sic_code_2'] = sic_codes[1] if len(sic_codes) > 1 else None
                        profile['sic_code_3'] = sic_codes[2] if len(sic_codes) > 2 else None
                        profile['sic_code_4'] = sic_codes[3] if len(sic_codes) > 3 else None
                        profiles.append(profile)
            
            if profiles:
                df_profiles = pd.DataFrame(profiles)
                # Reorder columns to put SIC codes together
                columns = df_profiles.columns.tolist()
                sic_columns = [col for col in columns if col.startswith('sic_code_')]
                other_columns = [col for col in columns if not col.startswith('sic_code_')]
                df_profiles = df_profiles[other_columns + sic_columns]
                
                profiles_path = os.path.join(output_dir, 'company_profiles.csv')
                df_profiles.to_csv(profiles_path, index=False)
                logger.info(f"Exported {len(profiles)} company profiles to {profiles_path}")
            else:
                logger.warning("No company profiles to export")

            # Export officers data
            officers = []
            for filename in os.listdir(self.company_officers_dir):
                if filename.endswith('.json'):
                    with open(os.path.join(self.company_officers_dir, filename), 'r') as f:
                        officers.extend(json.load(f))
            
            if officers:
                df_officers = pd.DataFrame(officers)
                officers_path = os.path.join(output_dir, 'company_officers.csv')
                df_officers.to_csv(officers_path, index=False)
                logger.info(f"Exported {len(officers)} officer records to {officers_path}")
            else:
                logger.warning("No officer data to export")

            # Export filing history
            filings = []
            for filename in os.listdir(self.filings_data_dir):
                if filename.endswith('.json'):
                    with open(os.path.join(self.filings_data_dir, filename), 'r') as f:
                        filings.extend(json.load(f))
            
            if filings:
                df_filings = pd.DataFrame(filings)
                filings_path = os.path.join(output_dir, 'filing_history.csv')
                df_filings.to_csv(filings_path, index=False)
                logger.info(f"Exported {len(filings)} filing records to {filings_path}")
            else:
                logger.warning("No filing data to export")

        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            raise

    def search_companies_by_sic(self, sic_code: str, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for companies by SIC code.
        
        Args:
            sic_code: The SIC code to search for
            max_pages: Maximum number of pages to retrieve (None for all available pages)
            
        Returns:
            List of company data dictionaries
        """
        logger.info(f"Starting search for companies with SIC code: {sic_code}")
        
        companies = []
        total_processed = 0
        
        try:
            # First, get the total number of results
            initial_response = self.client.search_companies_by_sic(sic_code, 1, 0)
            total_results = initial_response.get('total_results', 0)
            
            if total_results == 0:
                logger.info("No companies found with this SIC code")
                return []
            
            logger.info(f"Found {total_results} total results for SIC code {sic_code}")
            
            # Calculate total items to process
            items_per_page = 100
            if max_pages is None:
                # Calculate total pages needed
                total_pages = (total_results + items_per_page - 1) // items_per_page
                items_to_process = total_results
                logger.info(f"Will process all {total_results} companies ({total_pages} pages)")
            else:
                items_to_process = min(total_results, max_pages * items_per_page)
                logger.info(f"Will process up to {items_to_process} companies (max {max_pages} pages)")
            
            # Create progress bar
            with tqdm(total=items_to_process, desc="Processing companies", unit="companies") as pbar:
                start_index = 0
                while total_processed < items_to_process:
                    try:
                        # Get a page of results
                        response = self.client.search_companies_by_sic(sic_code, items_per_page, start_index)
                        items = response.get('items', [])
                        
                        if not items:
                            logger.info("No more items found")
                            break
                        
                        # Process each company in the page
                        for company in items:
                            if total_processed >= items_to_process:
                                break
                                
                            total_processed += 1
                            pbar.update(1)
                            
                            company_number = company.get('company_number')
                            if company_number:
                                try:
                                    # Get the full company profile
                                    profile = self.client.get_company_profile(company_number)
                                    # Verify the company has the correct SIC code
                                    if sic_code in profile.get('sic_codes', []):
                                        companies.append(profile)
                                        # Update progress bar description with current count and percentage
                                        percentage = (len(companies) / total_results) * 100
                                        pbar.set_description(f"Found {len(companies)} matching companies ({percentage:.1f}% of total)")
                                except Exception as e:
                                    logger.error(f"Error getting profile for company {company_number}: {e}")
                                    continue
                            
                            # Add a small delay to avoid hitting rate limits
                            time.sleep(0.1)
                        
                        # Move to next page
                        start_index += items_per_page
                        
                    except Exception as e:
                        logger.error(f"Error processing page starting at index {start_index}: {e}")
                        break
            
            logger.info(f"Search completed:")
            logger.info(f"- Total companies processed: {total_processed}")
            logger.info(f"- Companies with matching SIC code: {len(companies)}")
            if max_pages is None:
                logger.info(f"- Coverage: {len(companies)}/{total_results} companies ({len(companies)/total_results*100:.1f}%)")
            
            return companies
            
        except Exception as e:
            logger.error(f"Error during SIC code search: {e}")
            logger.info(f"Search interrupted after processing {total_processed} companies")
            return companies 