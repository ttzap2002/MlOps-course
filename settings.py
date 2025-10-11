# settings.py
from pydantic_settings import BaseSettings
from pydantic import field_validator

ENVIRONMENTS = {"dev", "test", "prod"}


class Settings(BaseSettings):
    ENVIRONMENT: str
    APP_NAME: str
    API_KEY: str
    PASSWORD: str

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, value):
        # prepare validator that will check whether the value of ENVIRONMENT is in (dev, test, prod)
        if value not in ENVIRONMENTS:
            raise ValueError("ENVIRONMENT must be one of 'dev', 'test', or 'prod'")
        return value
