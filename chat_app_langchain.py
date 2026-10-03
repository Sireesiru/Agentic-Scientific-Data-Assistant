import json

import streamlit as st
from openai import OpenAI

from tools.langchain_tools import (
    search_collection,
    get_metadata,
    airflow_trigger_dag,
    airflow_list_dags,
)


# -------------------------------------------------
# Ollama / OpenAI-compatible client
# -------------------------------------------------

client = OpenAI(
    base_url="http://10.64.194.121:11434/v1",
    api_key="ollama",
)


# -------------------------------------------------
# Tool Registry
# -------------------------------------------------

TOOL_MAP = {
    "search_collection": search_collection,
    "get_metadata": get_metadata,
    "airflow_list_dags": airflow_list_dags,
    "airflow_trigger_dag": airflow_trigger_dag,
}


# -------------------------------------------------
# Tool Definitions for LLM
# -------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_collection",
            "description": "Return all datasets inside a DataFed collection.",
            "parameters": {
                "type": "object",
                "properties": {
                    "collection_id": {
                        "type": "string"
                    }
                },
                "required": ["collection_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_metadata",
            "description": "Return metadata for a DataFed dataset.",
            "parameters": {
                "type": "object",
                "properties": {
                    "data_id": {
                        "type": "string"
                    }
                },
                "required": ["data_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "airflow_list_dags",
            "description": "List all Airflow DAGs.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "airflow_trigger_dag",
            "description": "Trigger an Airflow DAG.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dag_id": {
                        "type": "string"
                    }
                },
                "required": ["dag_id"],
            },
        },
    },
]


# -------------------------------------------------
# Streamlit Page Configuration
# -------------------------------------------------

st.set_page_config(
    page_title="BRaVE AI Assistant",
    page_icon="??",
    layout="wide",
)

st.title("BRaVE AI Assistant")

st.caption(
    "Facility-scale Scientific Data Management, "
    "Workflow Orchestration and AI Assistant"
)


# -------------------------------------------------
# Sidebar
# -------------------------------------------------

with st.sidebar:

    st.header("Connected Services")

    st.success("Gemma 4 (GPU)")
    st.success("DataFed")
    st.success("Airflow")
    st.warning("MCP (Work in Progress)")

    st.divider()

    st.header("Available Tools")

    st.markdown(
        """
- Search DataFed collections
- Retrieve dataset metadata
- Trigger Airflow DAGs
- List Airflow DAGs
"""
    )

    st.divider()

    st.header("Try asking")

    st.markdown(
        """
- List datasets in collection c/525611319
- Trigger datafed_orchestration_pipeline
- Show metadata for dataset d/525688177
- List all Airflow DAGs
"""
    )


# -------------------------------------------------
# Chat History
# -------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []


for message in st.session_state.messages:

    # Do not display internal tool messages
    if isinstance(message, dict) and message.get("role") in [
        "user",
        "assistant",
    ]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


# -------------------------------------------------
# User Input
# -------------------------------------------------

prompt = st.chat_input("Ask BRaVE...")


if prompt:

    # Add user message to history
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)


    # -------------------------------------------------
    # First LLM Call
    # -------------------------------------------------

    try:

        with st.spinner("Gemma is reasoning..."):

            response = client.chat.completions.create(
                model="gemma4:12b",
                messages=st.session_state.messages,
                tools=TOOLS,
            )

        message = response.choices[0].message


        # -------------------------------------------------
        # Tool Calls
        # -------------------------------------------------

        if message.tool_calls:

            # Store assistant tool-call message
            st.session_state.messages.append(message)

            # Process every tool call requested by Gemma
            for tool_call in message.tool_calls:

                tool_name = tool_call.function.name

                try:
                    args = json.loads(
                        tool_call.function.arguments or "{}"
                    )
                except json.JSONDecodeError:
                    args = {}

                # Validate tool
                if tool_name not in TOOL_MAP:

                    result = {
                        "error": f"Unknown tool: {tool_name}"
                    }

                    st.error(
                        f"Gemma requested an unknown tool: {tool_name}"
                    )

                else:

                    st.info(f"Calling {tool_name}...")

                    tool = TOOL_MAP[tool_name]

                    try:

                        result = tool.invoke(args)

                        st.success(
                            f"{tool_name} execution completed."
                        )

                    except Exception as tool_error:

                        result = {
                            "error": str(tool_error)
                        }

                        st.error(
                            f"{tool_name} failed: {tool_error}"
                        )


                # Optional debug view
                with st.expander(
                    f"Tool Output: {tool_name}"
                ):
                    st.code(str(result))


                # Add tool result to conversation
                st.session_state.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result),
                    }
                )


            # -------------------------------------------------
            # Second LLM Call
            # Gemma interprets tool results
            # -------------------------------------------------

            with st.spinner("Gemma is interpreting the results..."):

                final_response = client.chat.completions.create(
                    model="gemma4:12b",
                    messages=st.session_state.messages,
                    tools=TOOLS,
                )

            final_message = final_response.choices[0].message

            answer = (
                final_message.content
                or "Tool execution completed."
            )


        # -------------------------------------------------
        # No Tool Required
        # -------------------------------------------------

        else:

            answer = (
                message.content
                or "I could not generate a response."
            )


    # -------------------------------------------------
    # General Error Handling
    # -------------------------------------------------

    except Exception as error:

        answer = f"Error communicating with Gemma: {error}"

        st.error(answer)


    # -------------------------------------------------
    # Save Assistant Response
    # -------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )


    # -------------------------------------------------
    # Display Assistant Response
    # -------------------------------------------------

    with st.chat_message("assistant"):
        st.markdown(answer)