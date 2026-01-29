#!/usr/bin/env python3
"""
Interactive chat with OpenAI that calls tools via MCP server.

Usage:
    python chat.py <path-to-json-file>

Example:
    python chat.py BettysResult_seismology_tools_doi_in_readme.json

The script:
1. Reads the JSON file
2. Connects to the MCP server
3. Uploads the JSON data to the server
4. Starts an interactive chat where OpenAI can call the server's tools
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

# Load environment variables
load_dotenv()


async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Chat with OpenAI using BRE repository tools via MCP server"
    )
    parser.add_argument(
        "json_file",
        type=Path,
        help="Path to the JSON data file containing repository data"
    )
    args = parser.parse_args()

    # Read the JSON file
    json_path = args.json_file
    if not json_path.exists():
        print(f"Error: File not found: {json_path}")
        sys.exit(1)

    print("=" * 60)
    print("BRE Repository Chat - Seismology Tools")
    print("=" * 60)
    print(f"Reading JSON file: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    print(f"Loaded {len(json_data)} repositories from file")
    print("Connecting to MCP server...")

    # Connect to MCP server as subprocess
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "src.bre_mcp.server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()

            # Get available tools from MCP server
            tools_response = await session.list_tools()
            mcp_tools = tools_response.tools

            print(f"Connected! {len(mcp_tools)} tools available")

            # Upload the JSON data to the server
            print("Uploading data to MCP server...")
            upload_result = await session.call_tool("upload_data", {"json_data": json_data})

            # Parse upload result
            upload_response = json.loads(upload_result.content[0].text)
            if upload_response.get("status") == "success":
                print(f"Data uploaded: {upload_response.get('repository_count')} repositories")
            else:
                print(f"Upload failed: {upload_response}")
                sys.exit(1)

            # Convert MCP tools to OpenAI format (exclude upload_data)
            openai_tools = []
            for tool in mcp_tools:
                if tool.name == "upload_data":
                    continue  # Skip upload_data - already done
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema,
                    }
                })

            # Initialize OpenAI
            client = OpenAI()
            MODEL = "gpt-4o-mini"

            print(f"\nUsing model: {MODEL}")
            print("Available tools:")
            for tool in openai_tools:
                print(f"   - {tool['function']['name']}")
            print("\nType 'quit' to exit, 'reset' to clear history")
            print("=" * 60)

            conversation = [
                {
                    "role": "system",
                    "content": f"""You are a helpful assistant for finding seismology software tools.
You have access to a database of {upload_response.get('repository_count')} GitHub repositories related to seismology.
Use the available tools to answer questions. Be concise but informative."""
                }
            ]

            while True:
                try:
                    user_input = input("\nYou: ").strip()
                except (KeyboardInterrupt, EOFError):
                    print("\nGoodbye!")
                    break

                if not user_input:
                    continue

                if user_input.lower() in ("quit", "exit"):
                    print("Goodbye!")
                    break

                if user_input.lower() == "reset":
                    conversation = [conversation[0]]
                    print("Conversation reset.")
                    continue

                # Add user message
                conversation.append({"role": "user", "content": user_input})

                # Get response from OpenAI
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=conversation,
                    tools=openai_tools,
                    tool_choice="auto"
                )

                assistant_message = response.choices[0].message

                # Handle tool calls
                if assistant_message.tool_calls:
                    print("\n🔧 Tool calls:")
                    for tc in assistant_message.tool_calls:
                        args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                        print(f"   → {tc.function.name}({json.dumps(args)})")

                    conversation.append(assistant_message)

                    # Execute each tool via MCP server
                    for tool_call in assistant_message.tool_calls:
                        func_name = tool_call.function.name
                        func_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}

                        # Call MCP server
                        result = await session.call_tool(func_name, func_args)

                        # Extract text content from MCP response
                        result_text = ""
                        for content in result.content:
                            if hasattr(content, "text"):
                                result_text = content.text
                                break

                        conversation.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result_text
                        })

                    # Get final response
                    final_response = client.chat.completions.create(
                        model=MODEL,
                        messages=conversation
                    )
                    final_message = final_response.choices[0].message
                    conversation.append(final_message)

                    print(f"\nAssistant: {final_message.content}")
                else:
                    conversation.append(assistant_message)
                    print(f"\nAssistant: {assistant_message.content}")


if __name__ == "__main__":
    asyncio.run(main())
