import asyncio
import json
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_workflow():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server.py"],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Call scrape_github
            print("Step 1: Scraping 'torvalds'...")
            try:
                scrape_result = await session.call_tool("scrape_github", {"username": "torvalds"})
                github_data = scrape_result.content[0].text
                github_data_dict = json.loads(github_data)
                print("Scrape successful.")
            except Exception as e:
                print(f"FAILED Step 1: {e}")
                return

            # 2. Call analyze_profile
            print("\nStep 2: Analyzing profile...")
            try:
                analysis_result = await session.call_tool("analyze_profile", {"github_data": github_data_dict})
                analysis_data = analysis_result.content[0].text
                analysis_dict = json.loads(analysis_data)
                print("Analysis successful.")
                print(f"Theme: {analysis_dict.get('card_theme')}")
                print(f"Vibe: {analysis_dict.get('developer_vibe')}")
            except Exception as e:
                print(f"FAILED Step 2: {e}")
                return

            # 3. Generate HTML card
            print("\nStep 3: Generating HTML card...")
            try:
                card_result = await session.call_tool("generate_card_html", {
                    "username": "torvalds",
                    "github_data": github_data_dict,
                    "analysis": analysis_dict
                })
                print("HTML Generation successful.")
            except Exception as e:
                print(f"FAILED Step 3: {e}")
                return

            # 4. Save card
            print("\nStep 4: Saving card...")
            try:
                save_result = await session.call_tool("save_card", {
                    "username": "torvalds",
                    "html": card_result.content[0].text
                })
                print(f"Save successful: {save_result.content[0].text}")
            except Exception as e:
                print(f"FAILED Step 4: {e}")
                return

if __name__ == "__main__":
    asyncio.run(test_workflow())
