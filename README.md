# GitHub Dev Card Generator (ADK + MCP)

Workshop project for **Google Build with AI Workshop | 16th May 2026** — *Building Personalized Agents With ADK, MCP and Memory Bank*.

Generates a “dev card” (a self‑contained HTML snippet) for any **public** GitHub username.

- **Frontend**: a single-page static site served by Nginx.
- **Backend**: FastAPI service that orchestrates an agent workflow and serves generated cards from `/static/cards/`.

## How it works (high level)

1. The frontend calls the backend: `POST /generate` with `{ "username": "..." }`.
2. The backend runs an agent workflow (Google ADK).
3. The agent uses an **MCP tool server** (started as a subprocess) that exposes tools:
   - `scrape_github` (GitHub REST API)
   - `analyze_profile` (Gemini)
   - `generate_card_html` (build HTML)
   - `save_card` (writes `backend/static/cards/<username>.html`)
4. The backend returns:
   - `card_url` (served from `/static/cards/<username>.html`)
   - `html` (the generated HTML)

## API

- `GET /health` → `{ "status": "healthy" }`
- `POST /generate` → generates a card
- `GET /card/{username}` → serves a previously generated card
- `GET /static/cards/{username}.html` → direct static URL

## Configuration

Create a `.env` in the repo root (or use the existing one locally). Start by copying `.env.example`:

```env
GOOGLE_API_KEY=...        # required for Gemini
GITHUB_TOKEN=...          # optional, improves GitHub API rate limits
```

Notes:
- Don’t commit real keys (this repo ignores `.env` via `.gitignore`).
- If you ever accidentally committed a real key, rotate it immediately.

## Run with Docker (recommended)

Prereqs: Docker Desktop.

From the repo root:

```powershell
docker compose up --build
```

Then open:
- Frontend: http://localhost/
- Backend: http://localhost:8080/health

## Run locally (Windows)

Prereqs:
- Python 3.11+ (3.12 recommended)

### 1) Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

# set env vars (or rely on repo-root .env)
# $env:GOOGLE_API_KEY = "..."
# $env:GITHUB_TOKEN = "..."

uvicorn main:app --host 0.0.0.0 --port 8080
```

Backend health check:

```powershell
Invoke-RestMethod http://localhost:8080/health
```

### 2) Frontend

The frontend HTML expects `${BACKEND_URL}` to be substituted (that happens automatically in Docker via `envsubst`).

For local development without Docker, the frontend will automatically fall back to `http://localhost:8080` when `${BACKEND_URL}` was not substituted.

Then serve it with any static server (example using Python):

```powershell
cd ..\frontend
python -m http.server 5173
```

Open http://localhost:5173

## Troubleshooting

- **403/429 from GitHub**: set `GITHUB_TOKEN` to increase rate limits.
- **Gemini failures**: verify `GOOGLE_API_KEY` is set and valid.
- **Generated cards** are written to `backend/static/cards/`.


---

## 👨💻 Developer
<div align="center">

### © Made with ❤️ by Saurabh Kumar. All Rights Reserved 2025

<!-- Profile Section with Photo and Follow Button -->
<a href="https://github.com/Saurabhtbj1201">
  <img src="https://github.com/Saurabhtbj1201.png" width="100" style="border-radius: 50%; border: 3px solid #0366d6;" alt="Saurabh Profile"/>
</a>

### [Saurabh Kumar](https://github.com/Saurabhtbj1201)

<a href="https://github.com/Saurabhtbj1201">
  <img src="https://img.shields.io/github/followers/Saurabhtbj1201?label=Follow&style=social" alt="GitHub Follow"/>
</a>

### 🔗 Connect With Me

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/saurabhtbj1201)
[![Twitter](https://img.shields.io/badge/Twitter-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white)](https://twitter.com/saurabhtbj1201)
[![Instagram](https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white)](https://instagram.com/saurabhtbj1201)
[![Facebook](https://img.shields.io/badge/Facebook-1877F2?style=for-the-badge&logo=facebook&logoColor=white)](https://facebook.com/saurabh.tbj)
[![Portfolio](https://img.shields.io/badge/Portfolio-FF5722?style=for-the-badge&logo=todoist&logoColor=white)](https://gu-saurabh.site)
[![WhatsApp](https://img.shields.io/badge/WhatsApp-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)](https://wa.me/9798024301)

---

<p align="center">

  <strong>Made with ❤️ by Saurabh Kumar</strong>
  ⭐ Star this repo if you find it helpful!
</p>

![Repo Views](https://komarev.com/ghpvc/?username=Saurabhtbj1201&style=flat-square&color=red)

</div>

---

<div align="center">

<p align="center" >
🌐 <b>View All Projects Here:</b>  
<a href="https://www.projects.gu-saurabh.site/" target="_blank"> projects.gu-saurabh.site
</a>
</p>

### 💝 If you like this project, please give it a ⭐ and share it with others!

</div>