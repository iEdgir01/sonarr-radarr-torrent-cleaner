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
log_file = os.path.join(LOG_DIR, 'media_cleaner.log')
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s %(levelname)s[%(name)s]:%(message)s')

# Log script start
logging.info('Script started.')

# Configure Radarr API connection
API_EXTENSION = '/api/v3/'
RADARR_API_HOST = urljoin(RADARR_URL, API_EXTENSION)
logging.info(f'RADARR API URL: {RADARR_API_HOST}')

# Configure Sonarr API connection
API_EXTENSION = '/api/v3/'
SONARR_API_HOST = urljoin(SONARR_URL, API_EXTENSION)
logging.info(f'SONARR API URL: {SONARR_API_HOST}')

@retry(stop=stop_after_attempt(10), wait=wait_exponential(multiplier=1, min=4, max=60), 
       retry=retry_if_exception_type((requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError)))
def api_request(base_url: str, endpoint: str, method: str = "GET", api_key: str = "", extra_params: dict = None):
    extra_params = extra_params or {}
    params = {"apikey": api_key}
    params.update(extra_params)

    url = urljoin(base_url, endpoint)
    logging.debug(f"{method} request to {url} with params {params}")

    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params, timeout=API_TIMEOUT)
        elif method.upper() == "DELETE":
            response = requests.delete(url, params=params, timeout=API_TIMEOUT)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        return response.json() if method.upper() == "GET" else None

    except requests.exceptions.RequestException as e:
        logging.error(f"Error during {method} request to {url}: {e}")
        return None
    except ValueError as e:
        logging.error(f"Invalid HTTP method specified: {e}")
        return None
    
def count_records(base_url: str, api_key: str) -> int:
    endpoint = "queue"
    the_queue = api_request(base_url=base_url, endpoint=endpoint, method="GET", api_key=api_key)
    
    if the_queue and 'totalRecords' in the_queue:
        return the_queue['totalRecords']
    else:
        logging.warning(f"Failed to count records from {base_url}/queue.")
        return 0

# Function to remove stalled Sonarr downloads
async def remove_stalled_sonarr_downloads() -> None:
    logging.info('Checking Sonarr queue...')

    # Get total number of records in Sonarr's queue
    total_records = count_records(SONARR_API_HOST, SONARR_API_KEY)
    if total_records == 0:
        logging.info('No records in Sonarr queue.')
        return

    # Fetch the entire Sonarr queue
    sonarr_queue = api_request(
        base_url=SONARR_API_HOST,
        endpoint="queue",
        method="GET",
        api_key=SONARR_API_KEY,
        extra_params={'page': '1', 'pageSize': total_records}
    )

    if not sonarr_queue or 'records' not in sonarr_queue:
        logging.warning('Sonarr queue is None or missing "records" key.')
        return

    logging.info('Processing Sonarr queue...')
    for item in sonarr_queue['records']:
        if not all(key in item for key in ['title', 'status', 'trackedDownloadStatus']):
            logging.warning(f'Skipping item in Sonarr queue due to missing or invalid keys: {item}')
            continue

        logging.info(f'Checking the status of {item["title"]}')
        if item['status'] == 'warning' and item.get('errorMessage') == 'The download is stalled with no connections':
            item_id = item['id']
            if item_id not in strike_counts:
                strike_counts[item_id] = 0
            strike_counts[item_id] += 1
            logging.info(f'Item {item["title"]} has {strike_counts[item_id]} strikes.')

            if strike_counts[item_id] >= STRIKE_COUNT:
                logging.info(f'Removing stalled Sonarr download: {item["title"]}')
                api_request(
                    base_url=SONARR_API_HOST,
                    endpoint=f"queue/{item_id}",
                    method="DELETE",
                    api_key=SONARR_API_KEY,
                    extra_params={'removeFromClient': 'true', 'blocklist': 'true'}
                )
                del strike_counts[item_id]
      
# Function to remove stalled Radarr downloads
async def remove_stalled_radarr_downloads() -> None:
    logging.info('Checking Radarr queue...')

    # Get total number of records in Radarr's queue
    total_records = count_records(RADARR_API_HOST, RADARR_API_KEY)
    if total_records == 0:
        logging.info('No records in Radarr queue.')
        return

    # Fetch the entire Radarr queue
    radarr_queue = api_request(
        base_url=RADARR_API_HOST,
        endpoint="queue",
        method="GET",
        api_key=RADARR_API_KEY,
        extra_params={'page': '1', 'pageSize': total_records}
    )

    if not radarr_queue or 'records' not in radarr_queue:
        logging.warning('Radarr queue is None or missing "records" key.')
        return

    logging.info('Processing Radarr queue...')
    for item in radarr_queue['records']:
        if not all(key in item for key in ['title', 'status', 'trackedDownloadStatus']):
            logging.warning(f'Skipping item in Radarr queue due to missing or invalid keys: {item}')
            continue

        logging.info(f'Checking the status of {item["title"]}')
        if item['status'] == 'warning' and item.get('errorMessage') == 'The download is stalled with no connections':
            item_id = item['id']
            if item_id not in strike_counts:
                strike_counts[item_id] = 0
            strike_counts[item_id] += 1
            logging.info(f'Item {item["title"]} has {strike_counts[item_id]} strikes.')

            if strike_counts[item_id] >= STRIKE_COUNT:
                logging.info(f'Removing stalled Radarr download: {item["title"]}')
                api_request(
                    base_url=RADARR_API_HOST,
                    endpoint=f"queue/{item_id}",
                    method="DELETE",
                    api_key=RADARR_API_KEY,
                    extra_params={'removeFromClient': 'true', 'blocklist': 'true'}
                )
                del strike_counts[item_id]


# Main function
async def main() -> None:
    try:
        while True:
            logging.info('Starting media_cleaner.')
            
            # Handle stalled Sonarr downloads
            try:
                await remove_stalled_sonarr_downloads()
            except Exception as e:
                logging.error(f'Error while processing Sonarr downloads: {e}')
            
            # Handle stalled Radarr downloads
            try:
                await remove_stalled_radarr_downloads()
            except Exception as e:
                logging.error(f'Error while processing Radarr downloads: {e}')
            
            logging.info(f'Finished media_cleaner. Sleeping for {API_TIMEOUT / 60:.2f} minutes.')
            await asyncio.sleep(API_TIMEOUT)
    
    except asyncio.CancelledError:
        logging.info('Media-tools script execution was cancelled.')
    except Exception as e:
        logging.critical(f'Unexpected error in main execution loop: {e}')
    finally:
        logging.info('Exiting media-tools script.')

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('Script terminated by user.')
    except Exception as e:
        logging.critical(f'Fatal error during script execution: {e}')