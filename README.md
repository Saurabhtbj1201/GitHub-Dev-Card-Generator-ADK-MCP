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

## Title + Description (for GitHub)

**Title**: GitHub Dev Card Generator (ADK + MCP)

**Description**: A workshop project that builds a personalized GitHub “dev card” using Google ADK agents + an MCP tool server. The backend scrapes GitHub, uses Gemini to infer a developer persona, generates a themed HTML card, saves it, and serves shareable URLs.

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

For local development without Docker, simplest option is to hard-code the backend URL:
- edit `frontend/index.html` and replace `${BACKEND_URL}` with `http://localhost:8080`

Then serve it with any static server (example using Python):

```powershell
cd ..\frontend
python -m http.server 5173
```

Open http://localhost:5173

## Push to GitHub (first time)

From the repo root:

```powershell
git init
git add .
git commit -m "Initial workshop project"
git branch -M main

# Create an empty repo on GitHub, then:
git remote add origin https://github.com/<YOU>/<REPO>.git
git push -u origin main
```

Note: `.env` is ignored by `.gitignore`.

## Troubleshooting

- **403/429 from GitHub**: set `GITHUB_TOKEN` to increase rate limits.
- **Gemini failures**: verify `GOOGLE_API_KEY` is set and valid.
- **Generated cards** are written to `backend/static/cards/`.

## Deploy to Google Cloud (Cloud Shell → Cloud Run)

This deploys **two Cloud Run services**:
- `github-card-backend` (FastAPI on port 8080)
- `github-card-frontend` (Nginx on port 80)

### 0) Open Cloud Shell

In Google Cloud Console, open **Cloud Shell** and clone your repo:

```bash
git clone <YOUR_GITHUB_REPO_URL>
cd github-card-generator
```

### 1) Set variables

```bash
PROJECT_ID="$(gcloud config get-value project)"
REGION="us-central1"
AR_REPO="github-card-generator"
```

Optional: set your project explicitly:

```bash
# gcloud config set project YOUR_PROJECT_ID
```

### 2) Enable required services

```bash
gcloud services enable \
   run.googleapis.com \
   cloudbuild.googleapis.com \
   artifactregistry.googleapis.com \
   secretmanager.googleapis.com
```

### 3) Create Artifact Registry (Docker)

```bash
gcloud artifacts repositories create "$AR_REPO" \
   --repository-format=docker \
   --location="$REGION" \
   --description="Images for github-card-generator" \
   || true
```

### 4) Store secrets in Secret Manager (recommended)

```bash
# Paste your keys when prompted
read -s -p "GOOGLE_API_KEY: " GOOGLE_API_KEY; echo
read -s -p "GITHUB_TOKEN (optional, press Enter to skip): " GITHUB_TOKEN; echo

echo -n "$GOOGLE_API_KEY" | gcloud secrets create GOOGLE_API_KEY --data-file=- 2>/dev/null \
   || echo -n "$GOOGLE_API_KEY" | gcloud secrets versions add GOOGLE_API_KEY --data-file=-

if [ -n "$GITHUB_TOKEN" ]; then
   echo -n "$GITHUB_TOKEN" | gcloud secrets create GITHUB_TOKEN --data-file=- 2>/dev/null \
      || echo -n "$GITHUB_TOKEN" | gcloud secrets versions add GITHUB_TOKEN --data-file=-
fi
```

### 5) Build + deploy backend

```bash
BACKEND_IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO/backend:1"

gcloud builds submit backend --tag "$BACKEND_IMAGE"

gcloud run deploy github-card-backend \
   --image "$BACKEND_IMAGE" \
   --region "$REGION" \
   --allow-unauthenticated \
   --port 8080 \
   --set-secrets GOOGLE_API_KEY=GOOGLE_API_KEY:latest \
   $( [ -n "$GITHUB_TOKEN" ] && echo "--set-secrets GITHUB_TOKEN=GITHUB_TOKEN:latest" )

BACKEND_URL="$(gcloud run services describe github-card-backend --region "$REGION" --format='value(status.url)')"
echo "Backend URL: $BACKEND_URL"
```

Sanity check:

```bash
curl -s "$BACKEND_URL/health"; echo
```

### 6) Build + deploy frontend (wired to backend URL)

```bash
FRONTEND_IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO/frontend:1"

gcloud builds submit frontend --tag "$FRONTEND_IMAGE"

gcloud run deploy github-card-frontend \
   --image "$FRONTEND_IMAGE" \
   --region "$REGION" \
   --allow-unauthenticated \
   --port 80 \
   --set-env-vars BACKEND_URL="$BACKEND_URL"

FRONTEND_URL="$(gcloud run services describe github-card-frontend --region "$REGION" --format='value(status.url)')"
echo "Frontend URL: $FRONTEND_URL"
```

Open `FRONTEND_URL`, type a GitHub username (e.g. `torvalds`), and generate a card.

### Notes

- For a quick workshop deploy you *can* skip Secret Manager and use `--set-env-vars GOOGLE_API_KEY=...`, but Secret Manager is safer.
- GitHub API calls will work without `GITHUB_TOKEN` but may hit rate limits faster.
