# sonarr-radarr-torrent-cleaner
This is a fork of MattDGTLs project with some added functionality. Credit to the overall idea can go here: https://github.com/MattDGTL/sonarr-radarr-queue-cleaner

A simple Sonarr and Radarr script to clean out stalled downloads.

A "strike" system to ensure the stalled downloads have been stalled for a while.

The amount of strikes and amount of time between checks can be changed in the config file.
-this is forked from Paey Moopy's additions``https://github.com/PaeyMoopy/sonarr-radarr-queue-cleaner``

My fork aims to do 3 things.
```
1 : remove python ``|`` usage within the script as to allow more versatility with older python versions - this is specifically for OpenMediaVault compatability
```
```
2 : update the url parsing and creation logic to my own as refrenced here: ``https://github.com/iEdgir01/radarr-autodelete`` as I find the existing config.jason to not work correctly  # probably because I'm dumb.
```
```
3 : remove the dependancy to build the docker image locally on your system - this is a pain to do on OMV setups as most things are web based - including the docker-compose functionality. In this way you just need to add the provided docker-compose to the OMV docker-compose extension, edit a config volume mount, create your own config.yml somewhere and voila. It should work. - you can check the logs of course to confirm.
```

This setup still relies  on a config.yml file, I have provided an example which needs to be edited to your information.
your ``config.yml``,wherever it may be,  must be mounted under volumes in the docker-compose in order for the service to get your radarr /sonarr URL and API key.

I will also be creating a dedicated docker image so that you dont need to build the image locally, but instead can use a docker-compose file which i will add to the repo once I have made the above changes.
```link to docker image goes here once created```

config.yml particulars:
edit the config file and input your server information.
RADARR:
  URL: "http://radarr:port"
  API_KEY: "your-radarr-api-key"
SONARR:
  URL: "http://radarr:port"
  API_KEY: "your-radarr-api-key"
API_TIMEOUT = how often to check for stalled downloads in seconds.
STRIKE_COUNT = how many strikes before looking for a new download.

For example, if API_TIMEOUT = 600, and STRIKE_COUNT = 5, the system will check for stalled downloads every 10 minutes. If any item is stalled, it gets a strike. Once an item recieves 5 strikes it gets removed and searched.
So in this example, any item that has been stalled for 1 hour will get removed and searched.
