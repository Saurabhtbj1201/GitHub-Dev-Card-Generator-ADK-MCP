import os
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

from contextlib import aclosing
from google.genai import types

# ADK Imports
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService

# Local imports
from agent import github_card_agent
from mcp_server import scrape_github, analyze_profile, generate_card_html, save_card

app = FastAPI(title="GitHub Dev Card Generator")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Services
session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()

# Create Runner
runner = Runner(
    app_name="github-card_generator",
    agent=github_card_agent,
    session_service=session_service,
    memory_service=memory_service,
    auto_create_session=True,
)

def _cards_dir() -> str:
    override = os.getenv("CARDS_DIR")
    if override:
        return override

    # Cloud Run services commonly run with a read-only app filesystem; /tmp is always writable.
    if os.getenv("K_SERVICE"):
        return os.path.join(os.sep, "tmp", "cards")

    return os.path.join(os.path.dirname(__file__), "static", "cards")


STATIC_CARDS_DIR = _cards_dir()
os.makedirs(STATIC_CARDS_DIR, exist_ok=True)

# Mount static files to serve saved cards
app.mount("/static/cards", StaticFiles(directory=STATIC_CARDS_DIR), name="cards")

class GenerateRequest(BaseModel):
    username: str

@app.post("/generate")
async def generate_card(request: GenerateRequest):
    """
    Triggers the agent to generate a dev card for the given username.
    """
    username = request.username
    session_id = f"session_{username}"
    
    try:
        message = f"Generate a dev card for {username}"
        last_text: str = ""
        async with aclosing(
            runner.run_async(
                user_id=username,
                session_id=session_id,
                new_message=types.Content(role="user", parts=[types.Part(text=message)]),
            )
        ) as agen:
            async for event in agen:
                if event.content and event.content.parts:
                    text = "".join(part.text or "" for part in event.content.parts)
                    if text.strip():
                        last_text = text

        card_path = os.path.join(STATIC_CARDS_DIR, f"{username}.html")

        # Fallback: if the agent doesn't end up calling save_card (tooling can be flaky in some deployments),
        # run the tool pipeline deterministically to ensure the card exists.
        if not os.path.exists(card_path):
            github_data = await scrape_github(username)
            analysis = await analyze_profile(github_data)
            html = await generate_card_html(username, github_data, analysis)
            await save_card(username, html)
        
        if os.path.exists(card_path):
            with open(card_path, "r", encoding="utf-8") as f:
                html_content = f.read()

            return {
                "username": username,
                "card_url": f"/static/cards/{username}.html",
                "html": html_content,
                "agent_response": last_text,
            }

        raise HTTPException(
            status_code=500,
            detail="Card file was not created. Check GOOGLE_API_KEY/GITHUB_TOKEN and Cloud Run filesystem settings.",
        )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/card/{username}")
async def serve_card(username: str):
    """
    Serves a previously generated card.
    """
    file_path = os.path.join(STATIC_CARDS_DIR, f"{username}.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Card not found. Generate it first!")

@app.get("/health")
def health_check():
    """
    Health check for Cloud Run.
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
