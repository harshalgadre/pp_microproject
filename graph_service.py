"""
Builds PNG graphs (as base64 strings) with matplotlib so they can be
dropped straight into an <img src="data:image/png;base64,..."> tag —
no JS charting library needed.
"""

import io
import base64
from collections import defaultdict
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # headless, no display needed
import matplotlib.pyplot as plt


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def build_commit_activity_graph(branch_commits: dict) -> str:
    """
    branch_commits: { branch_name: [commit_json, ...] }
    One line per branch, commits-per-day.
    """
    fig, ax = plt.subplots(figsize=(9, 4.5))
    plotted_any = False

    for branch, commits in branch_commits.items():
        counts = defaultdict(int)
        for c in commits:
            try:
                date_str = c["commit"]["author"]["date"][:10]
                date = datetime.strptime(date_str, "%Y-%m-%d")
                counts[date] += 1
            except (KeyError, TypeError, ValueError):
                continue
        if not counts:
            continue
        dates = sorted(counts)
        values = [counts[d] for d in dates]
        ax.plot(dates, values, marker="o", label=branch, linewidth=1.8)
        plotted_any = True

    if not plotted_any:
        ax.text(0.5, 0.5, "No commit data available", ha="center", va="center")

    ax.set_title("Commits per day, by branch")
    ax.set_xlabel("Date")
    ax.set_ylabel("Commits")
    if plotted_any:
        ax.legend(loc="upper left", fontsize=8)
    ax.grid(alpha=0.3)
    fig.autofmt_xdate()

    return _fig_to_base64(fig)


def build_contributors_bar_graph(contributors: list) -> str:
    fig, ax = plt.subplots(figsize=(9, 4.5))
    top = contributors[:15]
    names = [c["login"] for c in top][::-1]
    counts = [c["contributions"] for c in top][::-1]
    ax.barh(names, counts, color="#4f8cff")
    ax.set_xlabel("Contributions")
    ax.set_title("Top contributors")
    fig.tight_layout()

    return _fig_to_base64(fig)
