from flask import Flask, render_template, request, flash, redirect, url_for

from github_service import GitHubService
from graph_service import build_commit_activity_graph, build_contributors_bar_graph

app = Flask(__name__)
app.secret_key = "dev-secret-change-me"  # only needed for flash messages


def parse_repo_input(text: str):
    """Accepts 'owner/repo' or a full https://github.com/owner/repo URL."""
    text = text.strip().rstrip("/")
    if text.startswith("http"):
        parts = text.split("/")
        owner, repo = parts[-2], parts[-1]
    else:
        owner, repo = text.split("/")
    return owner, repo.replace(".git", "")


def build_file_tree(flat_tree: list) -> dict:
    """
    GitHub's git-trees API returns a flat list of {path, type, ...}.
    Turn that into a nested dict so the template can render folders.
    Folders become nested dicts; a special '__files__' key holds
    the filenames directly inside that folder.
    """
    root: dict = {}
    for item in flat_tree:
        if item.get("type") not in ("blob", "tree"):
            continue
        parts = item["path"].split("/")
        node = root
        for i, part in enumerate(parts):
            is_last = i == len(parts) - 1
            if is_last and item["type"] == "blob":
                node.setdefault("__files__", []).append(part)
            else:
                node = node.setdefault(part, {})
    return root


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    repo_input = request.form.get("repo_url", "")
    token = request.form.get("token", "").strip() or None

    try:
        owner, repo = parse_repo_input(repo_input)
    except Exception:
        flash("Couldn't parse that. Use 'owner/repo' or a full github.com URL.")
        return redirect(url_for("index"))

    gh = GitHubService(token=token)

    try:
        info = gh.get_repo_info(owner, repo)
    except Exception as e:
        msg = str(e)
        if "403" in msg:
            flash("GitHub API rate limit hit. Add a personal access token below to fix this.")
        elif "404" in msg:
            flash("Repo not found. Check the owner/repo spelling.")
        else:
            flash(f"Couldn't reach GitHub: {e}")
        return redirect(url_for("index"))

    contributors = gh.get_contributors(owner, repo)
    branches = gh.get_branches(owner, repo)

    # cap to first 5 branches so we don't blow the unauthenticated rate limit
    branches_for_graph = branches[:5]
    branch_commits = {}
    for b in branches_for_graph:
        branch_commits[b] = gh.get_commits(owner, repo, b)

    commit_graph = build_commit_activity_graph(branch_commits)
    contributor_graph = build_contributors_bar_graph(contributors) if contributors else None

    try:
        flat_tree = gh.get_tree(owner, repo, info["default_branch"])
        file_tree = build_file_tree(flat_tree)
    except Exception:
        file_tree = {}

    return render_template(
        "result.html",
        info=info,
        contributors=contributors,
        branches=branches,
        branch_commit_counts={b: len(c) for b, c in branch_commits.items()},
        commit_graph=commit_graph,
        contributor_graph=contributor_graph,
        file_tree=file_tree,
    )


if __name__ == "__main__":
    app.run(debug=True)
