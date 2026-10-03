from pathlib import Path
import subprocess
import os

#print("Python in tool:", os.sys.executable)
#print("AIRFLOW_HOME in tool:", os.environ.get("AIRFLOW_HOME"))


AIRFLOW_CMD = "/home/cloud/microflow_server/bin/airflow"
LOG_ROOT = Path("/home/cloud/airflow_home/logs")


def _run_airflow_command(command):
    # Create a clean environment for Airflow
    env = os.environ.copy()

    # Remove virtual environment variables
    env.pop("VIRTUAL_ENV", None)
    env.pop("PYTHONHOME", None)

    # Make sure Airflow's Python is first on PATH
    env["PATH"] = "/home/cloud/microflow_server/bin:" + env.get("PATH", "")

    print("\n==============================")
    print("Running Airflow command")
    print("==============================")
    print("Command :", " ".join(command))
    print("PATH    :", env["PATH"])
    print("AIRFLOW_HOME :", env.get("AIRFLOW_HOME"))
    print("==============================\n")

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        env=env,
    )

    print("------ STDOUT ------")
    print(result.stdout)

    print("------ STDERR ------")
    print(result.stderr)

    print("Return code:", result.returncode)

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return result.stdout


# -------------------------------------------------
# DAG Operations
# -------------------------------------------------

def list_dags():
    output = _run_airflow_command(
        [
            AIRFLOW_CMD,
            "dags",
            "list",
        ]
    )

    dags = []

    for line in output.splitlines():
        if "/home/cloud/airflow_home/dags/" in line:
            dags.append(line.split("|")[0].strip())

    return dags


def trigger_dag(dag_id):
    return _run_airflow_command(
        [
            AIRFLOW_CMD,
            "dags",
            "trigger",
            dag_id,
        ]
    )


def pause_dag(dag_id):
    return _run_airflow_command(
        [
            AIRFLOW_CMD,
            "dags",
            "pause",
            dag_id,
        ]
    )


def unpause_dag(dag_id):
    return _run_airflow_command(
        [
            AIRFLOW_CMD,
            "dags",
            "unpause",
            dag_id,
        ]
    )


def get_latest_run(dag_id):
    return _run_airflow_command(
        [
            AIRFLOW_CMD,
            "dags",
            "list-runs",
            "-d",
            dag_id,
        ]
    )


def list_recent_runs(dag_id):
    return _run_airflow_command(
        [
            AIRFLOW_CMD,
            "dags",
            "list-runs",
            "-d",
            dag_id,
        ]
    )


# -------------------------------------------------
# Task Operations
# -------------------------------------------------

def list_tasks(dag_id):
    return _run_airflow_command(
        [
            AIRFLOW_CMD,
            "tasks",
            "list",
            dag_id,
        ]
    )


def get_task_status(dag_id, run_id):
    return _run_airflow_command(
        [
            AIRFLOW_CMD,
            "tasks",
            "states-for-dag-run",
            dag_id,
            run_id,
        ]
    )


def get_task_logs(dag_id, run_id, task_id, attempt=1):
    logfile = (
        LOG_ROOT
        / f"dag_id={dag_id}"
        / f"run_id={run_id}"
        / f"task_id={task_id}"
        / f"attempt={attempt}.log"
    )

    if not logfile.exists():
        return f"Log file not found:\n{logfile}"

    return logfile.read_text()


# -------------------------------------------------
# DAG Visualization
# -------------------------------------------------

def show_dag(dag_id):
    return _run_airflow_command(
        [
            AIRFLOW_CMD,
            "dags",
            "show",
            dag_id,
        ]
    )