
from datetime import datetime, timedelta
import logging

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator

from vn_stock.tasks.etl_vndirect_ticker import VNDirectCrawlTicker
from vn_stock.tasks.etl_vndirect_price import VNDirectCrawlPrice
from vn_stock.tasks import config
from vn_stock.tasks.utils import Utils

logger = Utils.get_logger(file_path="./vn_stock.log")
crawl_ticker = VNDirectCrawlTicker(config.conn_string, logger)
exchanges = Utils.get_exchange(config.conn_string)

default_args = {
    'owner': 'vanducng',
    'start_date': datetime(2019, 1, 1),
    # 'end_date': datetime(2018, 11, 30),
    'depends_on_past': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'catchup': False,
    'email_on_retry': False
}

dag = DAG('sparkify_dag',



          max_active_runs=3
          )


def hello_world():
    logging.info("Hello World")


dag = DAG(
    "vn_stock.etl",
    default_args=default_args,
    description='Scrap data from stock website',
    # Run on 8am and 8pm when the exchage open and close
    schedule_interval="0 8,20 * * *",
    max_active_runs=10
)

start_operator = DummyOperator(task_id='begin_execution',  dag=dag)
end_operator = DummyOperator(task_id='end_execution',  dag=dag)

ticker_ingestion = PythonOperator(
    task_id="ticker_ingestion",
    # python_callable=crawl_ticker.execute_etl,
    python_callable=hello_world,
    dag=dag)

price_ingestion_list = []
for _, exc in exchanges.iterrows():
    price_ingestion_list.append(
        PythonOperator(
            task_id=exc["exchange"],
            python_callable=VNDirectCrawlPrice(config.conn_string).execute_etl,
            op_args=[exc["exchange"]],
            dag=dag
        )
    )

# price_ingestion = PythonOperator(
#     task_id="price_ingestion",
#     python_callable=crawl_price.execute_etl,
#     dag=dag)

# ticker_ingestion >> price_ingestion

start_operator >> ticker_ingestion >> [
    x for x in price_ingestion_list] >> end_operator
