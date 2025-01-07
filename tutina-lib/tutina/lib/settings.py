import dotenv

dotenv.load_dotenv()

import functools
import os
from pathlib import Path
from typing import Annotated, Any, ClassVar, Type

import pydantic
import pydantic_settings

_DEFAULT_CONFIG_FILE_PATHS = [
    Path.home() / ".config/tutina.toml",
    Path("/etc/tutina.toml"),
]

_DEFAULT_DATA_DIR_PATHS = [
    Path.home() / ".local/share",
    Path("/usr/local/share"),
    Path("/usr/share"),
]

_DEFAULT_DATA_FILENAME = "tutina/data.parquet"
_DEFAULT_MODEL_FILENAME = "tutina/model.keras"


def _get_config_file_paths():
    config_file_from_env = (v := os.getenv("TUTINA_CONFIG_FILE")) and Path(v)
    return (
        [config_file_from_env, *_DEFAULT_CONFIG_FILE_PATHS]
        if config_file_from_env
        else _DEFAULT_CONFIG_FILE_PATHS
    )


def _get_data_file_path(filename):
    for dir_path in _DEFAULT_DATA_DIR_PATHS:
        if dir_path.is_dir() and os.access(dir_path, os.R_OK | os.W_OK):
            return dir_path / filename
    return None


class DatabaseSettings(pydantic.BaseModel):
    url: pydantic.SecretStr


class ModelSettings(pydantic.BaseModel):
    data_file: Path | None = pydantic.Field(
        default_factory=functools.partial(_get_data_file_path, _DEFAULT_DATA_FILENAME)
    )
    model_file: Path | None = pydantic.Field(
        default_factory=functools.partial(_get_data_file_path, _DEFAULT_MODEL_FILENAME)
    )
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

    _toml_file_override: ClassVar[Path | str | None] = None

    @classmethod
    def set_config_file(cls, path: Path | str):
        cls._toml_file_override = path

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[pydantic_settings.BaseSettings],
        init_settings: pydantic_settings.PydanticBaseSettingsSource,
        env_settings: pydantic_settings.PydanticBaseSettingsSource,
        dotenv_settings: pydantic_settings.PydanticBaseSettingsSource,
        file_secret_settings: pydantic_settings.PydanticBaseSettingsSource,
    ):
        toml_settings = (
            pydantic_settings.TomlConfigSettingsSource(
                settings_cls, cls._toml_file_override
            )
            if cls._toml_file_override
            else pydantic_settings.TomlConfigSettingsSource(settings_cls)
        )
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            toml_settings,
        )
