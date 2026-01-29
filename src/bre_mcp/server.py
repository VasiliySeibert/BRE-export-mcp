"""
MCP Server for BRE Export - Seismology Repository Query Tools.

This server exposes tools for querying a dataset of seismology-related
GitHub repositories through the Model Context Protocol (MCP).

Run with: python -m src.bre_mcp.server
"""

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .tools import BRETools


# Initialize the MCP server
server = Server("bre-export-mcp")

# Initialize tools (lazy loading of data)
tools = BRETools()


def format_result(result: Any) -> str:
    """Format tool result as JSON string for MCP response."""
    return json.dumps(result, indent=2, default=str)


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools with their descriptions and parameters."""
    return [
        Tool(
            name="upload_data",
            description=(
                "Upload JSON data to initialize the session. This MUST be called first "
                "before using any other tools. The data should be a list of repository "
                "objects containing fields like name, url, description, stars, readme, etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "json_data": {
                        "type": "array",
                        "description": "List of repository objects to load",
                        "items": {"type": "object"},
                    },
                },
                "required": ["json_data"],
            },
        ),
        Tool(
            name="list_repos",
            description=(
                "List all repositories in the dataset with pagination. "
                "Use this tool to get an overview of available seismology tool repositories. "
                "Returns summary information including name, description, stars, language, "
                "and whether the repository has an associated academic paper."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of repositories to return (default: 20, max: 100)",
                        "default": 20,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Number of repositories to skip for pagination (default: 0)",
                        "default": 0,
                    },
                },
            },
        ),
        Tool(
            name="get_repo_details",
            description=(
                "Get complete details for a specific repository by its name. "
                "Use this when you need full information including README content, "
                "associated paper details, citations, and all metadata. "
                "The name should match the GitHub format 'owner/repo-name'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Repository name in 'owner/repo-name' format (case-insensitive)",
                    },
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="search_by_name",
            description=(
                "Search for repositories by name using substring matching. "
                "Use this when you know part of a repository's name but not the exact full name. "
                "Performs case-insensitive substring matching."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search string to match against repository names",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="filter_by_language",
            description=(
                "Filter repositories by programming language. "
                "Use this to find repositories written in a specific language "
                "(e.g., Python, Jupyter Notebook, Fortran, MATLAB). "
                "Also returns a list of all available languages in the dataset."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "language": {
                        "type": "string",
                        "description": "Programming language to filter by (case-insensitive)",
                    },
                },
                "required": ["language"],
            },
        ),
        Tool(
            name="sort_by_stars",
            description=(
                "Get repositories sorted by GitHub star count. "
                "Use this to find the most popular (highest stars) or least popular repositories. "
                "By default returns top-starred repositories."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of repositories to return (default: 10)",
                        "default": 10,
                    },
                    "ascending": {
                        "type": "boolean",
                        "description": "If true, sort from lowest to highest stars (default: false)",
                        "default": False,
                    },
                },
            },
        ),
        Tool(
            name="sort_by_forks",
            description=(
                "Get repositories sorted by fork count. "
                "Use this to find repositories with the most (or fewest) forks, "
                "indicating community engagement and derivative work."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of repositories to return (default: 10)",
                        "default": 10,
                    },
                    "ascending": {
                        "type": "boolean",
                        "description": "If true, sort from lowest to highest forks (default: false)",
                        "default": False,
                    },
                },
            },
        ),
        Tool(
            name="get_repos_with_paper",
            description=(
                "Get all repositories that have an associated academic paper. "
                "Use this to find repositories that have been formally published "
                "or have a DOI. These are typically more rigorously documented "
                "and citable in academic work."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_repos_with_citations",
            description=(
                "Get repositories whose papers have been cited by other academic works. "
                "Use this to find high-impact tools that have been validated and "
                "referenced by the research community. Returns results sorted by citation count."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "min_citations": {
                        "type": "integer",
                        "description": "Minimum number of citations required (default: 1)",
                        "default": 1,
                    },
                },
            },
        ),
        Tool(
            name="get_repos_by_date_range",
            description=(
                "Filter repositories by creation or update date. "
                "Use this to find recent tools or tools from a specific time period. "
                "Dates should be in ISO format (e.g., '2020-01-01')."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in ISO format (e.g., '2020-01-01')",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format (e.g., '2024-12-31')",
                    },
                    "date_field": {
                        "type": "string",
                        "enum": ["createdAt", "updatedAt"],
                        "description": "Which date to filter by (default: 'createdAt')",
                        "default": "createdAt",
                    },
                },
            },
        ),
        Tool(
            name="semantic_search",
            description=(
                "Search repositories using natural language semantic search. "
                "Use this when looking for repositories based on concepts, topics, "
                "or descriptions rather than exact keywords. Searches through README "
                "content and descriptions using AI embeddings. "
                "Example queries: 'earthquake detection with machine learning', "
                "'ambient noise tomography', 'tsunami simulation'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query describing what you're looking for",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_statistics",
            description=(
                "Get statistics about the entire repository dataset. "
                "Use this to get an overview including total counts, language distribution, "
                "and paper/citation coverage."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_available_languages",
            description=(
                "Get list of all programming languages represented in the dataset. "
                "Use this to see available languages before filtering."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls from the LLM."""

    try:
        if name == "upload_data":
            result = tools.upload_data(json_data=arguments["json_data"])

        elif name == "list_repos":
            result = tools.list_repos(
                limit=arguments.get("limit", 20),
                offset=arguments.get("offset", 0),
            )

        elif name == "get_repo_details":
            result = tools.get_repo_details(name=arguments["name"])

        elif name == "search_by_name":
            result = tools.search_by_name(query=arguments["query"])

        elif name == "filter_by_language":
            result = tools.filter_by_language(language=arguments["language"])

        elif name == "sort_by_stars":
            result = tools.sort_by_stars(
                limit=arguments.get("limit", 10),
                ascending=arguments.get("ascending", False),
            )

        elif name == "sort_by_forks":
            result = tools.sort_by_forks(
                limit=arguments.get("limit", 10),
                ascending=arguments.get("ascending", False),
            )

        elif name == "get_repos_with_paper":
            result = tools.get_repos_with_paper()

        elif name == "get_repos_with_citations":
            result = tools.get_repos_with_citations(
                min_citations=arguments.get("min_citations", 1),
            )

        elif name == "get_repos_by_date_range":
            result = tools.get_repos_by_date_range(
                start_date=arguments.get("start_date"),
                end_date=arguments.get("end_date"),
                date_field=arguments.get("date_field", "createdAt"),
            )

        elif name == "semantic_search":
            result = tools.semantic_search(
                query=arguments["query"],
                limit=arguments.get("limit", 10),
            )

        elif name == "get_statistics":
            result = tools.get_statistics()

        elif name == "get_available_languages":
            result = tools.get_available_languages()

        else:
            result = {"error": f"Unknown tool: {name}"}

        return [TextContent(type="text", text=format_result(result))]

    except Exception as e:
        error_result = {
            "error": str(e),
            "tool": name,
            "arguments": arguments,
        }
        return [TextContent(type="text", text=format_result(error_result))]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
