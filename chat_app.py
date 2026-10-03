import asyncio
import json
from pathlib import Path

import streamlit as st
from openai import OpenAI

from mcp.client.session import ClientSession
from mcp.client.stdio import (
    stdio_client,
    StdioServerParameters,
)


# ============================================================
# LLM
# ============================================================

client = OpenAI(
    base_url="http://10.64.194.121:11434/v1",
    api_key="ollama",
)

MODEL = "gemma4:12b"


# ============================================================
# MCP
# ============================================================

SERVER = StdioServerParameters(
    command="python",
    args=["-m", "mcp_servers.brave_server"],
)


def mcp_tools_to_openai(mcp_tools):
    """
    Convert MCP tool definitions into the OpenAI-compatible
    function-calling format expected by Ollama/Gemma.
    """

    tools = []

    for tool in mcp_tools:

        tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema,
                },
            }
        )

    return tools


def parse_mcp_result(result):
    """
    Convert an MCP CallToolResult into ordinary text that can
    be returned to the LLM.
    """

    parts = []

    for item in result.content:

        if getattr(item, "type", None) == "text":
            parts.append(item.text)

    return "\n".join(parts)


async def run_agent(messages):
    """
    Run the LLM + MCP tool loop.

    The model may call multiple tools sequentially before
    producing its final scientific answer.
    """

    async with stdio_client(SERVER) as (
        read_stream,
        write_stream,
    ):

        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            await session.initialize()

            # --------------------------------------------
            # Discover tools dynamically from MCP
            # --------------------------------------------

            tool_response = await session.list_tools()

            openai_tools = mcp_tools_to_openai(
                tool_response.tools
            )

            # --------------------------------------------
            # Agent reasoning loop
            # --------------------------------------------

            max_iterations = 15

            for iteration in range(max_iterations):

                response = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    tools=openai_tools,
                )

                assistant_message = (
                    response.choices[0].message
                )

                # ----------------------------------------
                # No more tools -> final answer
                # ----------------------------------------

                if not assistant_message.tool_calls:

                    answer = (
                        assistant_message.content
                        or "I could not generate a response."
                    )

                    return {
                        "answer": answer,
                        "messages": messages,
                        "plots": [],
                    }

                # ----------------------------------------
                # Store assistant tool-call message
                # ----------------------------------------

                messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_message.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in assistant_message.tool_calls
                        ],
                    }
                )

                # ----------------------------------------
                # Execute requested MCP tools
                # ----------------------------------------

                for tool_call in assistant_message.tool_calls:

                    tool_name = tool_call.function.name

                    try:
                        arguments = json.loads(
                            tool_call.function.arguments
                            or "{}"
                        )
                    except json.JSONDecodeError:
                        arguments = {}

                    # Show activity in Streamlit
                    st.info(
                        f"Agent calling: {tool_name}"
                    )

                    try:

                        result = await session.call_tool(
                            tool_name,
                            arguments,
                        )

                        result_text = parse_mcp_result(
                            result
                        )

                        if result.isError:
                            st.error(
                                f"{tool_name} returned an error."
                            )
                        else:
                            st.success(
                                f"{tool_name} completed."
                            )

                    except Exception as error:

                        result_text = json.dumps(
                            {
                                "error": str(error)
                            }
                        )

                        st.error(
                            f"{tool_name} failed: {error}"
                        )

                    # ------------------------------------
                    # Debug output
                    # ------------------------------------

                    with st.expander(
                        f"Tool Output: {tool_name}"
                    ):
                        st.code(result_text)

                    # ------------------------------------
                    # Send tool result back to LLM
                    # ------------------------------------

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result_text,
                        }
                    )

            return {
                "answer": (
                    "The agent reached the maximum number "
                    "of reasoning/tool iterations."
                ),
                "messages": messages,
                "plots": [],
            }


# ============================================================
# Streamlit
# ============================================================

st.set_page_config(
    page_title="BRaVE AI Assistant",
    page_icon="🔬",
    layout="wide",
)

st.title("BRaVE AI Assistant")

st.caption(
    "Facility-scale Scientific Data Management, "
    "Scientific Analysis and AI Assistant"
)


# ============================================================
# Sidebar
# ============================================================

with st.sidebar:

    st.header("Connected Services")

    st.success("Gemma 4 (GPU)")
    st.success("DataFed")
    st.success("MCP")
    st.success("Scientific Analysis")

    st.divider()

    st.header("Agent Capabilities")

    st.markdown(
        """
- Discover DataFed collections
- Search scientific records
- Inspect experimental metadata
- Explore provenance
- Inspect numerical HDF5/NXS data
- Visualize scientific datasets
- Analyze value distributions
"""
    )

    st.divider()

    st.header("Try asking")

    st.markdown(
        """
- Find the Panteoa YR343 datasets.
- What metadata is available for these experiments?
- Compare the scan sizes and resolutions of the AFM datasets.
- Show me the topography of BioFilm_10%_0.
- Show me the distribution of its topography values.
"""
    )


# ============================================================
# Conversation
# ============================================================

if "messages" not in st.session_state:

    st.session_state.messages = [
        {
            "role": "system",
            "content": """
You are the BRaVE scientific data assistant.

Use the available MCP tools to investigate scientific
datasets rather than asking the user for internal DataFed
record IDs, collection IDs, HDF5 paths, or channel names
when those can be discovered using the tools.

For scientific questions, reason iteratively.

First discover the relevant collections and records.
Then inspect metadata or numerical datasets as required.
Use scientific visualization or distribution tools when
they help answer the question.

Metadata may differ between instruments and file formats.
Do not assume a fixed metadata schema. Inspect the
available metadata and determine which fields correspond
to the scientific concepts requested by the user.

Do not claim that two quantities are comparable merely
because both are numerical. Consider their scientific
meaning and units.

If the available data or tools are insufficient to answer
a question, explain what is missing rather than inventing
a result.
""",
        }
    ]


# Display only user/assistant conversation
for message in st.session_state.messages:

    if message.get("role") in [
        "user",
        "assistant",
    ]:

        content = message.get("content")

        if content:

            with st.chat_message(
                message["role"]
            ):
                st.markdown(content)


# ============================================================
# User input
# ============================================================

prompt = st.chat_input(
    "Ask BRaVE about your scientific data..."
)


if prompt:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    try:

        with st.spinner(
            "BRaVE is investigating the data..."
        ):

            result = asyncio.run(
                run_agent(
                    st.session_state.messages
                )
            )

        answer = result["answer"]

    except Exception as error:

        answer = (
            f"Agent error: {error}"
        )

        st.error(answer)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )

    with st.chat_message("assistant"):
        st.markdown(answer)