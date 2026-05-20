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

# Ensure static directory exists
STATIC_CARDS_DIR = os.path.join(os.path.dirname(__file__), "static", "cards")
os.makedirs(STATIC_CARDS_DIR, exist_ok=True)

# Mount static files to serve saved cards
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

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
        
        # The agent's final tool call (save_card) returns the URL.
        # We can also check if the file exists.
        card_path = os.path.join(STATIC_CARDS_DIR, f"{username}.html")
        if os.path.exists(card_path):
            with open(card_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            return {
                "username": username,
                "card_url": f"/static/cards/{username}.html",
                "html": html_content,
                "agent_response": last_text
            }
        else:
            raise HTTPException(status_code=500, detail="Agent completed but card file was not found.")
            
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
