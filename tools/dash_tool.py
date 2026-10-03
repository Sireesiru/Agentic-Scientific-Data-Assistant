import subprocess
from pathlib import Path
import pandas as pd

DASH_SCRIPT = "/home/cloud/Globus-Personal-Docker/dash_app.py"
MEASURE_DIR = Path("/home/cloud/Globus-Personal-Docker/data/measurements")


def launch_dashboard():
    """
    Start the Dash dashboard.
    """
    subprocess.Popen(
        ["python", DASH_SCRIPT],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return "Dashboard started."


def list_samples():
    """
    List all analyzed samples.
    """
    samples = []

    if MEASURE_DIR.exists():
        for f in sorted(MEASURE_DIR.glob("*_measurements.csv")):
            samples.append(
                f.name.replace("_measurements.csv", "")
            )

    return samples


def latest_sample():
    """
    Return the newest analyzed sample.
    """
    files = sorted(
        MEASURE_DIR.glob("*_measurements.csv"),
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )

    if not files:
        return "No analyzed samples."

    return files[0].name.replace("_measurements.csv", "")


def get_measurements(sample_name):
    """
    Return measurements for one sample.
    """
    csv = MEASURE_DIR / f"{sample_name}_measurements.csv"

    if not csv.exists():
        return f"{sample_name} not found."

    df = pd.read_csv(csv)

    return df.to_dict(orient="records")