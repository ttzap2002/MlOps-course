import os
import argparse
from dotenv import load_dotenv
from settings import Settings, ENVIRONMENTS


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


if __name__ == "__main__":
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
