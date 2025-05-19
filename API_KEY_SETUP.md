# Companies House API Key Setup Guide

This guide will help you set up and troubleshoot your Companies House API key for use with this scraper.

## Getting an API Key

1. Register or log in to the [Companies House Developer Hub](https://developer.company-information.service.gov.uk/)
2. Go to "Your Applications" and click "Add an application"
3. Fill in the required information:
   - Application name: A descriptive name for your scraper
   - Description: Brief description of what you're using it for
   - Environment: Choose either "Live" or "Test" (see below)
   - JavaScript domains: Leave blank unless you're making requests from a browser
   - Restricted IPs: Optionally specify IP addresses that can use this key

## Live vs Test Environment

Companies House API has two separate environments, each requiring different API keys:

- **Live Environment**: 
  - Contains real company data
  - API base URL: `https://api.company-information.service.gov.uk`
  - Limited number of requests per day (rate limited)

- **Test/Sandbox Environment**:
  - Contains limited test data only
  - API base URL: `https://api-sandbox.company-information.service.gov.uk`
  - Good for testing your code without using up your rate limits

## Configuring the Scraper

There are several ways to configure your API key and environment:

### Method 1: Environment Variables (Recommended)

Create a `.env` file in the project root with:

```
COMPANIES_HOUSE_API_KEY=your-api-key-here
COMPANIES_HOUSE_API_ENV=live  # or "test" for sandbox environment
```

### Method 2: Command Line Arguments

Run the scraper with the API key and environment specified:

```
python main.py --api-key "bf9a5d39-d519-4de1-9c25-fa46ead75386" --env live --query "tech"
```

### Method 3: Direct Configuration

Edit `src/config.py` and update the `API_KEY` value (not recommended for security reasons).

## Troubleshooting API Key Issues

If you see an "Invalid Authorization" error:

1. **Check your API key**:
   - Ensure the key is copied correctly with no extra spaces
   - Verify the key is active in the Companies House Developer Portal

2. **Check environment matching**:
   - Make sure your API key environment matches the environment you're using
   - A "Live" API key must be used with the live API URL
   - A "Test" API key must be used with the sandbox API URL

3. **IP Restrictions**:
   - If you configured restricted IPs, make sure your current IP is on the allowed list
   - For local testing, you might need to add your current IP address

4. **Check API key format**:
   - The API key should be used as the username in HTTP Basic Authentication
   - The password should be empty
   - No need to do base64 encoding yourself - the library handles this

5. **Test with a simple curl command**:
   - For live environment:
     ```
     curl -v -u "your-api-key-here:" https://api.company-information.service.gov.uk/company/00000006
     ```
   - For test environment:
     ```
     curl -v -u "your-api-key-here:" https://api-sandbox.company-information.service.gov.uk/company/00000006
     ```

## Common Error Messages

1. **"Invalid Authorization header", "type":"ch:service"**:
   - Your API key is not being properly formatted for authentication
   - Make sure you're using the key as the username with a colon at the end
   - The environment (live/test) might not match your key type

2. **"401 Unauthorized"**:
   - Your API key is invalid or has expired
   - You're using a test key with the live API or vice versa

3. **"403 Forbidden"**:
   - Your IP address might not be on the allowed list if you configured IP restrictions

## Need Help?

If you continue to experience issues, visit the [Companies House Developer Forum](https://forum.companieshouse.gov.uk/) for additional assistance. 