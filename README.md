# UK Companies Scraper

A Python application that uses the Companies House API to scrape information about UK companies.

## Features

- Search for UK companies by name, keyword, or other criteria
- Retrieve detailed company profiles, officers, and filing history
- Automatically handle pagination for large result sets
- Save data in JSON format for easy processing
- Export data to CSV files for analysis

## Installation

1. Clone this repository:
```
git clone <repository-url>
cd scraper_project
```

2. Install the required dependencies:
```
pip install -r requirements.txt
```

3. Configure your API key:
   - **Option 1 (Recommended)**: Create a `.env` file in the project root and add your API key:
     ```
     COMPANIES_HOUSE_API_KEY=your-api-key-here
     COMPANIES_HOUSE_API_ENV=live  # or "test" for sandbox environment
     ```
   - **Option 2**: Set it as an environment variable:
     ```
     # Windows
     set COMPANIES_HOUSE_API_KEY=your-api-key-here
     set COMPANIES_HOUSE_API_ENV=live  # or "test" for sandbox environment
     
     # Linux/Mac
     export COMPANIES_HOUSE_API_KEY=your-api-key-here
     export COMPANIES_HOUSE_API_ENV=live  # or "test" for sandbox environment
     ```
   - **Option 3**: Pass it directly when running the script:
     ```
     python main.py --api-key "your-api-key-here" --env live --query "tech"
     ```
   - **Option 4**: Update the default API key in `src/config.py` (not recommended)

> **Note**: You can get an API key by registering at the [Companies House Developer Hub](https://developer.company-information.service.gov.uk/).
> The free tier allows 500 requests per month, which is sufficient for small-scale scraping.
> For detailed setup instructions and troubleshooting, see the [API Key Setup Guide](API_KEY_SETUP.md).

## Troubleshooting API Authentication

If you encounter a `401 Unauthorized` error, try these steps:

1. Verify your API key is correct:
   - Log in to the [Companies House Developer Portal](https://developer.company-information.service.gov.uk/)
   - Check that your key is active and has the necessary permissions
   - Ensure you're using the correct environment (live vs. test)
   - Generate a new key if needed

2. Test your API key manually:
   ```
   # For live environment
   curl -u your-api-key-here: https://api.company-information.service.gov.uk/company/00000006
   
   # For test environment
   curl -u your-api-key-here: https://api-sandbox.company-information.service.gov.uk/company/00000006
   ```
   
3. Check that your API key is being properly set in the application

4. For more detailed troubleshooting, refer to the [API Key Setup Guide](API_KEY_SETUP.md)

## Usage

### Searching for companies

To search and scrape companies based on a query:

```
python main.py --query "tech london" --max-pages 5
```

### Getting information for a specific company

To get detailed information about a specific company by number:

```
python main.py --company-number "12345678"
```

### Exporting data to CSV

After scraping data, you can export it to CSV files for further analysis:

```
python main.py --export
```

This will generate the following CSV files in the `data` directory:
- `companies.csv`: Basic information about each company
- `officers.csv`: Information about company officers
- `filings.csv`: Company filing history

### Comprehensive Scraping of All UK Companies

The scraper now supports a comprehensive mode to retrieve information about all UK companies:

```
python main.py --scrape-all
```

This will:
1. Systematically gather all UK companies alphabetically
2. Save data for each company in JSON format
3. Track progress and allow resumption if interrupted
4. Monitor system resources during execution

#### Advanced Options for Comprehensive Scraping

```
python main.py --scrape-all --max-companies 1000 --save-interval 100
```

- `--max-companies`: Limit the total number of companies to scrape (useful for testing)
- `--resume-from-index`: Resume from a specific index if previously interrupted
- `--resume-from-company`: Resume from a specific company name
- `--save-interval`: How often to save progress (number of companies)

#### Resource Monitoring

During comprehensive scraping, the system will:
- Monitor available disk space
- Track memory and CPU usage
- Automatically pause if disk space becomes critically low
- Provide estimated completion time

> **Warning**: Scraping all UK companies (~4.8 million) will:
> - Require significant disk space (estimated 50-100GB for complete data)
> - Take several days to weeks depending on your internet connection
> - Use a substantial portion of your API request allocation

## Project Structure

- `src/`: Source code
  - `config.py`: Configuration settings
  - `api_client.py`: Client for the Companies House API
  - `scraper.py`: Main scraper implementation
- `data/`: Stored data
  - `companies/`: JSON files with company profiles
  - `officers/`: JSON files with company officers
  - `filings/`: JSON files with filing history
- `tests/`: Test files
- `main.py`: Command-line interface

## API Documentation

For more information about the Companies House API, see:
- [Companies House API Documentation](https://developer.company-information.service.gov.uk/) 