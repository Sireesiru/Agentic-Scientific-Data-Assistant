#!/bin/bash

echo "======================================"
echo " Starting BRaVE AI Assistant"
echo "======================================"

# Activate environment
source /home/cloud/microflow_server/bin/activate

# ---------------------------------------
# 1. Start Airflow webserver
# ---------------------------------------

echo "[1/4] Starting Airflow webserver..."

nohup airflow webserver \
    > /home/cloud/metadata_agent/airflow_web.log 2>&1 &

sleep 3


# ---------------------------------------
# 2. Start Airflow scheduler
# ---------------------------------------

echo "[2/4] Starting Airflow scheduler..."

nohup airflow scheduler \
    > /home/cloud/metadata_agent/airflow_scheduler.log 2>&1 &

sleep 3


# ---------------------------------------
# 3. Start Ollama SSH tunnel
# ---------------------------------------

echo "[3/4] Starting Ollama tunnel..."

ssh -f -N \
    -L 11434:localhost:11434 \
    YOUR_USERNAME@10.64.194.121

sleep 2


# ---------------------------------------
# 4. Start Streamlit
# ---------------------------------------

echo "[4/4] Starting BRaVE chatbot..."

cd /home/cloud/metadata_agent

nohup streamlit run chat_app.py \
    > /home/cloud/metadata_agent/chat_app.log 2>&1 &


echo ""
echo "======================================"
echo " BRaVE services started"
echo "======================================"
echo ""
echo "Airflow:   http://localhost:8080"
echo "Ollama:    localhost:11434"
echo "Streamlit: check chat_app.log"