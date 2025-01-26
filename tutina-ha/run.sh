#!/usr/bin/with-contenv bashio

export tutina_homeassistant__api_url="http://supervisor/core/api"
export tutina_homeassistant__api_token=$SUPERVISOR_TOKEN
export tutina_owm__api_key=$(bashio::config "owm_api_key")
export tutina_owm__coordinates=$(bashio::config "owm_coordinates")
export tutina_tutina__base_url=$(bashio::config "tutina_base_url")
export tutina_tutina__token_secret=$(bashio::config "tutina_token_secret")

/usr/src/tutina/tutina-ha/.venv/bin/tutina ha
