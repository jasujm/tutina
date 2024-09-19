import json
import os
import typing

import pydantic
import pydantic_settings
import sqlalchemy


class Coordinates(pydantic.BaseModel):
    lon: float
    lat: float


class DatabaseUrl(pydantic.BaseModel):
    drivername: str
    username: str
    password: pydantic.SecretStr
    host: str
    database: str
    port: typing.Optional[int] = None
    query: typing.Optional[str] = None

    def to_url(self) -> sqlalchemy.engine.URL:
        kwargs = self.dict()
        kwargs["password"] = self.password.get_secret_value()
        return sqlalchemy.engine.URL.create(**kwargs)


class Settings(pydantic_settings.BaseSettings):
    database_url: typing.Union[DatabaseUrl, pydantic.SecretStr]
    owm_api_key: pydantic.SecretStr
    owm_coordinates: Coordinates
    homeassistant_api_url: pydantic.AnyHttpUrl
    homeassistant_api_token: pydantic.SecretStr

    def get_database_url(self) -> sqlalchemy.engine.URL:
        if isinstance(self.database_url, DatabaseUrl):
            return self.database_url.to_url()
        return sqlalchemy.engine.make_url(self.database_url.get_secret_value())

    class Config:
        env_file = ".env"


settings = Settings()
