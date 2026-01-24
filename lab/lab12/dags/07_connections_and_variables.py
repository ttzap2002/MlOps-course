import datetime
from airflow.sdk import dag, task
from airflow.models import Variable
from airflow.providers.postgres.hooks.postgres import PostgresHook


@dag(
    schedule=datetime.timedelta(minutes=5),
    start_date=datetime.datetime(2025, 1, 1),
    catchup=False,
)
def connections_and_variables():
    @task.virtualenv(
        requirements=["twelvedata", "cloudpickle", "pendulum"],
        serializer="cloudpickle",
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
        symbol = data['symbol']
        rate = data['rate']

        pg_hook = PostgresHook(postgres_conn_id="postgres_data")
        pg_hook.insert_rows(
            table="exchange_rates",
            rows=[(symbol, rate)],
            target_fields=["symbol", "exchange_rate"],
        )

    api_key_val = Variable.get("TWELVEDATA_API_KEY")

    raw_data = get_data(
        api_key=api_key_val,
        logical_date="{{ logical_date }}"
    )

    save_data(raw_data)


connections_and_variables()