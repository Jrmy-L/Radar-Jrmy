#!/usr/bin/env python3
"""Point d'entrée principal pour la collecte des métriques."""

import asyncio
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv

from scripts.sources.cncf_source import fetch_cncf_metrics
from scripts.sources.github_source import fetch_github_metrics
from scripts.sources.npm_source import fetch_npm_metrics
from scripts.sources.pypi_source import fetch_pypi_metrics
from scripts.utils.position_proposal import propose_position

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("collect")

ROOT = Path(__file__).parent.parent
DATA_FILE = ROOT / "data" / "data.json"
TECH_FILE = ROOT / "technologies.yaml"


def load_technologies() -> list[dict]:
    with TECH_FILE.open(encoding="utf-8") as f:
        return yaml.safe_load(f)["technologies"]


def load_previous_data() -> dict[str, dict]:
    if not DATA_FILE.exists():
        return {}
    with DATA_FILE.open(encoding="utf-8") as f:
        data = json.load(f)
    return {t["id"]: t for t in data.get("technologies", [])}


def compute_trajectory(current_metrics: dict, prev_tech: dict | None) -> str:
    if prev_tech is None:
        return "stable"

    prev_metrics = prev_tech.get("metrics", {})
    prev_github = prev_metrics.get("github", {})
    curr_github = current_metrics.get("github", {})

    if curr_github and prev_github:
        prev_stars = prev_github.get("stars", 0)
        curr_stars = curr_github.get("stars", 0)
        if prev_stars > 0:
            pct = (curr_stars - prev_stars) / prev_stars * 100
            if pct >= 1.0:
                return "rising"
            if pct <= -1.0:
                return "declining"
        stars_delta = curr_github.get("stars_delta_30d")
        if stars_delta is not None:
            if stars_delta > 500:
                return "rising"
            if stars_delta < -500:
                return "declining"

    prev_npm = prev_metrics.get("npm", {})
    curr_npm = current_metrics.get("npm", {})
    if curr_npm and prev_npm:
        delta_pct = curr_npm.get("downloads_delta_pct")
        if delta_pct is not None:
            if delta_pct >= 5.0:
                return "rising"
            if delta_pct <= -5.0:
                return "declining"

    return "stable"


async def collect_technology(tech: dict, prev_tech: dict | None) -> dict:
    sources = tech.get("sources") or {}
    prev_metrics = (prev_tech or {}).get("metrics", {})
    metrics = {}

    tasks = {}
    if sources.get("github"):
        tasks["github"] = fetch_github_metrics(sources["github"], prev_metrics.get("github"))
    if sources.get("npm_package"):
        tasks["npm"] = fetch_npm_metrics(sources["npm_package"], prev_metrics.get("npm"))
    if sources.get("pypi_package"):
        tasks["pypi"] = fetch_pypi_metrics(sources["pypi_package"], prev_metrics.get("pypi"))
    if sources.get("cncf"):
        tasks["cncf"] = fetch_cncf_metrics(tech["name"])

    if tasks:
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        for key, result in zip(tasks.keys(), results, strict=True):
            if isinstance(result, Exception):
                logger.warning("Source %s failed for %s: %s", key, tech["id"], result)
            elif result is not None:
                metrics[key] = result

    trajectory = compute_trajectory(metrics, prev_tech)
    position_proposal = propose_position(tech, trajectory, metrics)
    collected_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not tasks:
        collection_status = "no_source"
    elif not metrics:
        collection_status = "failed"
    elif len(metrics) < len(tasks):
        collection_status = "partial"
    else:
        collection_status = "complete"

    return {
        "id": tech["id"],
        "name": tech["name"],
        "category": tech["category"],
        "position": tech["position"],
        "since": tech.get("since"),
        "switching_cost": tech.get("switching_cost"),
        "experience": tech.get("experience", "unassessed"),
        "evidence": tech.get("evidence", []),
        "notes": tech.get("notes"),
        "pros": tech.get("pros", []),
        "cons": tech.get("cons", []),
        "use_cases": tech.get("use_cases", []),
        "metrics": metrics,
        "trajectory": trajectory,
        "position_proposal": position_proposal,
        "collected_at": collected_at,
        "collection_status": collection_status,
    }


async def main() -> int:
    logger.info("Starting metrics collection")
    technologies = load_technologies()
    previous_data = load_previous_data()
    logger.info("Loaded %d technologies", len(technologies))

    collect_tasks = [
        collect_technology(tech, previous_data.get(tech["id"])) for tech in technologies
    ]
    results = await asyncio.gather(*collect_tasks, return_exceptions=True)

    collected = []
    failed = 0
    for tech, result in zip(technologies, results, strict=True):
        if isinstance(result, Exception):
            logger.error("Failed to collect %s: %s", tech["id"], result)
            failed += 1
        else:
            collected.append(result)
            source_count = len(result.get("metrics", {}))
            logger.info(
                "Collected %s — %d sources, trajectory=%s",
                tech["id"],
                source_count,
                result["trajectory"],
            )

    total = len(technologies)
    failure_rate = failed / total if total > 0 else 0
    logger.info(
        "Collection complete: %d/%d succeeded (%.0f%% failure)",
        total - failed,
        total,
        failure_rate * 100,
    )

    output = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_version": "1.2",
        "technologies": collected,
    }

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    logger.info("Written %s", DATA_FILE)

    if failure_rate > 0.5:
        logger.error("More than 50%% of sources failed — exiting with error")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
