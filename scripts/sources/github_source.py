import logging
import os
from datetime import UTC, datetime
from typing import Any

from scripts.utils.http_client import get_json

logger = logging.getLogger(__name__)

BASE_URL = "https://api.github.com"


def _auth_headers() -> dict[str, str]:
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


async def fetch_github_metrics(repo: str, previous: dict | None = None) -> dict[str, Any] | None:
    headers = _auth_headers()
    fetched_at = datetime.now(UTC).isoformat()

    repo_data = await get_json(f"{BASE_URL}/repos/{repo}", headers=headers)
    if repo_data is None:
        return None

    commits_data = await get_json(
        f"{BASE_URL}/repos/{repo}/commits",
        headers=headers,
        params={"per_page": 1},
    )

    last_commit_days_ago = None
    if commits_data and isinstance(commits_data, list) and len(commits_data) > 0:
        commit_date_str = commits_data[0].get("commit", {}).get("committer", {}).get("date")
        if commit_date_str:
            commit_date = datetime.fromisoformat(commit_date_str.replace("Z", "+00:00"))
            delta = datetime.now(UTC) - commit_date
            last_commit_days_ago = delta.days

    stars = repo_data.get("stargazers_count", 0)
    stars_delta_30d = None
    if previous and previous.get("stars") is not None:
        stars_delta_30d = stars - previous["stars"]

    return {
        "stars": stars,
        "stars_delta_30d": stars_delta_30d,
        "open_issues": repo_data.get("open_issues_count", 0),
        "last_commit_days_ago": last_commit_days_ago,
        "forks": repo_data.get("forks_count", 0),
        "archived": repo_data.get("archived", False),
        "fetched_at": fetched_at,
    }
