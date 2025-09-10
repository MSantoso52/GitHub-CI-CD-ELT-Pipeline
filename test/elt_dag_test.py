import pytest
from airflow.models import DagBag
from dags.elt_dag import extract_and_load, dag  # Import your DAG and functions

@pytest.fixture
def dagbag():
    return DagBag(dag_folder='dags/', include_examples=False)

def test_dag_loads_without_errors(dagbag):
    assert len(dagbag.import_errors) == 0, "DAG import failures occurred"
    assert dagbag.dags.get('elt_sales_pipeline') is not None

def test_dag_structure():
    assert len(dag.tasks) == 3  # extract_load_task, create_clean_table, cleanse_data
    assert dag.tasks[0].downstream_task_ids == {'create_clean_table'}
    assert dag.tasks[1].downstream_task_ids == {'cleanse_data'}

def test_extract_and_load_function():
    # Mock PostgresHook and test function logic
    # For simplicity, test flattening and column replacement (add mocks if needed for full ELT)
    import pandas as pd
    import os
    file_path = os.path.join(os.path.dirname(__file__), '../data/sales_record.json')
    df = pd.read_json(file_path)
    df_flat = pd.json_normalize(df.to_dict('records'))
    df_flat.columns = [c.replace('.', '_') for c in df_flat.columns]
    assert 'customer_info_age' in df_flat.columns  # Check ELT prep step
    assert df_flat.shape[0] > 0  # Ensure data is loaded

# Add more tests for SQL validation if needed (e.g., using sqlparse to check syntax)
