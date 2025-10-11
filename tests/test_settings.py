from settings import Settings


def test_settings() -> None:
    settings = Settings()

    assert settings.ENVIRONMENT == "test"
    assert settings.APP_NAME == "MlOps"
    assert settings.API_KEY == "fake key"
    assert settings.PASSWORD == "fake password"
