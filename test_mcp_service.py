#!/usr/bin/env python3
"""
MCP Service Test Script
"""

import os
from backend.service.mcp_server_service import MCPServerService


def test_mcp_service():
    """Test the extraction of tools and resources from the MCP service."""

    # GitHub repositories to test (actual MCP servers)
    test_repos = [
        "https://github.com/modelcontextprotocol/server-filesystem",
        "https://github.com/modelcontextprotocol/server-git",
        "https://github.com/modelcontextprotocol/server-http",
        "https://github.com/modelcontextprotocol/server-ollama",
    ]

    print("=== Starting MCP Service Test ===\n")

    # Check if GitHub token is set
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        print("✅ GitHub token is set.")
    else:
        print("⚠️  GitHub token is not set. API rate limits may apply.")

    # Create MCP service instance
    mcp_service = MCPServerService(github_token)

    for repo_url in test_repos:
        print(f"🔍 Testing: {repo_url}")

        try:
            # Test tool extraction
            print("📋 Extracting tools...")
            tools = mcp_service.read_mcp_server_tool_list(repo_url)
            print(f"   Tools found: {len(tools)}")
            for i, tool in enumerate(tools[:5], 1):  # Print only the first 5
                print(
                    f"   {i}. {tool.get('name', 'Unknown')} - {tool.get('description', 'No description')[:50]}..."
                )
            if len(tools) > 5:
                print(f"   ... and {len(tools) - 5} more")

            # Test resource extraction
            print("📁 Extracting resources...")
            resources = mcp_service.read_mcp_server_resource_list(repo_url)
            print(f"   Resources found: {len(resources)}")
            for i, resource in enumerate(resources[:5], 1):  # Print only the first 5
                print(
                    f"   {i}. {resource.get('name', 'Unknown')} - {resource.get('url', 'No URL')}"
                )
            if len(resources) > 5:
                print(f"   ... and {len(resources) - 5} more")

        except Exception as e:
            print(f"   ❌ Error occurred: {str(e)}")

        print("-" * 50)


if __name__ == "__main__":
    test_mcp_service()
