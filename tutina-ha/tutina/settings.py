import pydantic
import pydantic_settings


class Coordinates(pydantic.BaseModel):
    lon: float
    lat: float



class Settings(pydantic_settings.BaseSettings):
    owm_api_key: pydantic.SecretStr
    owm_coordinates: Coordinates
    homeassistant_api_url: pydantic.AnyHttpUrl
    homeassistant_api_token: pydantic.SecretStr

    class Config:
        env_file = ".env"


settings = Settings()
