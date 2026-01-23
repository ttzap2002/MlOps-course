import pandas as pd
import requests
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import ObjectStoragePath

BASE_PATH = ObjectStoragePath("s3://aws_default@weather-data/")

def get_data() -> dict:
    print("Fetching data from API")

    # New York temperature in 2025
    url = "https://archive-api.open-meteo.com/v1/archive?latitude=40.7143&longitude=-74.006&start_date=2025-01-01&end_date=2025-12-31&hourly=temperature_2m&timezone=auto"

    resp = requests.get(url)
    resp.raise_for_status()

    data = resp.json()
    data = {
        "time": data["hourly"]["time"],
        "temperature": data["hourly"]["temperature_2m"],
    }
    return data


def transform(data: dict) -> pd.DataFrame:
    df = pd.DataFrame(data)
    df["temperature"] = df["temperature"].clip(lower=-20, upper=50)
    return df


def save_data(df: pd.DataFrame, **kwargs) -> None:
    print("Saving the data")

    logical_date = kwargs["logical_date"]
    formatted_date = logical_date.strftime("YYYY-MM-DD")
    file_path = BASE_PATH / f"weather_{formatted_date}.csv"
    storage_options = {
        "client_kwargs": {
            "endpoint_url": "http://localstack:4566"
        }
    }
    BASE_PATH.mkdir(exist_ok=True)

    df.to_csv(
        file_path.as_uri(),
        index=False,
        storage_options=storage_options
    )


with DAG(dag_id="s3_integration"):
    get_data_op = PythonOperator(task_id="get_data", python_callable=get_data)
    transform_op = PythonOperator(
        task_id="transform", python_callable=transform, op_kwargs={"data": get_data_op.output},
    )
    load_op = PythonOperator(
        task_id="load", python_callable=save_data, op_kwargs={"df": transform_op.output}
    )

    get_data_op >> transform_op >> load_op
