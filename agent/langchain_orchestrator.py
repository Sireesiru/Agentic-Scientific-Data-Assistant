from langchain_openai import ChatOpenAI

from tools.langchain_tools import (
    search_collection,
    get_metadata,
    airflow_list_dags,
    airflow_trigger_dag,
)

# ------------------------
# LLM
# ------------------------

llm = ChatOpenAI(
    model="gemma4:12b",
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)

# ------------------------
# Register tools
# ------------------------

TOOLS = [
    search_collection,
    get_metadata,
    airflow_list_dags,
    airflow_trigger_dag,
]

# Give the LLM access to the tools
llm = llm.bind_tools(TOOLS)