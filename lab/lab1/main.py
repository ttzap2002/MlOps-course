import os
import argparse
from dotenv import load_dotenv
from settings import Settings, ENVIRONMENTS
from yaml import safe_load


def export_envs(environment: str = "dev") -> None:
    if environment not in ENVIRONMENTS:
        raise ValueError("Unknown environment")

    load_dotenv(f".env.{environment}")
    if environment == "dev":
        os.environ["ENVIRONMENT"] = "dev"
    elif environment == "prod":
        os.environ["ENVIRONMENT"] = "prod"
    elif environment == "test":
        os.environ["ENVIRONMENT"] = "test"

    return


def load_secrets_from_file(file_path: str) -> None:
    try:
        with open(file_path, "r") as file:
            secrets = safe_load(file)

            for key, value in secrets.items():
                os.environ[key] = str(value)
    except FileNotFoundError:
        print(f"{file_path} not found")


if __name__ == "__main__":
    load_secrets_from_file("secrets.yaml")
    parser = argparse.ArgumentParser(
        description="Load environment variables from specified.env file."
    )
    parser.add_argument(
        "--environment",
        type=str,
        default="dev",
        help="The environment to load (dev, test, prod)",
    )
    args = parser.parse_args()
    print(args.environment)
    export_envs(args.environment)

    settings = Settings()

    print("APP_NAME: ", settings.APP_NAME)
    print("ENVIRONMENT: ", settings.ENVIRONMENT)
    print("API_KEY: ", settings.API_KEY)
    print("PASSWORD: ", settings.PASSWORD)
