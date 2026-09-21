"""
Thin wrapper around the GitHub REST API (v3) using `requests`.
No external SDKs — just plain HTTP calls, kept in one place so
app.py stays readable.
"""

from typing import Optional
import requests

GITHUB_API = "https://api.github.com"


class GitHubService:
    def __init__(self, token: Optional[str] = None):
        self.headers = {"Accept": "application/vnd.github+json"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    # ---------- repo basics ----------
    def get_repo_info(self, owner: str, repo: str) -> dict:
        url = f"{GITHUB_API}/repos/{owner}/{repo}"
        r = requests.get(url, headers=self.headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        return {
            "name": data.get("name"),
            "full_name": data.get("full_name"),
            "description": data.get("description") or "No description provided.",
            "owner": data.get("owner", {}).get("login"),
            "owner_avatar": data.get("owner", {}).get("avatar_url"),
            "stars": data.get("stargazers_count"),
            "forks": data.get("forks_count"),
            "watchers": data.get("subscribers_count") or data.get("watchers_count"),
            "open_issues": data.get("open_issues_count"),
            "language": data.get("language"),
            "created_at": data.get("created_at", "")[:10],
            "updated_at": data.get("updated_at", "")[:10],
            "default_branch": data.get("default_branch", "main"),
            "license": (data.get("license") or {}).get("name") or "No license",
            "html_url": data.get("html_url"),
        }

    # ---------- contributors ----------
    def get_contributors(self, owner: str, repo: str) -> list:
        url = f"{GITHUB_API}/repos/{owner}/{repo}/contributors"
        r = requests.get(url, headers=self.headers, params={"per_page": 30}, timeout=10)
        if r.status_code != 200:
            return []
        return [
            {
                "login": c.get("login"),
                "avatar_url": c.get("avatar_url"),
                "contributions": c.get("contributions", 0),
                "html_url": c.get("html_url"),
            }
            for c in r.json()
        ]

    # ---------- branches ----------
    def get_branches(self, owner: str, repo: str) -> list:
        url = f"{GITHUB_API}/repos/{owner}/{repo}/branches"
        r = requests.get(url, headers=self.headers, params={"per_page": 50}, timeout=10)
        if r.status_code != 200:
            return []
        return [b["name"] for b in r.json()]

    # ---------- commits (for the push graph) ----------
    def get_commits(self, owner: str, repo: str, branch: str, per_page=100, max_pages=2) -> list:
        commits = []
        for page in range(1, max_pages + 1):
            url = f"{GITHUB_API}/repos/{owner}/{repo}/commits"
            r = requests.get(
                url,
                headers=self.headers,
                params={"sha": branch, "per_page": per_page, "page": page},
                timeout=10,
            )
            if r.status_code != 200:
                break
            page_data = r.json()
            if not page_data:
                break
            commits.extend(page_data)
            if len(page_data) < per_page:
                break
        return commits

    # ---------- file tree ----------
    def get_tree(self, owner: str, repo: str, branch: str) -> list:
        url = f"{GITHUB_API}/repos/{owner}/{repo}/branches/{branch}"
        r = requests.get(url, headers=self.headers, timeout=10)
        r.raise_for_status()
        tree_sha = r.json()["commit"]["commit"]["tree"]["sha"]

        tree_url = f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{tree_sha}"
        r2 = requests.get(tree_url, headers=self.headers, params={"recursive": "1"}, timeout=10)
        r2.raise_for_status()
        return r2.json().get("tree", [])
