from mcp.server.fastmcp import FastMCP
from tools.datafed_tool import DataFedTool
from tools.scientific_tool import ScientificTool

science = ScientificTool()


mcp = FastMCP("BRaVE DataFed")
df = DataFedTool()


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
    without downloading the underlying raw data.
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
    count: int = 20):
    """
    Search DataFed records using natural text.

    collection_id can optionally restrict the search
    to a particular DataFed collection.
    """
    return df.search_records(
        query=query,
        collection_id=collection_id,
        count=count
    )
    
@mcp.tool()
def inspect_h5_datasets(file_path: str):
    """Discover numerical datasets inside an HDF5/NXS file."""
    return science.inspect_h5_datasets(file_path)


@mcp.tool()
def visualize_data(file_path: str, dataset_path: str):
    """Visualize a numerical scientific dataset."""
    return science.visualize_data(file_path, dataset_path)
    
    
@mcp.tool()
def plot_distribution(file_path: str, dataset_path: str,bins: int = 50):
    """
    Plot the value distribution of a numerical scientific dataset
    and return basic descriptive statistics.
    """
    return science.plot_distribution(
        file_path=file_path,
        dataset_path=dataset_path,
        bins=bins)

if __name__ == "__main__":
    mcp.run()