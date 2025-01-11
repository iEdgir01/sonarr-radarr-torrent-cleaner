#!/bin/bash

# Function to log errors and continue (no exit)
log_error() {
    echo "ERROR: $1" | tee -a /app/logs/entrypoint.log
}

# Function to log info messages
log_info() {
    echo "INFO: $1" | tee -a /app/logs/entrypoint.log
}

# Function to log warnings
log_warning() {
    echo "WARNING: $1" | tee -a /app/logs/entrypoint.log
}

# Initialize an array to hold missing environment variables
missing_vars=()

# Check for required environment variables and optional defaults
check_env_vars() {
    [ -z "$RADARR_URL" ] && missing_vars+=("RADARR_URL")
    [ -z "$RADARR_API_KEY" ] && missing_vars+=("RADARR_API_KEY")
    [ -z "$PLEX_URL" ] && missing_vars+=("PLEX_URL")
    [ -z "$PLEX_TOKEN" ] && missing_vars+=("PLEX_TOKEN")

    # Optional config vars
    if [ -z "$API_TIMEOUT" ]; then
        API_TIMEOUT="600"  # Default to 600 if not set
    fi
    if [ -z "$STRIKE_COUNT" ]; then
        STRIKE_COUNT="5"  # Default to 5 if not set
    fi
}

# Validate integer variables
validate_integers() {
    if ! [[ "$API_TIMEOUT" =~ ^[0-9]+$ ]]; then
        log_warning "API_TIMEOUT must be an integer, but received: $API_TIMEOUT. Reverting to default 600."
        API_TIMEOUT="600"  # Default if invalid
    fi

    if ! [[ "$STRIKE_COUNT" =~ ^[0-9]+$ ]]; then
        log_warning "STRIKE_COUNT must be an integer, but received: $STRIKE_COUNT. Reverting to default 5."
        STRIKE_COUNT="5"  # Default if invalid
    fi
}

# Load configuration from config.yml if it exists
load_config_yml() {
    if [ -f /app/config/config.yml ]; then
        log_info "Loading configuration from config.yml"
        while IFS= read -r line || [ -n "$line" ]; do
            if [[ $line =~ ^[^#]*:[^#]*$ ]]; then
                varname=$(echo "$line" | cut -d ':' -f 1 | tr -d '[:space:]')
                varvalue=$(echo "$line" | cut -d ':' -f 2- | tr -d '[:space:]')

                # Validate and handle empty or invalid values
                if [ -z "$varvalue" ]; then
                    log_warning "Value for '$varname' is empty in config.yml. Skipping."
                    continue
                fi

                # Special validation for numeric values (e.g., API_TIMEOUT)
                case "$varname" in
                    api_timeout)
                        if ! [[ "$varvalue" =~ ^[0-9]+$ ]]; then
                            log_warning "Invalid value for '$varname' in config.yml: '$varvalue' is not a number. Skipping."
                            continue
                        fi
                        API_TIMEOUT="$varvalue"
                        log_info "Using API_TIMEOUT from config.yml: $API_TIMEOUT"
                        ;;
                    strike_count)
                        if ! [[ "$varvalue" =~ ^[0-9]+$ ]]; then
                            log_warning "Invalid value for '$varname' in config.yml: '$varvalue' is not a number. Skipping."
                            continue
                        fi
                        STRIKE_COUNT="$varvalue"
                        log_info "Using STRIKE_COUNT from config.yml: $STRIKE_COUNT"
                        ;;
                    *)
                        # If not API_TIMEOUT or STRIKE_COUNT, just set the variable
                        eval "$varname=\"$varvalue\""
                        log_info "Using $varname from config.yml: $varvalue"
                        ;;
                esac
            fi
        done < <(sed 's/\r//g' /app/config/config.yml)
    else
        log_info "config.yml not found. Proceeding with environment variables only."
    fi
}

# Ensure the /app/config directory exists
setup_config_directory() {
    if [ ! -d "/app/config" ]; then
        log_info "/app/config directory not found. Creating it."
        mkdir -p "/app/config"
        chmod -R 777 "/app/config"
    else
        log_info "/app/config directory exists."
    fi
}

# Update config.yml with environment variables
update_config_yml() {
    # Write to config.yml using environment variables
    envsubst < /app/config/config.template > /app/config/config.yml
    log_info "Environment variables have been written to config.yml"
}

# Ensure log directory exists and set permissions
setup_log_directory() {
    mkdir -p "/app/logs"
    chmod -R 777 "/app/logs"
}

# Main script execution
setup_config_directory
check_env_vars
load_config_yml

# Log and continue if any missing required environment variables are found
if [ ${#missing_vars[@]} -ne 0 ]; then
    log_warning "The following environment variables are missing: ${missing_vars[*]}"
fi

# Validate that API_TIMEOUT and STRIKE_COUNT are integers
validate_integers

# Write or update config.yml with environment variables
update_config_yml

setup_log_directory

# Execute the main application
exec "$@"