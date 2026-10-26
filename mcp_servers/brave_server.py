from pathlib import Path
import requests

from mcp.server.fastmcp import FastMCP

from tools.datafed_tool import DataFedTool
from tools.scientific_tool import ScientificTool


# ============================================================
# INITIALIZATION
# ============================================================

mcp = FastMCP("BRaVE DataFed")

df = DataFedTool()
science = ScientificTool()


# ============================================================
# DATAFED TOOLS
# ============================================================

@mcp.tool()
def list_collection(collection_id: str):
    """
    List datasets contained in a DataFed collection.

    Args:
        collection_id:
            DataFed collection ID, for example c/525611319.
    """
    return df.list_collection(collection_id)


@mcp.tool()
def get_metadata(data_id: str):
    """
    Return all metadata available in DataFed for a record.

    The metadata structure is not assumed in advance and may differ
    between instrument/file types.
    """
    return df.get_metadata(data_id)


@mcp.tool()
def get_provenance(data_id: str):
    """
    Return provenance relationships for a DataFed record.

    Shows how this record is related to other DataFed records,
    including derived-from, component-of, and version relationships.
    """
    return df.get_provenance(data_id)


@mcp.tool()
def inspect_record(data_id: str):
    """
    Inspect all information available from the DataFed record
    without downloading the underlying scientific data.
    """
    return df.inspect_record(data_id)


@mcp.tool()
def search_collections(query: str):
    """
    Recursively search DataFed collections and subcollections
    using a case-insensitive partial title match.
    """
    return df.search_collections(query)


@mcp.tool()
def search_records(
    query: str,
    collection_id: str | None = None,
    count: int = 20,
):
    """
    Discover candidate DataFed records using natural-language text search.

    Use this tool only to locate candidate record IDs and titles.
    After suitable candidate records are returned, STOP searching and
    use get_metadata, inspect_record, or inspect_h5_datasets on those
    record IDs to investigate the actual experimental data.

    Do not repeatedly call search_records with similar queries when
    candidate records have already been found.

    For tasks comparing modalities such as AFM and cryo-EM, search for
    candidate records for each modality, select appropriate records,
    then inspect those records before deciding which measurements or
    features can be compared.

    collection_id can optionally restrict the search to a particular
    DataFed collection.
    """
    return df.search_records(
        query=query,
        collection_id=collection_id,
        count=count,
    )


# ============================================================
# SCIENTIFIC DATA TOOLS
# ============================================================

@mcp.tool()
def inspect_h5_datasets(data_id: str):
    """
    Inspect numerical datasets inside an HDF5/NXS DataFed record.

    The tool resolves the DataFed record ID to an accessible local
    scientific file before inspecting the HDF5 structure.

    If the original file is still accessible through the local
    Microflows Globus staging mount, it is used directly.

    Otherwise the resolver attempts to retrieve the record from
    DataFed temporarily.

    Returns HDF5 dataset paths, shapes, dimensionality, and data types.
    """

    result = df.resolve_record_file(data_id)
    file_path = result["local_path"]

    try:
        return science.inspect_h5_datasets(
            file_path
        )

    finally:
        # Never delete an existing staging/source file.
        # Delete only files retrieved temporarily from DataFed.
        if result.get("temporary", False):
            path = Path(file_path)

            if path.exists():
                path.unlink()


@mcp.tool()
def visualize_data(
    data_id: str,
    dataset_path: str,
):
    """
    Visualize an actual numerical dataset contained in a DataFed
    HDF5/NXS record.

    Args:
        data_id:
            DataFed record ID, for example d/525697641.

        dataset_path:
            Exact internal HDF5 dataset path discovered using
            inspect_h5_datasets.

    Returns information about the dataset and the path of the
    generated visualization.
    """

    result = df.resolve_record_file(data_id)
    file_path = result["local_path"]

    try:
        return science.visualize_data(
            file_path=file_path,
            dataset_path=dataset_path,
        )

    finally:
        # Delete only temporary DataFed retrievals.
        if result.get("temporary", False):
            path = Path(file_path)

            if path.exists():
                path.unlink()


@mcp.tool()
def plot_distribution(
    data_id: str,
    dataset_path: str,
    bins: int = 50,
):
    """
    Plot the value distribution of an actual numerical dataset
    contained in a DataFed HDF5/NXS record and return descriptive
    statistics calculated from that dataset.

    Args:
        data_id:
            DataFed record ID, for example d/525697641.

        dataset_path:
            Exact internal HDF5 dataset path discovered using
            inspect_h5_datasets.

        bins:
            Number of histogram bins. Default is 50.

    Returns statistics calculated by the analysis tool together
    with the path of the generated distribution plot.
    """

    result = df.resolve_record_file(data_id)
    file_path = result["local_path"]

    try:
        return science.plot_distribution(
            file_path=file_path,
            dataset_path=dataset_path,
            bins=bins,
        )

    finally:
        # Delete only temporary DataFed retrievals.
        if result.get("temporary", False):
            path = Path(file_path)

            if path.exists():
                path.unlink()

@mcp.tool()
def compare_datasets(
    data_id_a: str,
    dataset_path_a: str,
    data_id_b: str,
    dataset_path_b: str,
):
    """
    Compare two numerical datasets using pixel-wise quantitative analysis.

    The datasets may belong to the same DataFed record or to two
    different DataFed records.

    Use this tool when corresponding array positions have scientific
    meaning and a pixel-wise comparison is appropriate.

    Returns descriptive statistics and, when array shapes match:
    mean difference, mean absolute difference, RMSE, Pearson correlation,
    and difference maps for 2D arrays.

    Do not use pixel-wise metrics merely because two arrays have the same
    shape. Their measurements and spatial correspondence must also be
    scientifically meaningful.
    """

    result_a = df.resolve_record_file(data_id_a)

    # Avoid resolving/downloading the same DataFed record twice.
    same_record = data_id_a == data_id_b

    if same_record:
        result_b = result_a
    else:
        result_b = df.resolve_record_file(data_id_b)

    file_path_a = result_a["local_path"]
    file_path_b = result_b["local_path"]

    try:
        return science.compare_datasets(
            file_path_a=file_path_a,
            dataset_path_a=dataset_path_a,
            file_path_b=file_path_b,
            dataset_path_b=dataset_path_b,
        )

    finally:
        # Only delete files that were temporary downloads.
        # Never delete existing local source files.

        paths_to_delete = set()

        if result_a.get("temporary", False):
            paths_to_delete.add(file_path_a)

        if result_b.get("temporary", False):
            paths_to_delete.add(file_path_b)

        for file_path in paths_to_delete:
            path = Path(file_path)

            if path.exists():
                path.unlink()
                
@mcp.tool()
def compare_distributions(
    data_id_a: str,
    dataset_path_a: str,
    data_id_b: str,
    dataset_path_b: str,
):
    """
    Compare the numerical value distributions of two experimental datasets.

    The datasets may belong to the same DataFed record or to different
    DataFed records.

    Use this tool when comparing independent experimental images or
    measurements where pixel-to-pixel spatial correspondence is not
    required or is not scientifically meaningful.

    Returns descriptive statistics, differences in mean and median,
    a two-sample Kolmogorov-Smirnov statistic and p-value, and an
    overlaid normalized distribution plot.

    This tool does not establish biological or physical causation.
    Interpret distribution differences in the context of the measurement,
    units, experimental conditions, and metadata.
    """

    result_a = df.resolve_record_file(data_id_a)

    same_record = data_id_a == data_id_b

    if same_record:
        result_b = result_a
    else:
        result_b = df.resolve_record_file(data_id_b)

    file_path_a = result_a["local_path"]
    file_path_b = result_b["local_path"]

    try:
        return science.compare_distributions(
            file_path_a=file_path_a,
            dataset_path_a=dataset_path_a,
            file_path_b=file_path_b,
            dataset_path_b=dataset_path_b,
        )

    finally:
        paths_to_delete = set()

        if result_a.get("temporary", False):
            paths_to_delete.add(file_path_a)

        if result_b.get("temporary", False):
            paths_to_delete.add(file_path_b)

        for file_path in paths_to_delete:
            path = Path(file_path)

            if path.exists():
                path.unlink()

# ============================================================
# SCIENTIFIC LITERATURE RAG
# ============================================================

RAG_SERVICE_URL = "http://10.64.194.121:8003"


@mcp.tool()
def search_scientific_literature(
    question: str,
    data_context: str = "",
    top_k: int = 3,
) -> dict:
    """
    Search scientific literature relevant to an experimental
    dataset, analysis question, or scientific interpretation.

    Use this tool after inspecting the relevant DataFed records
    when literature evidence would help determine:

    - what quantitative analyses are scientifically appropriate,
    - how experimental measurements should be interpreted,
    - what limitations or confounding factors should be considered,
    - or what analysis or experiment should be performed next.

    The data_context should describe relevant information already
    discovered from DataFed, such as modality, sample, channels,
    dimensions, metadata, experimental conditions, or previous
    analysis results.

    Do not use this tool as a replacement for inspecting the
    actual DataFed data.
    """

    payload = {
        "question": question,
        "data_context": data_context,
        "top_k": top_k,
    }

    try:
        response = requests.post(
            f"{RAG_SERVICE_URL}/retrieve",
            json=payload,
            timeout=180,
        )

        response.raise_for_status()

        result = response.json()

        return {
            "status": "success",
            "question": question,
            "literature_results": result.get(
                "results",
                [],
            ),
        }

    except requests.RequestException as error:
        return {
            "status": "error",
            "message": (
                "Scientific literature RAG service "
                f"could not be reached: {error}"
            ),
        }


# ============================================================
# START MCP SERVER
# ============================================================

if __name__ == "__main__":
    mcp.run()