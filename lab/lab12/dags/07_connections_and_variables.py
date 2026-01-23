import datetime
import json
from airflow.sdk import dag, task
from airflow.models import Variable

# Pobieramy klucz API z Variables Airflow
# Robimy to w globalnym scope, aby przekazać do op_kwargs
TWELVE_KEY = Variable.get("TWELVEDATA_API_KEY", default_var="missing_key")


@dag(
    schedule=datetime.timedelta(minutes=5),  # Zmienione na 5 min, by nie spamować bazy
    start_date=datetime.datetime(2025, 1, 1),
    catchup=False,
    tags=["exercise_5"]
)
def connections_and_variables():
    @task.virtualenv(
        requirements=["twelvedata", "cloudpickle", "pendulum"],
        serializer="cloudpickle",
        op_kwargs={
            "api_key": TWELVE_KEY,
            "logical_date": "{{ logical_date }}"
        }
    )
    def get_data(api_key, logical_date) -> dict:
        from twelvedata import TDClient
        import pendulum

        td = TDClient(apikey=api_key)
        log_date_dt = pendulum.parse(logical_date)

        ts = td.exchange_rate(symbol="USD/EUR", date=log_date_dt.isoformat())
        data = ts.as_json()

        return data

    @task
    def save_data(data: dict, logical_date) -> None:
        import pendulum

        symbol = data['symbol']
        rate = data['rate']
        log_date_dt = pendulum.parse(logical_date)

        # Używamy ID połączenia zdefiniowanego w UI
        pg_hook = PostgresHook(postgres_conn_id="postgres_storage")
        pg_hook.insert_rows(
            table="exchange_rates",
            rows=[symbol, rate],
            target_fields=["symbol", "exchange_rate"],
        )

    raw_data = get_data()
    save_data(raw_data)


connections_and_variables()