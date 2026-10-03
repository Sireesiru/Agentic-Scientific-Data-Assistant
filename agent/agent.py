import json
from openai import OpenAI
from tools.langchain_tools import (search_collection,get_metadata,airflow_list_dags, airflow_trigger_dag,)

client = OpenAI(
    base_url="http://10.64.194.121:11434/v1",
    api_key="ollama",
)

# -------------------------------------------------
# Tools available to Gemma
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
                "required": ["collection_id"]
            }
        }
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
                "required": ["data_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "airflow_list_dags",
            "description": "List all Airflow DAGs.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
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
                "required": ["dag_id"]
            }
        }
    }
]
# -------------------------------------------------
# User question
# -------------------------------------------------

messages = [
    {
        "role": "user",
        "content": "Trigger the datafed_orchestration_pipeline"
    }
]

# -------------------------------------------------
# First call to Gemma
# -------------------------------------------------

response = client.chat.completions.create(
    model="gemma4:12b",
    messages=messages,
    tools=TOOLS,
)

message = response.choices[0].message

print("\n===== FIRST RESPONSE =====\n")
print(message)

# -------------------------------------------------
# Execute requested tool
# -------------------------------------------------

#if message.tool_calls:
#    tool_call = message.tool_calls[0]
#    tool_name = tool_call.function.name
#    args = json.loads(tool_call.function.arguments)
#    print(f"\nExecuting {tool_name}...\n")
#
#    if tool_name == "search_collection":
#        result = search_collection.invoke(
#            {
#                "collection_id": args["collection_id"]
#            }
#        )
#    elif tool_name == "get_metadata":
#        result = get_metadata.invoke(
#            {
#                "data_id": args["data_id"]
#            }
#        )
#    elif tool_name == "airflow_list_dags":
#        print("\nExecuting airflow_list_dags...\n")
#        result = airflow_list_dags.invoke({})
#    elif tool_name == "airflow_trigger_dag":
#        print("\nExecuting airflow_trigger_dag...\n")
#        result = airflow_trigger_dag.invoke(
#             {
#                "dag_id": args["dag_id"]
#             }
#        )
#    else:
#        raise ValueError(f"Unknown tool: {tool_name}")
#    print(result)

if message.tool_calls:

    tool_results = []

    for tool_call in message.tool_calls:

        tool_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        print(f"\nExecuting {tool_name}...\n")

        if tool_name == "search_collection":

            result = search_collection.invoke(
                {
                    "collection_id": args["collection_id"]
                }
            )

        elif tool_name == "get_metadata":

            result = get_metadata.invoke(
                {
                    "data_id": args["data_id"]
                }
            )

        elif tool_name == "airflow_list_dags":

            result = airflow_list_dags.invoke({})

        elif tool_name == "airflow_trigger_dag":

            result = airflow_trigger_dag.invoke(
                {
                    "dag_id": args["dag_id"]
                }
            )

        else:

            raise ValueError(f"Unknown tool: {tool_name}")

        print(result)

        tool_results.append(result)

        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            }
        )
 
    # Add assistant message
    messages.append(message)

    # Add tool result
    messages.append(
        {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": str(result)
        }
    )

    # -------------------------------------------------
    # Second call to Gemma
    # -------------------------------------------------

    final_response = client.chat.completions.create(
        model="gemma4:12b",
        messages=messages,
        tools=TOOLS,
    )

    print("\n===== FINAL ANSWER =====\n")

    print(final_response.choices[0].message.content)