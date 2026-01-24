import pandas as pd
import requests
from airflow import DAG
import datetime
import pendulum
from airflow.sdk import dag, task


@dag(
    schedule=datetime.timedelta(days=7),
    catchup=True,
    start_date=pendulum.datetime(2025, 1, 1, tz="America/New_York"),
    end_date=pendulum.datetime(2025, 2, 1, tz="America/New_York"),
    max_active_runs=1,
)
def open_meteo_weather_backfill():
    @task
    def get_data(**kwargs) -> dict:
        print("Fetching data from API")

        url = "https://archive-api.open-meteo.com/v1/archive"

        logical_date = kwargs["logical_date"]
        start_date = logical_date
        end_date = logical_date.add(days=6)

        params = {
            "latitude": 40.7143,
            "longitude": -74.006,
            "start_date": start_date.to_date_string(),
            "end_date": end_date.to_date_string(),
            "hourly": "temperature_2m",
            "timezone": "auto",
        }

        resp = requests.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    @task
    def transform_data(data: dict) -> pd.DataFrame:
        hourly_data = data["hourly"]
        df_hourly = pd.DataFrame({
            "timestamp": pd.to_datetime(hourly_data["time"]),
            "temperature": hourly_data["temperature_2m"]
        })
        df_hourly["date"] = df_hourly["timestamp"].dt.date
        df_daily = df_hourly.groupby("date")["temperature"].agg(["max", "min"]).reset_index()
        df_daily.columns = ["date", "temp_max", "temp_min"]

        return df_daily

    @task
    def save_data(df: pd.DataFrame) -> None:
        print("Saving the data")
        df.to_csv("ny_temperature.csv", mode="a" , index=False)

    ny_temperature = get_data()
    transformed_data = transform_data(data=ny_temperature)
    save_data = save_data(transformed_data)

open_meteo_weather_backfill()

