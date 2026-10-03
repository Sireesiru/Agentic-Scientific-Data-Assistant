from langchain.tools import tool

from tools.datafed_tool import DataFedTool
from tools.airflows_tool import (
    list_dags,
    trigger_dag,
    get_latest_run,
    list_recent_runs,
    list_tasks,
    get_task_status,
    get_task_logs,
    pause_dag,
    unpause_dag,
    show_dag,
)

df = DataFedTool()


# -------------------------------------------------
# DataFed
# -------------------------------------------------

@tool
def search_collection(collection_id: str):
    """
    Return all datasets in a DataFed collection.
    """
    return df.list_collection(collection_id)


@tool
def get_metadata(data_id: str):
    """
    Return metadata for a DataFed dataset.
    """
    return str(df.get_metadata(data_id))


# -------------------------------------------------
# Airflow
# -------------------------------------------------

@tool
def airflow_list_dags():
    """List all Airflow DAGs."""
    return list_dags()


@tool
def airflow_trigger_dag(dag_id: str):
    """Trigger an Airflow DAG."""
    return trigger_dag(dag_id)


@tool
def airflow_latest_run(dag_id: str):
    """Return the latest DAG run."""
    return get_latest_run(dag_id)


@tool
def airflow_recent_runs(dag_id: str):
    """Return recent DAG runs."""
    return list_recent_runs(dag_id)


@tool
def airflow_list_tasks(dag_id: str):
    """List tasks in a DAG."""
    return list_tasks(dag_id)


@tool
def airflow_task_status(dag_id: str, run_id: str):
    """Return task status for a DAG run."""
    return get_task_status(dag_id, run_id)


@tool
def airflow_task_logs(dag_id: str, run_id: str, task_id: str):
    """Return task logs."""
    return get_task_logs(dag_id, run_id, task_id)


@tool
def airflow_pause_dag(dag_id: str):
    """Pause an Airflow DAG."""
    return pause_dag(dag_id)


@tool
def airflow_unpause_dag(dag_id: str):
    """Unpause an Airflow DAG."""
    return unpause_dag(dag_id)


@tool
def airflow_show_dag(dag_id: str):
    """Return the DAG graph."""
    return show_dag(dag_id)