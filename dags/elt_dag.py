from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import pandas as pd
from datetime import datetime
from sqlalchemy.types import Text

default_args = {
    'owner': 'data_engineer',
    'start_date': datetime(2024, 1, 1),
}

dag = DAG('elt_sales_pipeline',
          default_args=default_args,
          schedule=None,
          catchup=False)

def extract_and_load():
    # Extract and flatten JSON
    df = pd.read_json('/opt/airflow/dags/sales_record.json')
    df_flat = pd.json_normalize(df.to_dict('records'))
    
    # Replace dots in column names
    df_flat.columns = [c.replace('.', '_') for c in df_flat.columns]
    
    # Load to staging table - ALL COLUMNS as text
    pg_hook = PostgresHook(postgres_conn_id='postgres_conn')
    engine = pg_hook.get_sqlalchemy_engine()
    
    # Create dtype dict for ALL columns as text
    dtype_dict = {col: Text for col in df_flat.columns}
    df_flat.to_sql('staging_sales', engine, if_exists='replace', index=False, dtype=dtype_dict)


extract_load_task = PythonOperator(
    task_id='extract_and_load',
    python_callable=extract_and_load,
    dag=dag
)


create_clean_table = SQLExecuteQueryOperator(
    task_id='create_clean_table',
    conn_id='postgres_conn',
    sql="""
    CREATE TABLE IF NOT EXISTS clean_sales (
        order_id TEXT,
        item_name TEXT,
        quantity INTEGER,
        price_per_unit NUMERIC,
        total_price NUMERIC,
        order_date TIMESTAMP,
        region TEXT,
        payment_method TEXT,
        customer_info_customer_id TEXT,
        customer_info_email TEXT,
        customer_info_age INTEGER,
        customer_info_address_street TEXT,
        customer_info_address_city TEXT,
        customer_info_address_zip TEXT,
        status TEXT,
        notes TEXT
    );
    """,
    dag=dag
)


cleanse_data = SQLExecuteQueryOperator(
    task_id='cleanse_data',
    conn_id='postgres_conn',
    sql="""
    TRUNCATE TABLE clean_sales;
    INSERT INTO clean_sales
    SELECT
        order_id,
        item_name,
        CASE
            WHEN TRIM(quantity) ~ E'^[0-9]+(\\\\[0-9]+)?$'
            AND TRIM(quantity) != ''
            THEN TRIM(quantity)::NUMERIC::INTEGER
            ELSE NULL
        END AS quantity,
        NULLIF(TRIM(price_per_unit), '')::NUMERIC,
        NULLIF(TRIM(REPLACE(total_price, '$', '')), '')::NUMERIC,
        NULLIF(TRIM(order_date), '')::TIMESTAMP,
        region,
        payment_method,
        customer_info_customer_id,
        customer_info_email,
        CASE
            WHEN TRIM(customer_info_age) ~ E'^[0-9]+(\\\\[0-9]+)?$'
            AND TRIM(customer_info_age) != ''
            THEN TRIM(customer_info_age)::NUMERIC::INTEGER
            ELSE NULL
        END AS customer_info_age,
        customer_info_address_street,
        customer_info_address_city,
        customer_info_address_zip,
        status,
        notes
    FROM staging_sales;
    """,
    dag=dag
)


extract_load_task >> create_clean_table >> cleanse_data
# EOF comment add for testing
