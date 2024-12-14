import asyncio
import yaml
import logging
import os
import requests
from datetime import datetime
from urllib.parse import urljoin
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Any

# Load configuration from config.yml
config_file = os.path.join(os.getcwd(), 'config', 'config.yml')
with open(config_file, 'r') as file:
    config = yaml.safe_load(file)

# Extract configuration values
RADARR_URL = config['radarr']['url']
RADARR_API_KEY = config['radarr']['api_key']
SONARR_URL = config['sonarr']['url']
SONARR_API_KEY = config['sonarr']['api_key']
API_TIMEOUT = config['api_timeout']
STRIKE_COUNT = config['strike_count']
LOG_DIR = config['log_directory']

# Initialize the strike count dictionary
strike_counts = {}

# Create the logs directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging
log_file = os.path.join(LOG_DIR, 'radarr-autodelete.log')
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s %(levelname)s[%(name)s]:%(message)s')

# Log script start
logging.info('Script started.')

# Function to make API requests
def make_api_request(url: str, api_key: str, params=None) -> Any:
    headers = {
        'X-Api-Key': api_key
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f'Error making API request to {url}: {e}')
        return None

# Function to make API delete requests
def make_api_request(url: str, api_key: str, params=None) -> Any:
    headers = {
        'X-Api-Key': api_key
    }
    try:
        response = requests.delete(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f'Error making API delete request to {url}: {e}')
        return None

# Function to count records
def count_records(api_url:str, api_key:str) -> int:
    the_url = f'{api_url}/queue'
    the_queue = make_api_request(the_url, api_key)
    if the_queue is not None and 'records' in the_queue:
        return the_queue['totalRecords']

# Function to remove stalled Sonarr downloads
async def remove_stalled_sonarr_downloads() -> None:
    logging.info('Checking Sonarr queue...')
    sonarr_url = f'{SONARR_API_URL}/queue'
    sonarr_queue = make_api_request(sonarr_url, SONARR_API_KEY, {'page': '1', 'pageSize': count_records(SONARR_API_URL, SONARR_API_KEY)})
    
    if sonarr_queue is None and 'records' not in sonarr_queue:
        logging.warning('Sonarr queue is None or missing "records" key')
        return 
    
    logging.info('Processing Sonarr queue...')
    for item in sonarr_queue['records']:
        if ('title' not in item) and ('status' not in item) and ('trackedDownloadStatus' not in item):
            logging.warning(f'Skipping item in Sonarr queue due to missing or invalid keys: {item}')
            continue
        logging.info(f'Checking the status of {item["title"]}')
        if item['status'] == 'warning' and item['errorMessage'] == 'The download is stalled with no connections':
            item_id = item['id']
            if item_id not in strike_counts:
                strike_counts[item_id] = 0
            strike_counts[item_id] += 1
            logging.info(f'Item {item["title"]} has {strike_counts[item_id]} strikes')
            if strike_counts[item_id] >= STRIKE_COUNT:
                logging.info(f'Researching stalled Sonarr download: {item["title"]}')
                make_api_delete(f'{SONARR_API_URL}/queue/{item_id}', SONARR_API_KEY, {'removeFromClient': 'true', 'blocklist': 'true'})
                del strike_counts[item_id]
        
    

# Function to remove stalled Radarr downloads
async def remove_stalled_radarr_downloads() -> None:
    logging.info('Checking Radarr queue...')
    radarr_url = f'{RADARR_API_URL}/queue'
    radarr_queue = make_api_request(radarr_url, RADARR_API_KEY, {'page': '1', 'pageSize': count_records(RADARR_API_URL, RADARR_API_KEY)})
    if radarr_queue is None and 'records' not in radarr_queue:
        logging.warning('Radarr queue is None or missing "records" key')
        return
    
    logging.info('Processing Radarr queue...')
    for item in radarr_queue['records']:
        if ('title' not in item) and ('status' not in item) and ('trackedDownloadStatus' not in item):
            logging.warning('Skipping item in Radarr queue due to missing or invalid keys')
            continue

        logging.info(f'Checking the status of {item["title"]}')
        if item['status'] == 'warning' and item['errorMessage'] == 'The download is stalled with no connections':
            item_id = item['id']
            if item_id not in strike_counts:
                strike_counts[item_id] = 0
            strike_counts[item_id] += 1
            logging.info(f'Item {item["title"]} has {strike_counts[item_id]} strikes')
            if strike_counts[item_id] >= STRIKE_COUNT:
                logging.info(f'Researching stalled Radarr download: {item["title"]}')
                make_api_delete(f'{RADARR_API_URL}/queue/{item_id}', RADARR_API_KEY, {'removeFromClient': 'true', 'blocklist': 'true'})
                del strike_counts[item_id]
        
    

# Main function
async def main() -> None:
    while True:
        logging.info('Running media-tools script')
        await remove_stalled_sonarr_downloads()
        await remove_stalled_radarr_downloads()
        logging.info(f'Finished running media-tools script. Sleeping for {API_TIMEOUT / 60} minutes.')
        await asyncio.sleep(API_TIMEOUT)

if __name__ == '__main__':
    asyncio.run(main())