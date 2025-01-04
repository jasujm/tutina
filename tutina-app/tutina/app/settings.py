import dotenv

dotenv.load_dotenv()

import typing

import pydantic
import pydantic_settings


class DatabaseSettings(pydantic.BaseModel):
    url: pydantic.SecretStr


class ModelSettings(pydantic.BaseModel):
    data_file: str | None = None
    model_file: str | None = None
    config: dict[str, typing.Any] = {}


class Settings(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(
        env_prefix="tutina_", extra="ignore", env_nested_delimiter="_"
    )

    database: DatabaseSettings
    model: ModelSettings = ModelSettings()
    token_secret: pydantic.SecretStr
