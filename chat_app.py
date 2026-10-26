import json
from pathlib import Path
import asyncio
import streamlit as st
from openai import OpenAI
from mcp.client.session import ClientSession
from mcp.client.stdio import (stdio_client, StdioServerParameters,)


CHAT_HISTORY_FILE = Path("/home/cloud/metadata_agent/chat_history.json")

# ============================================================
# LLM
# ============================================================
client = OpenAI(base_url="http://10.64.194.121:11434/v1", api_key="ollama",)
MODEL = "gemma4:12b"

# ============================================================
# MCP
# ============================================================

SERVER = StdioServerParameters(command="python", args=["-m", "mcp_servers.brave_server"],)

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


# ============================================================
# Agent
# ============================================================

#async def run_agent(messages):
#    """
#    Run the LLM + MCP tool loop.
#
#    The model may call multiple tools sequentially before
#    producing its final scientific answer.
#    """
#
#    async with stdio_client(SERVER) as (
#        read_stream,
#        write_stream,
#    ):
#
#        async with ClientSession(
#            read_stream,
#            write_stream,
#        ) as session:
#
#            await session.initialize()
#
#            # --------------------------------------------
#            # Discover tools dynamically from MCP
#            # --------------------------------------------
#
#            tool_response = await session.list_tools()
#
#            openai_tools = mcp_tools_to_openai(
#                tool_response.tools
#            )
#
#            # --------------------------------------------
#            # Agent reasoning loop
#            # --------------------------------------------
#
#            max_iterations = 15
#
#            for iteration in range(max_iterations):
#
#                response = client.chat.completions.create(
#                    model=MODEL,
#                    messages=messages,
#                    tools=openai_tools,
#                )
#
#                assistant_message = (
#                    response.choices[0].message
#                )
#
#                # ----------------------------------------
#                # No more tools -> final answer
#                # ----------------------------------------
#
#                if not assistant_message.tool_calls:
#
#                    answer = (
#                        assistant_message.content
#                        or "I could not generate a response."
#                    )
#
#                    return {
#                        "answer": answer,
#                        "messages": messages,
#                        "plots": [],
#                    }
#
#                # ----------------------------------------
#                # Store assistant tool-call message
#                # ----------------------------------------
#
#                messages.append(
#                    {
#                        "role": "assistant",
#                        "content": assistant_message.content,
#                        "tool_calls": [
#                            {
#                                "id": tc.id,
#                                "type": "function",
#                                "function": {
#                                    "name": tc.function.name,
#                                    "arguments": tc.function.arguments,
#                                },
#                            }
#                            for tc in assistant_message.tool_calls
#                        ],
#                    }
#                )
#
#                # ----------------------------------------
#                # Execute requested MCP tools
#                # ----------------------------------------
#
#                for tool_call in assistant_message.tool_calls:
#                    tool_name = tool_call.function.name
#                    try:
#                        arguments = json.loads(
#                            tool_call.function.arguments
#                            or "{}"
#                        )
#                    except json.JSONDecodeError:
#                        arguments = {}
#
#                    # Show activity in Streamlit
#
#                    st.info(
#                        f"Agent calling: {tool_name}"
#                    )
#
#                    try:
#                        result = await session.call_tool(
#                            tool_name,
#                            arguments,
#                        )
#                        result_text = parse_mcp_result(
#                            result
#                        )
#                        if result.isError:
#
#                            st.error(
#                                f"{tool_name} returned an error."
#                            )
#                        else:
#                            st.success(
#                                f"{tool_name} completed."
#                            )
#                            
#                            try:
#                                result_data = json.loads(result_text)
#                                plot_paths = []
#                            
#                                if result_data.get("plot_path"):
#                                    plot_paths.append(result_data["plot_path"])
#                                if result_data.get("difference_plot_path"):
#                                    plot_paths.append(result_data["difference_plot_path"])
#                                if result_data.get("absolute_difference_plot_path"):
#                                    plot_paths.append(result_data["absolute_difference_plot_path"])
#                                if result_data.get("distribution_plot_path"):
#                                    plot_paths.append(result_data["distribution_plot_path"])
#                                for plot_path in plot_paths:
#                                    plot_file = Path(plot_path)
#                            
#                                    if plot_file.exists():
#                                        st.image(
#                                            str(plot_file),
#                                            caption=(
#                                                tool_name
#                                                .replace("_", " ")
#                                                .title()
#                                            ),
#                                            width=500,
#                                        )
#
#                            except (
#                                json.JSONDecodeError,
#                                TypeError,
#                                AttributeError,
#                            ):
#                                pass
#
#                    except Exception as error:
#                        result_text = json.dumps(
#                            {
#                                "error": str(error)
#                            }
#                        )
#
#                        st.error(
#                            f"{tool_name} failed: {error}"
#                        )
#
#                    # ------------------------------------
#                    # Debug output
#                    # ------------------------------------
#
#                    with st.expander(
#                        f"Tool Output: {tool_name}"
#                    ):
#                        st.code(result_text)
#
#                    # ------------------------------------
#                    # Send tool result back to LLM
#                    # ------------------------------------
#
#                    messages.append(
#                        {
#                            "role": "tool",
#                            "tool_call_id": tool_call.id,
#                            "content": result_text,
#                        }
#                    )
#
#            return {
#                "answer": (
#                    "The agent reached the maximum number "
#                    "of reasoning/tool iterations."
#                ),
#                "messages": messages,
#                "plots": [],
#            }
#
async def run_agent(messages):
    """
    Run the LLM + MCP tool loop.

    The model may call multiple tools sequentially before
    producing its final scientific answer.

    Evidence-gating prevents the model from producing a final
    answer before explicitly requested data inspection, metadata
    inspection, analysis, visualization, or literature retrieval
    has actually been completed.
    """

    # ============================================================
    # Determine evidence explicitly required by CURRENT request
    # ============================================================

    current_user_message = ""

    for msg in reversed(messages):
        if msg.get("role") == "user":
            current_user_message = msg.get("content", "")
            break

    request_lower = current_user_message.lower()

    require_data_inspection = any(
        phrase in request_lower
        for phrase in [
            "inspect the actual",
            "inspect actual",
            "inspect the data",
            "inspect experimental",
            "inspect dataset",
            "inspect the dataset",
            "inspect datasets",
            "inspect the datasets",
            "inspect channels",
            "inspect the channels",
            "actual data",
            "actual dataset",
            "actual datasets",
        ]
    )

    require_metadata = any(
        phrase in request_lower
        for phrase in [
            "inspect metadata",
            "inspect the metadata",
        ]
    )

    require_literature = any(
        phrase in request_lower
        for phrase in [
            "literature",
            "published evidence",
            "published studies",
            "literature evidence",
            "literature-supported",
        ]
    )

    require_analysis = any(
        phrase in request_lower
        for phrase in [
            "perform the analysis",
            "perform analysis",
            "quantitative comparison",
            "quantitatively compare",
            "calculate",
            "compute",
            "analyze the data",
            "analyse the data",
        ]
    )

    require_visualization = any(
        phrase in request_lower
        for phrase in [
            "plot",
            "visualize",
            "visualise",
            "show the distribution",
            "show me the topography",
            "display any generated analysis plots",
        ]
    )

    # ============================================================
    # Track evidence obtained during THIS request
    # ============================================================

    evidence = {
        "data_inspection": False,
        "metadata": False,
        "literature": False,
        "analysis": False,
        "visualization": False,
    }

    # Tool groups
    inspection_tools = {
        "inspect_h5_datasets",
        "inspect_record",
        "get_data",
    }

    metadata_tools = {
        "get_metadata",
        "inspect_record",
    }

    literature_tools = {
        "search_scientific_literature",
    }

    analysis_tools = {
        "compare_datasets",
        "compare_distributions",
        "plot_distribution",
        "visualize_data",
    }

    visualization_tools = {
        "compare_datasets",
        "compare_distributions",
        "plot_distribution",
        "visualize_data",
    }

    # ============================================================
    # Helper: determine which explicitly requested steps are missing
    # ============================================================

    def missing_evidence():

        missing = []

        if require_data_inspection and not evidence["data_inspection"]:
            missing.append("actual experimental data inspection")

        if require_metadata and not evidence["metadata"]:
            missing.append("experimental metadata inspection")

        if require_literature and not evidence["literature"]:
            missing.append("scientific literature retrieval")

        if require_analysis and not evidence["analysis"]:
            missing.append("requested scientific analysis")

        if require_visualization and not evidence["visualization"]:
            missing.append("requested visualization")

        return missing

    # ============================================================
    # MCP session
    # ============================================================

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

                # ========================================
                # No tool call: Gemma wants to finish
                # ========================================

                if not assistant_message.tool_calls:

                    missing = missing_evidence()

                    # ------------------------------------
                    # All requested evidence obtained
                    # ------------------------------------

                    if not missing:

                        answer = (
                            assistant_message.content
                            or "I could not generate a response."
                        )

                        return {
                            "answer": answer,
                            "messages": messages,
                            "plots": [],
                        }

                    # ------------------------------------
                    # Evidence missing: reject completion
                    # ------------------------------------

                    missing_text = "\n".join(
                        f"- {item}"
                        for item in missing
                    )

                    st.warning(
                        "Evidence gate prevented premature "
                        "completion. Missing: "
                        + ", ".join(missing)
                    )

                    # Keep Gemma's attempted answer in context
                    messages.append(
                        {
                            "role": "assistant",
                            "content": (
                                assistant_message.content
                                or ""
                            ),
                        }
                    )

                    # Tell Gemma why it is not finished
                    messages.append(
                        {
                            "role": "system",
                            "content": f"""
EVIDENCE COMPLETION CHECK FAILED.

The user's request explicitly requires evidence that has
not yet been obtained.

Missing:

{missing_text}

Continue using the available MCP tools before producing
the final answer.

Do not substitute pretrained knowledge for the missing
experimental or literature evidence.

Do not claim that data, metadata, analysis, visualization,
or literature retrieval was performed unless the
corresponding tool completed successfully during this
request.
""",
                        }
                    )

                    continue

                # ========================================
                # Store assistant tool-call message
                # ========================================

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

                # ========================================
                # Execute requested MCP tools
                # ========================================

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

                            # ============================
                            # UPDATE EVIDENCE STATE
                            # only after successful call
                            # ============================

                            if tool_name in inspection_tools:
                                evidence["data_inspection"] = True

                            if tool_name in metadata_tools:
                                evidence["metadata"] = True

                            if tool_name in literature_tools:
                                evidence["literature"] = True

                            if tool_name in analysis_tools:
                                evidence["analysis"] = True

                            if tool_name in visualization_tools:
                                evidence["visualization"] = True

                            # ============================
                            # Existing plot display logic
                            # ============================

                            try:

                                result_data = json.loads(
                                    result_text
                                )

                                plot_paths = []

                                if result_data.get("plot_path"):
                                    plot_paths.append(
                                        result_data["plot_path"]
                                    )

                                if result_data.get(
                                    "difference_plot_path"
                                ):
                                    plot_paths.append(
                                        result_data[
                                            "difference_plot_path"
                                        ]
                                    )

                                if result_data.get(
                                    "absolute_difference_plot_path"
                                ):
                                    plot_paths.append(
                                        result_data[
                                            "absolute_difference_plot_path"
                                        ]
                                    )

                                if result_data.get(
                                    "distribution_plot_path"
                                ):
                                    plot_paths.append(
                                        result_data[
                                            "distribution_plot_path"
                                        ]
                                    )

                                for plot_path in plot_paths:

                                    plot_file = Path(plot_path)

                                    if plot_file.exists():

                                        st.image(
                                            str(plot_file),
                                            caption=(
                                                tool_name
                                                .replace("_", " ")
                                                .title()
                                            ),
                                            width=500,
                                        )

                            except (
                                json.JSONDecodeError,
                                TypeError,
                                AttributeError,
                            ):
                                pass

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

            # ============================================
            # Maximum iterations reached
            # ============================================

            missing = missing_evidence()

            if missing:

                return {
                    "answer": (
                        "The agent reached the maximum number "
                        "of reasoning/tool iterations before "
                        "obtaining all evidence required by the "
                        "request. Missing evidence: "
                        + ", ".join(missing)
                        + "."
                    ),
                    "messages": messages,
                    "plots": [],
                }

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

    if CHAT_HISTORY_FILE.exists():
        try:
            with open(
                CHAT_HISTORY_FILE,
                "r",
            ) as f:
                st.session_state.messages = json.load(f)

        except Exception:
            st.session_state.messages = []

    else:
        st.session_state.messages = []

    # Always ensure the system prompt exists

    if not st.session_state.messages:
        st.session_state.messages = [
            {
                "role": "system",
                "content": """

You are the BRaVE scientific data assistant.

Your role is to investigate scientific data by using tools, not to
simulate tool results from your own knowledge.

When an answer can be obtained from the connected experimental data or
analysis tools, prefer obtaining the evidence through those tools before
reasoning about it.

Your primary evidence is the experimental data available through DataFed.

Use the available MCP tools to discover relevant collections, records,
metadata, provenance, numerical datasets, and scientific analysis results.

Do not ask the user for internal DataFed IDs, HDF5 paths, or channel names
when these can be discovered using the tools.


For scientific questions, follow this workflow.

1. GROUND IN THE EXPERIMENTAL DATA

First investigate the relevant experimental data in DataFed.

Discover the relevant records, metadata, provenance, numerical datasets,
channels, and measurements using the available tools.

Do not assume that a measurement, channel, dataset, modality, unit, or
experimental condition exists until it has been discovered from the data
or metadata.

Do not assume a fixed metadata schema or HDF5 structure. Different
instruments and file formats may organize their data differently.


2. DETERMINE WHAT CAN ACTUALLY BE ANALYZED

Based on the discovered experimental data, determine which analyses are
scientifically meaningful and supported by the available analysis tools.

Choose datasets based on their scientific meaning, measurement type,
units, dimensions, and experimental context.

Do not compare two quantities merely because both are numerical.

When dataset paths or channel names are required, discover them using
the available tools rather than inventing them or asking the user when
they can be discovered automatically.

Choose the comparison method according to the scientific relationship
between the datasets.

Use compare_datasets when corresponding array positions represent
scientifically comparable measurements and pixel-wise comparison is
meaningful. The two datasets may come from the same DataFed record or
from different DataFed records. If they are from the same record, use
that record ID for both data_id_a and data_id_b.

Use compare_distributions when comparing numerical value distributions,
especially for independent experimental images or measurements where
pixel-to-pixel spatial correspondence is not meaningful.

Do not use pixel-wise correlation, RMSE, or difference maps merely
because two arrays happen to have the same dimensions.


3. EXECUTE REQUESTED ANALYSES

When the user asks you to perform, calculate, compare, analyze,
visualize, or plot experimental data, you MUST execute the appropriate
scientific analysis tool during the current request.

Do not calculate experimental numerical results yourself.

Do not reuse numerical results, plots, or analysis outputs from earlier
conversation turns as a substitute for executing the requested analysis.

Report numerical analysis results only when they were returned by a
successful scientific tool call.

Never claim that an analysis, comparison, calculation, visualization,
or plot was performed unless the corresponding tool call completed
successfully.


4. COMPLETE MULTI-STEP REQUESTS BEFORE ANSWERING

A user request may require multiple tool calls.

Before producing the final answer, check whether every executable part
of the user's request has been completed.

For example, if the user asks you to inspect the data, select an analysis,
perform the analysis, generate plots, and interpret the results, continue
making tool calls until all requested executable steps have been completed.

Do not stop after inspection or analysis if the user also requested
visualization, comparison, interpretation, or another available action.

If a tool call fails because of an incorrect dataset path or other
recoverable error, use the available discovery information to correct
the problem and retry when appropriate.

If the requested analysis cannot be completed with the available data
or tools, clearly state what is missing.


5. USE LITERATURE WHEN IT ADDS SCIENTIFIC EVIDENCE

Use search_scientific_literature when the question requires scientific
context, methodological justification, interpretation, hypothesis
generation, or recommendations that would benefit from literature evidence.

Give the literature tool relevant experimental context discovered from
DataFed.

Do not search the literature independently of the experimental context
when the question concerns a specific experimental dataset.

Do not use literature retrieval as a substitute for analyzing the
experimental data.

Do not call the literature tool when the user explicitly asks for
data-only analysis or says not to use literature.


6. INTERPRET RESULTS CONSERVATIVELY

Separate what the analysis directly demonstrates from possible
scientific explanations.

A numerical association or image similarity does not by itself establish
a biological mechanism, material mechanism, sample stability, instrument
performance, causation, or experimental quality.

Use language such as "shows", "indicates", or "is consistent with"
according to the strength of the available evidence.

Do not convert correlation into causation.

Do not infer scientific meaning from a numerical result without
considering the measurement type and experimental context.


7. REASON ITERATIVELY WHEN NEEDED

After obtaining an analysis result, determine whether another available
analysis is necessary to answer the user's question.

Perform additional analysis or literature retrieval when it would
materially improve the answer.

Do not perform unnecessary analyses merely because tools are available.


8. RECOMMEND NEXT STEPS BASED ON EVIDENCE

When appropriate, recommend the most informative next analysis that can
be performed using the existing data.

Recommend a new experiment only when it addresses an important
uncertainty or scientific question that the existing data cannot
adequately resolve.

Explain what uncertainty the proposed analysis or experiment would address.


9. MAINTAIN EVIDENCE TRACEABILITY

Clearly distinguish among:

- observations and numerical results obtained from experimental data,
- scientific interpretation of those results,
- conclusions or methods supported by retrieved literature,
- hypotheses and suggested next steps.

Never invent numerical values, dataset contents, tool results, literature
evidence, or completed actions.

If the available data, literature, or tools are insufficient to support
a conclusion, state what is missing instead of filling the gap with an
assumption.

10. When comparing datasets, first determine whether the datasets are in the same DataFed record or in different DataFed records.

The comparison tools compare TWO datasets and always require FOUR arguments:

- data_id_a: DataFed record containing dataset A
- dataset_path_a: HDF5 path of dataset A
- data_id_b: DataFed record containing dataset B
- dataset_path_b: HDF5 path of dataset B

Never call compare_datasets or compare_distributions using the argument
"data_id". These tools do not accept "data_id".

For two datasets in the same record, provide that same record ID as both
data_id_a and data_id_b.

For datasets in different records, provide the corresponding record ID
for data_id_a and data_id_b.

Before calling a comparison tool, discover both dataset paths and construct
all four required arguments.

Choose the comparison method according to the scientific relationship
between the datasets.

Use compare_datasets when corresponding array positions represent
scientifically comparable measurements and pixel-wise spatial comparison
is meaningful.

Use compare_distributions when comparing numerical value distributions,
especially for independent experimental images or measurements where
pixel-to-pixel spatial correspondence is not meaningful.

Do not use pixel-wise correlation, RMSE, or difference maps merely because
two arrays happen to have the same dimensions.

If a comparison tool call fails because an argument is missing or invalid,
inspect the tool error, correct the arguments, and retry the tool before
producing the final answer.

11. Interpret cross-record comparisons conservatively.

A statistically significant difference between two datasets demonstrates
that the measured numerical distributions differ. It does not by itself
establish the biological or experimental cause of that difference.

Do not attribute a difference to treatment, concentration, time, sample
condition, instrument performance, biological change, or another causal
factor unless the available metadata or other evidence supports that
interpretation.

For independent AFM topography images, be especially careful when
interpreting absolute height values. Differences in absolute Z offset or
mean topography between separate scans may reflect referencing, leveling,
preprocessing, scan conditions, or other experimental factors. Do not
automatically interpret an absolute shift in topography as a biological
height difference.

When reporting statistical tests, describe extremely small p-values
conservatively. If a tool reports a p-value of 0.0, state that it is
effectively zero at numerical precision rather than claiming that the
true p-value is exactly zero.

    Clearly separate:
    - what the numerical comparison directly demonstrates,
    - what may be a possible explanation,
    - and what additional evidence would be required to establish that
      explanation.
      
12. USE LITERATURE ONLY THROUGH RETRIEVED EVIDENCE
When the user asks for literature evidence, literature-supported
interpretation, published evidence, or scientific literature context,
you MUST call search_scientific_literature during the current request.

Do not substitute your internal knowledge for a requested literature
search.

Never state or imply that a literature search was performed unless
search_scientific_literature completed successfully during the current
request.

When experimental analysis is also requested, first obtain the relevant
experimental result. Then use the experimental finding to formulate a
focused literature search relevant to interpreting that result.

After literature retrieval, base literature-supported claims only on
information returned by search_scientific_literature.

If the retrieved literature does not support a proposed explanation,
do not present that explanation as literature-supported.

If search_scientific_literature fails or returns insufficient evidence,
explicitly state that adequate literature evidence was not retrieved.

Clearly distinguish:
- experimental observations obtained from analysis tools,
- statements directly supported by retrieved literature,
- scientific interpretation connecting the two,
- hypotheses that remain unverified.

Do not describe scientific claims from internal model knowledge as
retrieved literature evidence.
""",
            }
        ]


# ============================================================
# Editable prompt state
# ============================================================

if "edit_prompt" not in st.session_state:
    st.session_state.edit_prompt = ""


# ============================================================
# Display only user/assistant conversation
# ============================================================

for i, message in enumerate(
    st.session_state.messages
):

    if message.get("role") in [
        "user",
        "assistant",
    ]:

        content = message.get("content")

        if content:

            with st.chat_message(
                message["role"]
            ):

                if message["role"] == "user":

                    col1, col2 = st.columns(
                        [0.94, 0.06]
                    )

                    with col1:
                        st.markdown(content)

                    with col2:

                        if st.button(
                            "✏️",
                            key=f"edit_{i}",
                            help="Edit this prompt",
                        ):
                            st.session_state.edit_prompt = (
                                content
                            )
                            st.rerun()

                else:
                    st.markdown(content)


# ============================================================
# User input
# ============================================================

if st.session_state.edit_prompt:

    prompt = st.text_area(
        "Edit prompt",
        value=st.session_state.edit_prompt,
        key="edited_prompt_text",
    )

    col1, col2 = st.columns([1, 1])

    with col1:

        submit_edit = st.button(
            "Send edited prompt",
            type="primary",
        )

    with col2:

        cancel_edit = st.button(
            "Cancel",
        )

    if cancel_edit:
        st.session_state.edit_prompt = ""
        st.rerun()

    if not submit_edit:
        prompt = None

    else:
        st.session_state.edit_prompt = ""

else:

    prompt = st.chat_input(
        "Ask BRaVE about your scientific data..."
    )


# ============================================================
# Process prompt
# ============================================================

if prompt:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with open(
        CHAT_HISTORY_FILE,
        "w",
    ) as f:
        json.dump(
            st.session_state.messages,
            f,
            indent=2,
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

    with open(
        CHAT_HISTORY_FILE,
        "w",
    ) as f:
        json.dump(
            st.session_state.messages,
            f,
            indent=2,
        )

    with st.chat_message("assistant"):
        st.markdown(answer)