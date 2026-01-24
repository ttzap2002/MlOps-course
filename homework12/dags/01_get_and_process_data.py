import pendulum
from airflow.decorators import dag, task
from airflow.sdk import ObjectStoragePath
import polars as pl
import os
import boto3

BASE_S3 = ObjectStoragePath("s3://aws_default@nyc-taxi")

@dag(
    dag_id="01_process_taxi_data",
    schedule="@monthly",
    catchup=True,
    start_date=pendulum.datetime(2025, 1, 1),
    end_date=pendulum.datetime(2025, 6, 1),
    max_active_runs=6,
)
def process_taxi_data():
    @task()
    def get_taxi_data(*, logical_date: pendulum.datetime, base_path: ObjectStoragePath) -> ObjectStoragePath:
        print("get taxi data")
        s3_opts = {
            "aws_access_key_id": "test",
            "aws_secret_access_key": "test",
            "endpoint_url": "http://localstack:4566",
            "region_name": "us-east-1",
            "aws_allow_http": "true",
        }

        date = logical_date.format("YYYY-MM")
        file_name = f"yellow_tripdata_{date}.parquet"
        url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/{file_name}"
        target_path = base_path / file_name
        df = pl.read_parquet(url)
        df.write_parquet(str(target_path), storage_options=s3_opts)

        return target_path

    @task()
    def process_data(data_path: ObjectStoragePath, processed_base_path: ObjectStoragePath) -> ObjectStoragePath:
        print("process taxi data with polars")
        s3_opts = {
            "aws_access_key_id": "test",
            "aws_secret_access_key": "test",
            "endpoint_url": "http://localstack:4566",
            "region_name": "us-east-1",
            "aws_allow_http": "true",
        }

        df = pl.scan_parquet(str(data_path), storage_options=s3_opts)

        df_daily = (
            df.group_by(pl.col("tpep_pickup_datetime").dt.date().alias("date"))
            .agg(pl.len().alias("total_rides"))
            .sort("date")
            .collect()
        )

        output_name = f"processed_{data_path.name}"
        target_path = processed_base_path / output_name
        df_daily.write_parquet(str(target_path), storage_options=s3_opts)

        return target_path

    data_file = get_taxi_data(
        base_path=BASE_S3 / "raw"
    )

    processed_file = process_data(
        data_path=data_file,
        processed_base_path=BASE_S3 / "processed"
    )

process_taxi_data()