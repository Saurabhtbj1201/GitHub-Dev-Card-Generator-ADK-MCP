from mcp.server.fastmcp import FastMCP
import httpx
import os
import json
import re
from collections import Counter
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Initialize FastMCP
mcp = FastMCP("GitHubDevCardTools")

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Accept": "application/vnd.github.v3+json"
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

@mcp.tool()
async def scrape_github(username: str) -> dict:
    """Scrape detailed GitHub profile and repository data."""
    async with httpx.AsyncClient() as client:
        # User Profile
        user_res = await client.get(f"https://api.github.com/users/{username}", headers=HEADERS)
        user_res.raise_for_status()
        user_data = user_res.json()
        
        # Repositories
        repos_res = await client.get(f"https://api.github.com/users/{username}/repos?sort=updated&per_page=100", headers=HEADERS)
        repos_res.raise_for_status()
        repos_data = repos_res.json()
        
        # Process top 6 repos
        top_6_repos = sorted(repos_data, key=lambda x: x.get("stargazers_count", 0), reverse=True)[:6]
        top_6_processed = [
            {
                "name": r["name"],
                "stars": r["stargazers_count"],
                "language": r["language"],
                "description": r["description"]
            } for r in top_6_repos
        ]
        
        # Aggregate languages
        languages = [r["language"] for r in repos_data if r["language"]]
        lang_counts = Counter(languages)
        
        return {
            "name": user_data.get("name") or username,
            "avatar_url": user_data.get("avatar_url"),
            "bio": user_data.get("bio"),
            "location": user_data.get("location"),
            "public_repos": user_data.get("public_repos"),
            "followers": user_data.get("followers"),
            "top_6_repos": top_6_processed,
            "most_used_languages": dict(lang_counts.most_common(5))
        }

@mcp.tool()
async def analyze_profile(github_data: dict) -> dict:
    """Analyze GitHub data using Gemini 2.5 Flash to create a developer persona."""
    prompt = f"""
    Analyze this GitHub data and return a JSON object representing the developer's persona.
    
    Data:
    {json.dumps(github_data, indent=2)}
    
    Return JSON with:
    - developer_vibe: 1 sentence personality.
    - top_skills: list of 3 skills.
    - fun_fact: something clever inferred from their repos.
    - card_theme: one of ["hacker", "builder", "researcher", "designer", "open-source-hero"]
    
    JSON only.
    """
    
    response = model.generate_content(prompt)
    json_match = re.search(r"\{.*\}", response.text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(0))
    return {"error": "Failed to parse Gemini response"}

@mcp.tool()
async def generate_card_html(username: str, github_data: dict, analysis: dict) -> str:
    """Generate a beautiful, self-contained HTML dev card."""
    theme = analysis.get("card_theme", "builder")
    
    themes = {
        "hacker": {"bg": "#0D0208", "text": "#00FF41", "accent": "#008F11", "card": "#151515"},
        "builder": {"bg": "#F4F7F6", "text": "#2D3436", "accent": "#0984E3", "card": "#FFFFFF"},
        "researcher": {"bg": "#2C3E50", "text": "#ECF0F1", "accent": "#E67E22", "card": "#34495E"},
        "designer": {"bg": "#FF9FF3", "text": "#2D3436", "accent": "#5F27CD", "card": "#FFFFFF"},
        "open-source-hero": {"bg": "#6C5CE7", "text": "#FFFFFF", "accent": "#FAB1A0", "card": "#A29BFE"}
    }
    
    t = themes.get(theme, themes["builder"])
    
    skills_html = "".join([f'<span class="badge" style="background: {t["accent"]};">{s}</span>' for s in analysis.get("top_skills", [])])
    repos_html = "".join([f'<div class="repo"><strong>{r["name"]}</strong> ★{r["stars"]}</div>' for r in github_data.get("top_6_repos", [])[:3]])
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ background: {t["bg"]}; color: {t["text"]}; font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }}
            .card {{ background: {t["card"]}; width: 350px; padding: 20px; border-radius: 15px; box-shadow: 0 10px 20px rgba(0,0,0,0.2); text-align: center; border: 2px solid {t["accent"]}; }}
            .avatar {{ width: 100px; height: 100px; border-radius: 50%; border: 3px solid {t["accent"]}; margin-bottom: 10px; }}
            h2 {{ margin: 10px 0 5px 0; }}
            .vibe {{ font-style: italic; margin-bottom: 15px; font-size: 0.9em; opacity: 0.8; }}
            .badges {{ display: flex; justify-content: center; gap: 5px; margin-bottom: 15px; flex-wrap: wrap; }}
            .badge {{ padding: 4px 10px; border-radius: 12px; font-size: 0.75em; color: white; }}
            .stats {{ display: flex; justify-content: space-around; font-size: 0.8em; margin-bottom: 15px; border-top: 1px solid {t["accent"]}; padding-top: 10px; }}
            .repos {{ text-align: left; font-size: 0.8em; }}
            .repo {{ margin-bottom: 5px; padding: 5px; border-radius: 4px; background: rgba(0,0,0,0.05); }}
            .fun-fact {{ font-size: 0.75em; border-top: 1px solid {t["accent"]}; margin-top: 10px; padding-top: 10px; opacity: 0.7; }}
        </style>
    </head>
    <body>
        <div class="card">
            <img src="{github_data.get('avatar_url')}" class="avatar">
            <h2>{github_data.get('name')}</h2>
            <div class="vibe">"{analysis.get('developer_vibe')}"</div>
            <div class="badges">{skills_html}</div>
            <div class="stats">
                <div><strong>{github_data.get('public_repos')}</strong><br>Repos</div>
                <div><strong>{github_data.get('followers')}</strong><br>Followers</div>
            </div>
            <div class="repos">
                <strong>Top Projects:</strong>
                {repos_html}
            </div>
            <div class="fun-fact"><strong>Fun Fact:</strong> {analysis.get('fun_fact')}</div>
        </div>
    </body>
    </html>
    """
    return html

@mcp.tool()
async def save_card(username: str, html: str) -> str:
    """Save the generated card HTML to the static directory."""
    static_dir = os.path.join(os.path.dirname(__file__), "static", "cards")
    os.makedirs(static_dir, exist_ok=True)
    
    file_path = os.path.join(static_dir, f"{username}.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    return f"/static/cards/{username}.html"

if __name__ == "__main__":
    mcp.run()
