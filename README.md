# sonarr-radarr-torrent-cleaner

This is a fork of MattDGTL's project with some added functionality. Credit to the overall idea can go here: [MattDGTL's sonarr-radarr-queue-cleaner](https://github.com/MattDGTL/sonarr-radarr-queue-cleaner).

A simple Sonarr and Radarr script to clean out stalled downloads with a "strike" system to ensure the stalled downloads have been stalled for a while.

The number of strikes and the time between checks can be customized in the `config.yml` file.
- This logic is forked from Paey Moopy's additions: [PaeyMoopy's sonarr-radarr-queue-cleaner](https://github.com/PaeyMoopy/sonarr-radarr-queue-cleaner).

## My fork aims to achieve 3 main objectives:

### 1. Remove Python `|` usage within the script
This change ensures greater compatibility with older versions of Python, specifically for OpenMediaVault setups.

### 2. Update the URL parsing and creation logic
I’ve updated the URL handling logic to my own, as referenced in [this project](https://github.com/iEdgir01/radarr-autodelete), because the existing `config.json` handling didnt want to work ## probably because I am dumb.

### 3. Remove the need to build a Docker image locally
Building Docker images locally on OpenMediaVault can be inconvenient since the OMV environment is largely web-based, including the Docker Compose functionality. Instead, you only need to add the provided `docker-compose.yml` file via the OMV Docker Compose extension. Then, you can mount the `config.yml` file and start the service with ease. Check the logs to ensure it's working.

I will also be creating a dedicated Docker image, which will allow you to use a pre-built Docker Compose file instead of building the image locally. Once that is ready, I will provide the link to the image here:
``link to docker image``

## `config.yml` File Setup

To configure the system, edit the `config.yml` file with your server information.

```yaml
RADARR:
  URL: "http://radarr:port"
  API_KEY: "your-radarr-api-key"

SONARR:
  URL: "http://sonarr:port"
  API_KEY: "your-sonarr-api-key"

API_TIMEOUT: 600  # How often to check for stalled downloads, in seconds
STRIKE_COUNT: 5   # How many strikes before removing the download
```
