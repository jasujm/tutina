#!/usr/bin/with-contenv bashio

export tutina_homeassistant__api_url="http://supervisor/core/api"
export tutina_homeassistant__api_token=$SUPERVISOR_TOKEN
export tutina_owm__api_key=$(bashio::config "owm_api_key")
export tutina_owm__coordinates=$(bashio::config "owm_coordinates")
export tutina_tutina__base_url=$(bashio::config "tutina_base_url")
export tutina_tutina__token_secret=$(bashio::config "tutina_token_secret")
export tutina_logging='{
  "version": 1,
  "loggers": {
    "": {
      "handlers": ["default"],
      "level": "WARNING"
    },
    "tutina": {
      "handlers": ["default"],
      "level": "INFO",
      "propagate": false
    }
  },
  "handlers": {
    "default": {
      "level": "INFO",
      "class": "logging.StreamHandler",
      "formatter": "default"
    }
  },
  "formatters": {
    "default": {
      "format": "[%(asctime)s] %(levelname)-8s: %(name)s %(message)s"
    }
  }
}'

/usr/src/tutina/tutina-ha/.venv/bin/tutina ha
