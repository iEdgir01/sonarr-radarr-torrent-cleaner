# sonarr-radarr-torrent-cleaner

This is a fork of MattDGTL's project with some added functionality. Credit to the overall idea can go here: [MattDGTL's sonarr-radarr-queue-cleaner](https://github.com/MattDGTL/sonarr-radarr-queue-cleaner).

A simple Sonarr and Radarr script to clean out stalled downloads with a "strike" system to ensure the stalled downloads have been stalled for a while.

The number of strikes and the time between checks can be customized with envoironment variables in the `docker-compose.yml`.
- This logic is forked from Paey Moopy's additions: [PaeyMoopy's sonarr-radarr-queue-cleaner](https://github.com/PaeyMoopy/sonarr-radarr-queue-cleaner).

## My fork aims to achieve 3 main objectives:

### 1. Remove Python `|` usage within the script
This change ensures greater compatibility with older versions of Python, specifically for OpenMediaVault setups.

### 2. Update the CONFIG parsing URL and creation logic
I’ve updated the URL handling logic to my own, as referenced in [this project](https://github.com/iEdgir01/radarr-autodelete), because the existing `config.json` handling didnt want to work ## probably because I am dumb.

### 3. Remove the need to build a Docker image locally
Building Docker images locally on OpenMediaVault can be inconvenient since the OMV environment is web-based. you only need to add the provided `docker-compose.yml` file via the OMV Docker Compose extension or clone the docker-compose file locally and ``docker-compose up``. Check the logs to ensure it's working.

I have created [a dedicated Docker image](https://hub.docker.com/r/iedgir01/media_cleaner), which will allow you to use thge provided docker-compose file instead of building the image and hosting the codebase locally.

## `ENVIRONMENT_VARIABLES` Setup:
To configure the script add these ENVIROMENT_VARIABLES to the docker compose.

```bash
#basic config !!REQUIRED!!
RADARR_URL=http://radarr:port
RADARR_API_KEY=your-radarr-api-key
SONARR_URL="http://sonarr:port"
SONARR_API_KEY="your-sonarr-api-key"

# How often to check for stalled downloads, in seconds
API_TIMEOUT: 600

# How many strikes before removing the download
STRIKE_COUNT: 5
```
