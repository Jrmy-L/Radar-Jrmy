from scripts.utils.position_proposal import propose_position


def test_proposes_one_ring_promotion_for_rising_technology():
    proposal = propose_position({"position": "assess"}, "rising", {})

    assert proposal == {
        "from": "assess",
        "to": "trial",
        "reason": "Trajectoire en hausse ; revue architecturale recommandée.",
    }


def test_proposes_hold_for_archived_repository():
    proposal = propose_position(
        {"position": "adopt"},
        "stable",
        {"github": {"archived": True}},
    )

    assert proposal["to"] == "hold"


def test_does_not_propose_change_for_stable_technology():
    assert propose_position({"position": "trial"}, "stable", {}) is None
