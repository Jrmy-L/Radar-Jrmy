"""Human-in-the-loop position proposals for the technology radar."""

PROMOTION_TARGET = {"hold": "assess", "assess": "trial", "trial": "adopt"}
DEMOTION_TARGET = {"adopt": "trial", "trial": "assess", "assess": "hold"}


def propose_position(tech: dict, trajectory: str, metrics: dict) -> dict | None:
    """Suggest a one-ring move without changing the source YAML."""
    current = tech["position"]
    github = metrics.get("github", {})

    if github.get("archived") and current != "hold":
        return {"from": current, "to": "hold", "reason": "Le dépôt GitHub est archivé."}

    if trajectory == "rising" and current in PROMOTION_TARGET:
        return {
            "from": current,
            "to": PROMOTION_TARGET[current],
            "reason": "Trajectoire en hausse ; revue architecturale recommandée.",
        }

    if trajectory == "declining" and current in DEMOTION_TARGET:
        return {
            "from": current,
            "to": DEMOTION_TARGET[current],
            "reason": "Trajectoire en baisse ; réévaluation recommandée.",
        }

    return None
