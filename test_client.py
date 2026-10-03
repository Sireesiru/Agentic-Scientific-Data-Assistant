import asyncio

from mcp.client.session import ClientSession
from mcp.client.stdio import (
    stdio_client,
    StdioServerParameters,
)


async def main():

    server = StdioServerParameters(
        command="python",
        args=["-m", "mcp_servers.brave_server"],
    )

    async with stdio_client(server) as (read_stream, write_stream):

        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            await session.initialize()

            # Show available MCP tools
            tools = await session.list_tools()

            print("\nREGISTERED TOOLS:")
            print([tool.name for tool in tools.tools])


            # TEST: visualize the Forward Topography dataset
            result = await session.call_tool(
            "visualize_data",{"file_path":"/home/cloud/Globus-Personal-Docker/data/BioFilm_10%_0.h5.nxs", "dataset_path": "entry/Measurement_Nexus/Channel_000/Forward _ Topography/Forward _ Topography"})
            print("\nVISUALIZATION RESULT:")
            print(result)

if __name__ == "__main__":
    asyncio.run(main())