#!/usr/bin/with-contenv bashio

export database_url=$(bashio::services mysql | jq '{
   drivername: "mysql",
   username: .username,
   password: .password,
   host: .host,
   port: .port,
   database: "tutina"
}')
export homeassistant_api_url="http://supervisor/core/api"
export homeassistant_api_token=$SUPERVISOR_TOKEN
export owm_api_key=$(bashio::config "owm_api_key")
export owm_coordinates=$(bashio::config "owm_coordinates")

/usr/src/tutina/venv/bin/python3 -m tutina.ha
