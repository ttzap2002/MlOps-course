import pendulum
import joblib
import polars as pl
import datetime

from sklearn.pipeline import make_pipeline

from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR

from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV

from airflow.sdk import dag, task, ObjectStoragePath
from airflow.providers.postgres.hooks.postgres import PostgresHook

BASE_S3 = ObjectStoragePath("s3://aws_default@nyc-taxi")
RAW_DATA_PATH = "s3://nyc-taxi/processed/*.parquet"
ML_DATA_DIR = BASE_S3 / "ml_data"
MODELS_DIR = BASE_S3 / "models"

S3_OPTS = {
    "aws_access_key_id": "test",
    "aws_secret_access_key": "test",
    "endpoint_url": "http://localstack:4566",
    "region_name": "us-east-1",
    "aws_allow_http": "true",
}

@dag(
    dag_id="02_train_taxi_models",
    schedule=None,
    start_date=pendulum.datetime(2025, 1, 1),
    catchup=False,
)
def train_taxi_model():
    @task()
    def prepare_data(input_path: str, output_path: ObjectStoragePath) -> dict:
        df = pl.read_parquet(input_path, storage_options=S3_OPTS)
        df = df.sort("date")
        max_date = df["date"].max()
        split_date = datetime.date(max_date.year, max_date.month, 1)

        train = df.filter(pl.col("date") < split_date)
        test = df.filter(pl.col("date") >= split_date)

        train_path = output_path / "train.parquet"
        test_path = output_path / "test.parquet"

        train.write_parquet(str(train_path), storage_options=S3_OPTS)
        test.write_parquet(str(test_path), storage_options=S3_OPTS)

        return {
            "train_path": str(train_path),
            "test_path": str(test_path),
        }

    @task()
    def train_model(models_output_dir: ObjectStoragePath, model_type: str, dataset_info: dict):
        train = pl.read_parquet(dataset_info["train_path"], storage_options=S3_OPTS)
        test = pl.read_parquet(dataset_info["test_path"], storage_options=S3_OPTS)

        X_train = train["date"].cast(pl.Int64).to_numpy().reshape(-1, 1)
        y_train = train["total_rides"].to_numpy()
        X_test = test["date"].cast(pl.Int64).to_numpy().reshape(-1, 1)
        y_test = test["total_rides"].to_numpy()

        match model_type:
            case "svm":
                pipeline = make_pipeline(StandardScaler(), SVR())
                param_grid = {"svr__C": [0.1, 1.0, 10.0], "svr__kernel": ["linear", "rbf"]}
                model = GridSearchCV(pipeline, param_grid, cv=3, scoring='neg_mean_absolute_error')

            case "ridge":
                model = make_pipeline(StandardScaler(), Ridge())

            case "random forest":
                rf = RandomForestRegressor(random_state=42, n_jobs=-1)
                param_grid = {"n_estimators": [50, 120], "max_depth": [5, 10, None]}
                model = GridSearchCV(rf, param_grid, cv=3, scoring='neg_mean_absolute_error')

            case _:
                raise ValueError(f"Unknown model: {model_type}")

        model.fit(X_train, y_train)

        predictions = model.predict(X_test)
        mae_score = mean_absolute_error(y_test, predictions)

        model_filename = f"candidate_{model_type}.pkl"
        model_path = models_output_dir / model_filename

        with model_path.open("wb") as file:
            joblib.dump(model, file)

        return {
            "model_name": model_type,
            "mae": mae_score,
            "model_path": str(model_path),
            "train_size": len(X_train),
        }

    @task
    def save_model_to_database(results: list[dict]):
        rows_to_insert = []
        for result in results:
            row = (
                result["model_name"],
                result["train_size"],
                result["mae"],
            )
            rows_to_insert.append(row)

        pg_hook = PostgresHook(postgres_conn_id="POSTGRES_DATA")
        pg_hook.insert_rows(
            table="model_metrics",
            rows=rows_to_insert,
            target_fields=["model_name", "train_size", "mae"]
        )

    @task
    def select_best_model(models_dir: ObjectStoragePath, results: list[dict]) -> None:
        best_run = min(results, key=lambda x: x["mae"])

        source_path = ObjectStoragePath(best_run["model_path"])
        target_path = models_dir / "best_model.pkl"
        source_path.rename(target_path)

        for path in models_dir.iterdir():
            if path.name == "best_model.pkl":
                continue

            if path.name.startswith("candidate_"):
                path.unlink()

    dataset_meta = prepare_data(
        input_path=RAW_DATA_PATH,
        output_path=ML_DATA_DIR
    )

    model_types = ["svm", "ridge", "random forest"]

    training_results = train_model.partial(
        dataset_info=dataset_meta,
        models_output_dir=MODELS_DIR
    ).expand(model_type=model_types)

    save_model_to_database(training_results)

    select_best_model(
        models_dir=MODELS_DIR,
        results=training_results
    )


train_taxi_model()
