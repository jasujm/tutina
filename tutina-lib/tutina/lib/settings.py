import dotenv

dotenv.load_dotenv()

import os
from pathlib import Path
from typing import Any, Type

import pydantic
import pydantic_settings

_DEFAULT_CONFIG_FILE_PATHS = [
    Path.home() / ".config/tutina.toml",
    Path("/etc/tutina.toml"),
]


def _get_config_file_paths():
    config_file_from_env = (v := os.getenv("TUTINA_CONFIG_FILE")) and Path(v)
    return (
        [config_file_from_env, *_DEFAULT_CONFIG_FILE_PATHS]
        if config_file_from_env
        else _DEFAULT_CONFIG_FILE_PATHS
    )


class DatabaseSettings(pydantic.BaseModel):
    url: pydantic.SecretStr


class ModelSettings(pydantic.BaseModel):
    data_file: str | None = None
    model_file: str | None = None
    config: dict[str, Any] = {}


class Settings(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(
        env_prefix="tutina_",
        extra="ignore",
        env_nested_delimiter="_",
        toml_file=_get_config_file_paths(),
    )

    database: DatabaseSettings
    model: ModelSettings = ModelSettings()
    token_secret: pydantic.SecretStr

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[pydantic_settings.BaseSettings],
        init_settings: pydantic_settings.PydanticBaseSettingsSource,
        env_settings: pydantic_settings.PydanticBaseSettingsSource,
        dotenv_settings: pydantic_settings.PydanticBaseSettingsSource,
        file_secret_settings: pydantic_settings.PydanticBaseSettingsSource,
    ):
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            pydantic_settings.TomlConfigSettingsSource(settings_cls),
        )
