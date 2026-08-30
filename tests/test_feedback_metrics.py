from __future__ import annotations


def _persisted_analysis(client, conversation_id: str) -> dict:
    conversation = client.get(f"/api/v1/conversations/{conversation_id}").json()
    response = client.post(
        "/api/v1/analyze",
        json={
            "mode": conversation["mode"],
            "conversation_id": conversation["id"],
            "turns": [
                {
                    "speaker": turn["speaker"],
                    "role": turn["role"],
                    "text": turn["text"],
                    "timestamp": turn["created_at"],
                }
                for turn in conversation["turns"]
            ],
            "context": {
                "goal": conversation["goal"],
                "stage": conversation["stage"],
                "known_facts": [],
            },
            "data_handling": {
                "persist_analysis": True,
                "store_raw_content": False,
                "retention_days": 7,
                "consent_confirmed": False,
            },
        },
    )
    assert response.status_code == 200
    return response.json()


def test_feedback_changes_metrics_and_suggestion_state(client) -> None:
    baseline = client.get("/api/v1/metrics").json()
    analysis = _persisted_analysis(client, "conv_sales_northstar")
    suggestion_id = analysis["suggestions"][0]["id"]

    accepted = client.post(
        "/api/v1/feedback",
        json={
            "kind": "accepted",
            "suggestion_id": suggestion_id,
            "note": "Useful after editing.",
        },
    )
    assert accepted.status_code == 201

    outcome = client.post(
        "/api/v1/feedback",
        json={
            "kind": "outcome",
            "conversation_id": "conv_sales_northstar",
            "outcome": "advanced",
            "note": "Fictional meeting moved to a technical review.",
        },
    )
    assert outcome.status_code == 201

    metrics = client.get("/api/v1/metrics").json()
    assert metrics["suggestions_accepted"] == baseline["suggestions_accepted"] + 1
    assert metrics["outcomes_recorded"] == baseline["outcomes_recorded"] + 1
    assert metrics["positive_outcomes"] == baseline["positive_outcomes"] + 1
    assert metrics["acceptance_rate"] >= baseline["acceptance_rate"]

    feedback = client.get("/api/v1/feedback").json()["items"]
    assert any(item["suggestion_id"] == suggestion_id for item in feedback)
    audit = client.get("/api/v1/audit").json()["items"]
    accepted_event = next(item for item in audit if item["event_type"] == "feedback.accepted")
    assert accepted_event["details"]["note_recorded"] is True
    assert accepted_event["details"]["note_in_audit"] is False
    assert "Useful after editing" not in str(accepted_event)
