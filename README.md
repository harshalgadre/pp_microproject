# GitHub Repo Analyzer

A Flask web app (pure Python backend, no JS frameworks) that takes a GitHub
repo and shows:
- Repo info (description, owner, stars, license, etc.)
- Contributors, with a bar graph
- Push/commit activity per branch, as a line graph
- Full file tree of the default branch

## Deploying (Render, free tier)

1. **Push this project to GitHub** (if it isn't already):
   ```bash
   cd repo-analyzer
   git init
   git add .
   git commit -m "repo analyzer"
   git branch -M main
   git remote add origin https://github.com/<you>/repo-analyzer.git
   git push -u origin main
   ```
2. Go to **render.com** → sign up/log in with GitHub (no card needed for free tier).
3. **New +** → **Web Service** → pick your `repo-analyzer` repo.
4. Render should auto-detect the settings from `render.yaml`, or set manually:
   - **Build command**: `pip install -r requirements.txt`
   - **Start command**: `gunicorn app:app`
   - **Plan**: Free
5. Click **Create Web Service**. First deploy takes a few minutes; you'll get
   a live URL like `https://repo-analyzer-xxxx.onrender.com`.

Notes:
- Free-tier services spin down after 15 min of no traffic and take ~30–50s
  to wake back up on the next request — fine for a college demo, just don't
  be alarmed if the first load is slow.
- If GitHub rate-limits your live app (shared IPs on Render can trip this
  faster), point people to the token field on the home page.

## Setup (local)

```bash
cd repo-analyzer
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

## Usage

Enter a repo as either `owner/repo` (e.g. `psf/requests`) or a full URL
(e.g. `https://github.com/psf/requests`).

### Rate limits
GitHub allows only 60 unauthenticated API requests/hour per IP, which this
app can burn through quickly (repo info + contributors + branches + commits
per branch + file tree). If you hit "rate limit exceeded":

1. Go to GitHub → Settings → Developer settings → Personal access tokens →
   Generate new token (classic) → no scopes needed for public repos.
2. Paste it into the "Optional: GitHub token" field on the home page.
   This raises your limit to 5,000 requests/hour. The token is never
   stored — it's only used for that one request.

## Project structure

```
repo-analyzer/
├── app.py              # Flask routes + file-tree builder
├── github_service.py   # All GitHub REST API calls
├── graph_service.py    # matplotlib -> base64 PNG graphs
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── index.html
│   └── result.html
└── static/
    └── style.css
```

## How it works

- **Repo info / contributors / branches**: direct GitHub REST API calls
  (`/repos/{owner}/{repo}`, `/contributors`, `/branches`).
- **Push graph**: fetches recent commits per branch (capped at the first 5
  branches to be rate-limit friendly), buckets them by date, and plots
  commits/day per branch with matplotlib.
- **File tree**: fetches the git tree recursively
  (`/git/trees/{sha}?recursive=1`) and reshapes GitHub's flat path list
  into a nested folder structure for rendering.

## Notes for your project report

- Everything server-side is standard Python + Flask + requests + matplotlib
  — no frontend JS framework, no database.
- Graphs are rendered server-side as images (not client-side charts), which
  keeps the frontend framework-free.
- Possible extensions: cache API responses, add pagination for big repos,
  add a search/autocomplete for repo names, show commit graph per-author
  instead of per-branch.
