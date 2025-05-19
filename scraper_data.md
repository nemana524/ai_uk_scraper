# Companies House Scraper: Configuration Guide

## Overview

This document provides a detailed configuration guide for the Companies House API scraper project. The scraper allows you to collect company information from the UK Companies House registry, including company profiles, officers, and filing history.

## Requirements

- Python 3.6+
- Companies House API key (see [API Key Setup](#api-key-setup))
- Dependencies listed in requirements.txt

## Installation

1. Clone the repository to your local machine
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## API Key Setup

### Obtaining an API Key

1. Register for an account on the [Companies House Developer Portal](https://developer.company-information.service.gov.uk/)
2. Create a new application to generate an API key
3. Note that there are two environments:
   - Live API: For production use
   - Sandbox API: For testing purposes

### Configuring Your API Key

There are three ways to provide your API key to the scraper:

1. **Environment variable (recommended)**:
   ```bash
   # For Windows
   set COMPANIES_HOUSE_API_KEY=your_api_key_here
   
   # For Linux/MacOS
   export COMPANIES_HOUSE_API_KEY=your_api_key_here
   ```

2. **Configuration file**:
   Update the `API_KEY` variable in `src/config.py`

3. **Command-line argument**:
   ```bash
   python main.py --api-key your_api_key_here --query "company name"
   ```

### API Environment Configuration

To specify which API environment to use:

1. **Environment variable**:
   ```bash
   # For Windows
   set COMPANIES_HOUSE_API_ENV=live  # or 'test' for sandbox
   
   # For Linux/MacOS
   export COMPANIES_HOUSE_API_ENV=live  # or 'test' for sandbox
   ```

2. **Command-line argument**:
   ```bash
   python main.py --env live --query "company name"
   ```

## Data Storage

All scraped data is stored in the `data` directory with the following structure:

```
data/
├── companies/           # Raw company profile data
├── officers/            # Company officers data
├── filings/             # Filing history data
├── company_profiles/    # Processed company profiles
└── company_officers/    # Processed officer information
```

## Usage Examples

### Search and Scrape Companies by Query

```bash
python main.py --query "tech london" --max-pages 5
```

This will search for companies matching "tech london" and retrieve up to 5 pages of results.

### Scrape a Specific Company

```bash
python main.py --company-number 00000006
```

This will scrape all available data for the company with registration number 00000006.

### Export Collected Data to CSV

```bash
python main.py --export
```

This will process all collected data and export it to CSV files in the data directory.

### Comprehensive Scraping of All Companies

```bash
python main.py --scrape-all --max-companies 1000
```

This will scrape data for up to 1000 companies. Omit `--max-companies` to scrape all available companies.

Resume scraping from a specific index:

```bash
python main.py --scrape-all --resume-from-index 5000
```

## Rate Limiting

The Companies House API has a rate limit of 600 requests per minute. The scraper implements automatic rate limiting to avoid hitting this limit. If the rate limit is exceeded, the scraper will pause for 60 seconds before continuing.

## Advanced Configuration Options

### Adjusting Rate Limits

You can modify the `MAX_REQUESTS_PER_MINUTE` setting in `src/config.py` to change the rate limiting behavior. The default is 600 requests per minute (the Companies House API limit).

### Debug Logging

Enable debug logging for more detailed information:

```bash
python main.py --query "tech" --debug
```

### Save Interval for Large Scrapes

When performing large scrapes, you can adjust how often the scraper saves its progress:

```bash
python main.py --scrape-all --save-interval 500
```

This will save progress after every 500 companies (default is 1000).

## Environment Variables Summary

| Variable | Description | Default |
|----------|-------------|---------|
| COMPANIES_HOUSE_API_KEY | Your Companies House API key | None |
| COMPANIES_HOUSE_API_ENV | API environment ('live' or 'test') | 'live' |

## Command-Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| --query | Search query for companies | None |
| --max-pages | Maximum number of pages to retrieve | 10 |
| --export | Export collected data to CSV | False |
| --company-number | Scrape a specific company by number | None |
| --api-key | API key for Companies House | From config/env |
| --debug | Enable debug logging | False |
| --scrape-all | Scrape all UK companies alphabetically | False |
| --max-companies | Maximum number of companies to scrape | None |
| --resume-from-index | Resume scraping from a specific index | 0 |
| --resume-from-company | Resume scraping from a specific company name | None |
| --save-interval | Save progress interval | 1000 |
| --env | API environment to use ('live' or 'test') | From env var |

## Troubleshooting

### API Key Validation Failure

If you encounter an error like "API key validation failed":

1. Verify your API key is correct
2. Ensure you're using the correct environment (live vs. test)
3. Check if the API key has IP address restrictions
4. For sandbox API keys, make sure to set `--env test` or `COMPANIES_HOUSE_API_ENV=test`

### HTTP 429 Errors

If you see "Rate limit exceeded" errors, the scraper will automatically pause, but you may want to:

1. Decrease your scraping speed by manually adding delays
2. Run the scraper during off-peak hours
3. Split large scraping jobs into smaller batches

## Development Notes

The scraper is designed to be resilient and handles pagination automatically. When scraping large amounts of data, it's recommended to use the `--save-interval` option to ensure progress is saved regularly. 