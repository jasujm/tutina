import dotenv

dotenv.load_dotenv()

import functools
import os
from pathlib import Path
from typing import Annotated, Any, ClassVar, Type

import pydantic
import pydantic_settings
import xdg_base_dirs as xbd

_DEFAULT_CONFIG_FILE_PATHS = [
    d / "tutina.toml"
    for d in [
        xbd.xdg_config_home(),
        *xbd.xdg_config_dirs(),
        Path("/etc"),
    ]
]

_DEFAULT_DATA_DIR_PATHS = [
    d / "tutina"
    for d in [
        xbd.xdg_data_home(),
        *xbd.xdg_data_dirs(),
    ]
]

_DEFAULT_DATA_FILENAME = "data.parquet"
_DEFAULT_MODEL_FILENAME = "model.keras"


def _get_config_file_paths():
    config_file_from_env = (v := os.getenv("TUTINA_CONFIG_FILE")) and Path(v)
    return (
        [config_file_from_env, *_DEFAULT_CONFIG_FILE_PATHS]
        if config_file_from_env
        else _DEFAULT_CONFIG_FILE_PATHS
    )


def _get_data_file_path_for_read(filename):
    for dir_path in _DEFAULT_DATA_DIR_PATHS:
        if dir_path.is_dir() and os.access(dir_path, os.R_OK):
            return dir_path / filename
    return None


def _get_data_file_path_for_write(filename):
    dir_path = _DEFAULT_DATA_DIR_PATHS[0]
    if not dir_path.is_dir():
        os.mkdir(dir_path, 0o700)
    return dir_path / filename


def _get_data_file_path(filename: str, write: bool):
    if write:
        return _get_data_file_path_for_write(filename)
    return _get_data_file_path_for_read(filename)


class TutinaSettings(pydantic.BaseModel):
    token_secret: pydantic.SecretStr
    base_url: pydantic.AnyHttpUrl = "http://localhost:8000"  # type: ignore


class DatabaseUrlParts(pydantic.BaseModel):
    drivername: str = "mysql+aiomysql"
    username: str | None = None
    password: pydantic.SecretStr | None = None
    host: str | None = None
    database: str | None = None
    port: int | None = None
    query: str | None = None

    def to_url(self):
        import sqlalchemy

        kwargs = self.dict()
        kwargs["password"] = self.password and self.password.get_secret_value()
        return sqlalchemy.engine.URL.create(**kwargs)


class DatabaseSettings(pydantic.BaseModel):
    url: pydantic.SecretStr | DatabaseUrlParts = DatabaseUrlParts()

    def get_url(self):
        import sqlalchemy

        if isinstance(self.url, DatabaseUrlParts):
            return self.url.to_url()
        return sqlalchemy.engine.make_url(self.url.get_secret_value())


class ModelSettings(pydantic.BaseModel):
    data_file: Path | None = None
    model_file: Path | None = None
    config: dict[str, Any] = {}

    def get_data_file_path(self, *, write: bool) -> Path | None:
        if self.data_file:
            return self.data_file
        return _get_data_file_path(_DEFAULT_DATA_FILENAME, write)

    def get_model_file_path(self, *, write: bool) -> Path | None:
        if self.model_file:
            return self.model_file
        return _get_data_file_path(_DEFAULT_MODEL_FILENAME, write)


class HomeAssistantSettings(pydantic.BaseModel):
    api_url: pydantic.AnyHttpUrl
    api_token: pydantic.SecretStr


class Coordinates(pydantic.BaseModel):
    lon: float
    lat: float


class OwmSettings(pydantic.BaseModel):
    api_key: pydantic.SecretStr
    coordinates: Coordinates


class Settings(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(
        env_prefix="tutina_",
        extra="ignore",
        env_nested_delimiter="__",
        env_ignore_empty=True,
        toml_file=_get_config_file_paths(),
    )

    tutina: TutinaSettings | None = None
    database: DatabaseSettings | None = None
    model: ModelSettings = ModelSettings()
    homeassistant: HomeAssistantSettings | None = None
    owm: OwmSettings | None = None
    logging: dict[str, Any] | None = None

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
