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
        
        # Create data directories if they don't exist
        for directory in [self.companies_data_dir, self.officers_data_dir, self.filings_data_dir]:
            os.makedirs(directory, exist_ok=True)
        
        logger.info("Scraper initialized")
    
    def search_companies_paginated(self, query: str, 
                                max_pages: int = 10) -> Generator[Dict[str, Any], None, None]:
        """Search for companies and handle pagination.
        
        Args:
            query: The search query
            max_pages: Maximum number of pages to retrieve
            
        Yields:
            Company data dictionaries
        """
        items_per_page = 100
        start_index = 0
        total_results = None
        current_page = 0
        
        while current_page < max_pages:
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
            # Save profile
            profile_path = os.path.join(self.companies_data_dir, f"{company_number}.json")
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2)
            
            # Save officers
            officers = company_data.get('officers', [])
            if officers:
                officers_path = os.path.join(self.officers_data_dir, f"{company_number}.json")
                with open(officers_path, 'w', encoding='utf-8') as f:
                    json.dump(officers, f, indent=2)
            
            # Save filing history
            filings = company_data.get('filing_history', [])
            if filings:
                filings_path = os.path.join(self.filings_data_dir, f"{company_number}.json")
                with open(filings_path, 'w', encoding='utf-8') as f:
                    json.dump(filings, f, indent=2)
                    
            logger.info(f"Successfully saved data for company {company_number}")
            
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
        """Export collected data to CSV files for analysis.
        
        Args:
            output_dir: Directory to save CSV files
        """
        # Export companies data
        companies = []
        for filename in os.listdir(self.companies_data_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(self.companies_data_dir, filename), 'r', encoding='utf-8') as f:
                        company = json.load(f)
                        companies.append({
                            'company_number': company.get('company_number'),
                            'company_name': company.get('company_name'),
                            'company_status': company.get('company_status'),
                            'date_of_creation': company.get('date_of_creation'),
                            'sic_codes': ', '.join(company.get('sic_codes', [])),
                            'registered_office_address': json.dumps(company.get('registered_office_address', {})),
                            'has_insolvency_history': company.get('has_insolvency_history'),
                            'has_charges': company.get('has_charges'),
                            'jurisdiction': company.get('jurisdiction'),
                            'last_updated': company.get('last_full_members_list_date')
                        })
                except Exception as e:
                    logger.error(f"Error processing company file {filename}: {e}")
                    continue
        
        if companies:
            df_companies = pd.DataFrame(companies)
            companies_csv_path = os.path.join(output_dir, 'companies.csv')
            df_companies.to_csv(companies_csv_path, index=False)
            logger.info(f"Exported {len(companies)} companies to {companies_csv_path}")
        else:
            logger.warning("No company data to export")
        
        # Export officers data
        officers = []
        for filename in os.listdir(self.officers_data_dir):
            if filename.endswith('.json'):
                try:
                    company_number = filename.replace('.json', '')
                    with open(os.path.join(self.officers_data_dir, filename), 'r', encoding='utf-8') as f:
                        officers_data = json.load(f)
                        for officer in officers_data:
                            officers.append({
                                'company_number': company_number,
                                'name': officer.get('name'),
                                'officer_role': officer.get('officer_role'),
                                'appointed_on': officer.get('appointed_on'),
                                'resigned_on': officer.get('resigned_on'),
                                'nationality': officer.get('nationality'),
                                'country_of_residence': officer.get('country_of_residence'),
                                'occupation': officer.get('occupation'),
                                'address': json.dumps(officer.get('address', {})),
                                'date_of_birth': json.dumps(officer.get('date_of_birth', {}))
                            })
                except Exception as e:
                    logger.error(f"Error processing officers file {filename}: {e}")
                    continue
        
        if officers:
            df_officers = pd.DataFrame(officers)
            officers_csv_path = os.path.join(output_dir, 'officers.csv')
            df_officers.to_csv(officers_csv_path, index=False)
            logger.info(f"Exported {len(officers)} officers to {officers_csv_path}")
        else:
            logger.warning("No officer data to export")
        
        # Export filings data
        filings = []
        for filename in os.listdir(self.filings_data_dir):
            if filename.endswith('.json'):
                try:
                    company_number = filename.replace('.json', '')
                    with open(os.path.join(self.filings_data_dir, filename), 'r', encoding='utf-8') as f:
                        filings_data = json.load(f)
                        for filing in filings_data:
                            filings.append({
                                'company_number': company_number,
                                'filing_type': filing.get('type'),
                                'description': filing.get('description'),
                                'date': filing.get('date'),
                                'category': filing.get('category'),
                                'subcategory': filing.get('subcategory'),
                                'barcode': filing.get('barcode'),
                                'transaction_id': filing.get('transaction_id')
                            })
                except Exception as e:
                    logger.error(f"Error processing filings file {filename}: {e}")
                    continue
        
        if filings:
            df_filings = pd.DataFrame(filings)
            filings_csv_path = os.path.join(output_dir, 'filings.csv')
            df_filings.to_csv(filings_csv_path, index=False)
            logger.info(f"Exported {len(filings)} filings to {filings_csv_path}")
        else:
            logger.warning("No filing data to export") 