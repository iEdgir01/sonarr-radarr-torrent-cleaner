#!/bin/bash

# Function to log errors and exit
log_error_and_exit() {
    echo "ERROR: $1" | tee -a /app/logs/entrypoint.log
    exit 1
}

# Function to log info messages
log_info() {
    echo "INFO: $1" | tee -a /app/logs/entrypoint.log
}

# Initialize an array to hold missing environment variables
missing_vars=()

# Check for required environment variables and set defaults for non-critical ones
check_env_vars() {
    [ -z "$RADARR_URL" ] && missing_vars+=("RADARR_URL")
    [ -z "$RADARR_API_KEY" ] && missing_vars+=("RADARR_API_KEY")
    [ -z "$SONARR_URL" ] && missing_vars+=("SONARR_URL")
    [ -z "$SONARR_API_KEY" ] && missing_vars+=("SONARR_API_KEY")
    API_TIMEOUT=${API_TIMEOUT:-600}
    STRIKE_COUNT=${STRIKE_COUNT:-5}
}

# Update config.yml with environment variables
update_config_yml() {
    envsubst < /app/config/config.template > /app/config/config.yml
    log_info "Environment variables have been written to config.yml"
}

# Ensure log directory exists and set permissions
setup_log_directory() {
    mkdir -p "/app/logs"
    chmod -R 777 "/app/logs"
}

# Main script execution
check_env_vars
update_config_yml

# Log and exit if any missing environment variables are found
if [ ${#missing_vars[@]} -ne 0 ]; then
    log_error_and_exit "The following environment variables are missing: ${missing_vars[*]}"
fi

setup_log_directory

# Execute the main application
exec "$@"