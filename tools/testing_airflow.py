from tools.airflows_tool import *

DAG_ID = "datafed_orchestration_pipeline"

print("========== LIST DAGS ==========")
print(list_dags())

print("\n========== TRIGGER DAG ==========")
print(trigger_dag(DAG_ID))

for dag in list_dags():
    print(f"\n===== {dag} =====")
    print(get_latest_run(dag))

#print("\n========== LATEST RUN ==========")
#print(get_latest_run(DAG_ID))
#
#print("\n========== RECENT RUNS ==========")
#print(list_recent_runs(DAG_ID))

print("\n========== LIST TASKS ==========")
print(list_tasks(DAG_ID))

print("\n========== SHOW DAG ==========")
print(show_dag(DAG_ID))

# -------------------------------------------------
# After the above runs, copy the latest run_id here
# Example:
# run_id = "manual__2026-08-13T18:05:38+00:00"
# -------------------------------------------------

# run_id = ""

# print("\n========== TASK STATUS ==========")
# print(get_task_status(DAG_ID, run_id))

# print("\n========== TASK LOGS ==========")
# print(get_task_logs(
#     DAG_ID,
#     "run_production_pipeline",
#     run_id,
# ))

# Optional (test separately)
# print("\n========== PAUSE DAG ==========")
# print(pause_dag(DAG_ID))

# print("\n========== UNPAUSE DAG ==========")
# print(unpause_dag(DAG_ID))