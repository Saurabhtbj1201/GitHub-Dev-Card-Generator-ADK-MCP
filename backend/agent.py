import os
import sys
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams, StdioServerParameters

# Path to the MCP server script
mcp_server_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "mcp_server.py"))

# Configure connection to the MCP server
connection_params = StdioConnectionParams(
    server_params=StdioServerParameters(
        command=sys.executable,
        args=[mcp_server_path]
    )
)

# Initialize the MCP Toolset
mcp_toolset = McpToolset(connection_params=connection_params)

# Define the ADK Agent
github_card_agent = Agent(
    name="github_card_agent",
    model=Gemini(model="gemini-2.5-flash"),
    instruction="""
    You are a GitHub profile analyst and dev card generator. 
    When a user gives you a GitHub username, you ALWAYS follow this exact sequence: 
    1. first call scrape_github
    2. then analyze_profile with the result
    3. then generate_card_html with all three inputs (username, github_data, and analysis)
    4. then save_card. 
    Never skip steps. Be enthusiastic about developers' work. 
    If the profile is private or doesn't exist, say so clearly.
    """,
    tools=[mcp_toolset]
)
