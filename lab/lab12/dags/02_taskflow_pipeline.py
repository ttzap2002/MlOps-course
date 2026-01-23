import pandas as pd
import requests
from airflow import DAG
from airflow.sdk import dag, task
from airflow.providers.standard.operators.python import PythonOperator

@dag()
def weather_pipeline():
    @task
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

    @task
    def transform(data: dict) -> pd.DataFrame:
        df = pd.DataFrame(data)
        df["temperature"] = df["temperature"].clip(lower=-20, upper=50)
        return df

    @task
    def save_data(df: pd.DataFrame) -> None:
        print("Saving the data")
        df.to_csv("data.csv", index=False)

    raw_data = get_data()
    clean_data = transform(raw_data)
    save_data(clean_data)

weather_pipeline()