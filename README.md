# Agentic Scientific Data Assistant

An agentic AI framework for natural-language scientific data discovery and analysis using **LLM tool calling, Model Context Protocol (MCP), DataFed, and scientific Python tools**.

The system enables a scientist to ask questions in natural language while the LLM determines which tools to use, retrieves experimental data and metadata, performs scientific analysis, and synthesizes the results.

## Overview

Scientific data analysis often requires researchers to interact separately with data repositories, workflow systems, analysis scripts, and visualization tools.

This project explores an agentic approach in which an LLM acts as an orchestration layer between the scientist and these scientific resources.

The current implementation focuses on microscopy data stored in **DataFed** and standardized **HDF5/NeXus** files.

## Architecture

```text
Scientist
    |
    v
Natural-Language Question
    |
    v
+---------------------+
|   Streamlit Agent   |
|        + LLM        |
+----------+----------+
           |
           | Tool Calling
           v
+---------------------+
|     MCP Client      |
+----------+----------+
           |
           v
+---------------------+
|     MCP Server      |
+----------+----------+
           |
     +-----+------+
     |            |
     v            v
+---------+   +------------------+
| DataFed |   | Scientific Tools |
|  Tools  |   | HDF5 / Analysis |
+----+----+   +--------+---------+
     |                 |
     v                 v
 Metadata          Numerical Data
 Provenance        Statistics
 Search            Visualization
```

The MCP server exposes scientific tools dynamically to the agent. The LLM can select and combine these tools depending on the user's scientific question, allowing multi-step data interrogation rather than relying on a fixed analysis sequence.

## Current Capabilities

### DataFed Data Interrogation

The agent can:

- Search DataFed collections and scientific records
- List datasets within collections
- Retrieve experimental metadata
- Inspect DataFed records
- Trace provenance relationships between datasets

### Scientific Data Analysis

The agent can:

- Inspect numerical datasets within HDF5/NeXus files
- Discover dataset dimensions and structure
- Visualize numerical scientific data
- Calculate descriptive statistics
- Plot data distributions

This allows the agent to move from **data discovery → metadata interrogation → scientific analysis** within the same conversation.

## Example Agent Workflow

```text
User Question
      |
      v
LLM determines required information
      |
      v
Search DataFed
      |
      v
Identify relevant datasets
      |
      v
Retrieve metadata / provenance
      |
      v
Inspect scientific data
      |
      v
Run analysis / visualization
      |
      v
LLM synthesizes the result
```

Rather than implementing a separate hard-coded tool for every scientific question, the framework provides general scientific tools that the LLM can combine as needed.

## LangChain to MCP Development

The project was initially developed using **LangChain tool wrappers and LLM function calling** for scientific data and workflow operations.

The architecture was subsequently extended using the **Model Context Protocol (MCP)**, allowing tools to be exposed through a standardized server and dynamically discovered by the agent.

Both stages are retained in the repository:

- `chat_app_langchain.py` — earlier LangChain/tool-calling implementation
- `agent/langchain_orchestrator.py` — LangChain orchestration
- `chat_app.py` — current MCP-based Streamlit agent
- `mcp_servers/brave_server.py` — MCP server exposing scientific tools

## Repository Structure

```text
├── agent/                  # Agent and LangChain components
├── llm/                    # LLM-related components
├── mcp_servers/            # MCP scientific tool server
├── models/                 # Data models
├── tools/
│   ├── datafed_tool.py     # DataFed search, metadata and provenance
│   ├── scientific_tool.py  # HDF5 inspection and analysis
│   ├── langchain_tools.py  # LangChain tool wrappers
│   ├── airflows_tool.py    # Airflow interaction utilities
│   └── dash_tool.py        # Analysis dashboard utilities
├── chat_app.py             # Current MCP-based agent
├── chat_app_langchain.py   # Earlier LangChain implementation
├── config.py
└── requirements.txt
```

## Technology Stack

- **Agentic AI:** LLM function/tool calling, MCP, LangChain
- **LLM serving:** Ollama with OpenAI-compatible API
- **Scientific data:** DataFed, HDF5, NeXus
- **Scientific computing:** h5py, NumPy, pandas, Matplotlib
- **User interface:** Streamlit
- **Workflow orchestration:** Apache Airflow

## Ongoing Development

The current implementation establishes the scientific data discovery and analysis layer of a broader agentic research framework.

Ongoing work includes integration with:

- **Apache Airflow** for automated scientific data-processing and ML workflows
- **Literature RAG** for connecting experimental observations with scientific literature
- **Multimodal microscopy analysis** for comparing quantitative features across complementary imaging modalities

The longer-term goal is to enable an AI agent to coordinate **experimental data, computational workflows, quantitative analysis, and scientific literature** within a unified scientific investigation.

## Status

**Active research and development.**

Currently implemented: **LLM tool calling, MCP-based dynamic tool discovery, DataFed interrogation, HDF5/NeXus inspection, quantitative analysis, and visualization.**

Airflow orchestration, literature-RAG integration, and broader multimodal scientific reasoning are under continued development.
