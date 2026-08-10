#!/usr/bin/env python3
"""Valide le schéma de technologies.yaml."""

import re
import sys
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
TECH_FILE = ROOT / "technologies.yaml"

VALID_POSITIONS = {"adopt", "trial", "assess", "hold"}
VALID_CATEGORIES = {
    "languages",
    "frameworks_front",
    "frameworks_back",
    "mobile",
    "databases",
    "devops",
    "observability",
    "security",
    "messaging",
    "ai",
}
VALID_SWITCHING_COSTS = {"low", "medium", "high"}
VALID_EXPERIENCE_LEVELS = {
    "unassessed",
    "observed",
    "studied",
    "practiced",
    "delivered",
    "operated",
}
REQUIRED_FIELDS = {"id", "name", "category", "position"}
VALID_SOURCE_FIELDS = {"github", "npm_package", "pypi_package", "cncf"}
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
EXPECTED_TECHNOLOGIES_PER_CATEGORY = 10


def validate(tech_file: Path = TECH_FILE) -> list[str]:
    with tech_file.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    errors = []
    if not isinstance(data, dict):
        return ["racine YAML invalide : un objet est attendu"]

    technologies = data.get("technologies")
    if not isinstance(technologies, list):
        return ["'technologies' doit être une liste"]

    ids_seen = set()

    for i, tech in enumerate(technologies):
        if not isinstance(tech, dict):
            errors.append(f"[{i}]: une technologie doit être un objet")
            continue

        prefix = f"[{i}] {tech.get('name', '???')}"

        for field in REQUIRED_FIELDS:
            if field not in tech:
                errors.append(f"{prefix}: champ requis manquant '{field}'")

        tech_id = tech.get("id")
        if tech_id:
            if not isinstance(tech_id, str) or not ID_PATTERN.fullmatch(tech_id):
                errors.append(f"{prefix}: id invalide (format kebab-case attendu)")
            if tech_id in ids_seen:
                errors.append(f"{prefix}: id dupliqué '{tech_id}'")
            ids_seen.add(tech_id)

        name = tech.get("name")
        if name is not None and (not isinstance(name, str) or not name.strip()):
            errors.append(f"{prefix}: name doit être une chaîne non vide")

        if tech.get("position") and tech["position"] not in VALID_POSITIONS:
            errors.append(
                f"{prefix}: position invalide '{tech['position']}' (valeurs: {VALID_POSITIONS})"
            )

        if tech.get("category") and tech["category"] not in VALID_CATEGORIES:
            errors.append(
                f"{prefix}: catégorie invalide '{tech['category']}' (valeurs: {VALID_CATEGORIES})"
            )

        if tech.get("switching_cost") and tech["switching_cost"] not in VALID_SWITCHING_COSTS:
            errors.append(f"{prefix}: switching_cost invalide '{tech['switching_cost']}'")

        experience = tech.get("experience", "unassessed")
        if experience not in VALID_EXPERIENCE_LEVELS:
            errors.append(
                f"{prefix}: experience invalide '{experience}' (valeurs: {VALID_EXPERIENCE_LEVELS})"
            )

        evidence = tech.get("evidence")
        if evidence is not None and (
            not isinstance(evidence, list)
            or any(not isinstance(item, str) or not item.strip() for item in evidence)
        ):
            errors.append(f"{prefix}: evidence doit être une liste de chaînes non vides")
        elif experience != "unassessed" and not evidence:
            errors.append(f"{prefix}: au moins une preuve est requise pour '{experience}'")

        since = tech.get("since")
        if since is not None:
            try:
                datetime.strptime(since, "%Y-%m")
            except (TypeError, ValueError):
                errors.append(f"{prefix}: since invalide (format YYYY-MM attendu)")

        for field in ("pros", "cons", "use_cases"):
            value = tech.get(field)
            if value is not None and (
                not isinstance(value, list)
                or any(not isinstance(item, str) or not item.strip() for item in value)
            ):
                errors.append(f"{prefix}: {field} doit être une liste de chaînes non vides")

        sources = tech.get("sources")
        if sources is not None:
            if not isinstance(sources, dict):
                errors.append(f"{prefix}: sources doit être un objet")
            else:
                unknown_sources = set(sources) - VALID_SOURCE_FIELDS
                if unknown_sources:
                    errors.append(f"{prefix}: sources inconnues {sorted(unknown_sources)}")
                github = sources.get("github")
                if github is not None and (not isinstance(github, str) or github.count("/") != 1):
                    errors.append(f"{prefix}: source github invalide (owner/repo attendu)")

    return errors


def validate_category_balance(tech_file: Path = TECH_FILE) -> list[str]:
    """Ensure the published catalog keeps exactly ten entries per category."""
    with tech_file.open(encoding="utf-8") as f:
        technologies = yaml.safe_load(f).get("technologies", [])

    counts = {category: 0 for category in VALID_CATEGORIES}
    for tech in technologies:
        if isinstance(tech, dict) and tech.get("category") in counts:
            counts[tech["category"]] += 1

    return [
        f"catégorie '{category}': {count} technologies "
        f"(attendu: {EXPECTED_TECHNOLOGIES_PER_CATEGORY})"
        for category, count in sorted(counts.items())
        if count != EXPECTED_TECHNOLOGIES_PER_CATEGORY
    ]


if __name__ == "__main__":
    errors = validate() + validate_category_balance()
    if errors:
        print("Erreurs de validation YAML :")
        for error in errors:
            print(f"  ✗ {error}")
        sys.exit(1)
    print(f"technologies.yaml valide ({TECH_FILE})")
