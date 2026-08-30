from __future__ import annotations

from datetime import UTC, datetime, timedelta


def _enable_raw_storage(client) -> None:
    response = client.put(
        "/api/v1/privacy/settings",
        json={
            "allow_raw_content_storage": True,
            "default_analysis_retention_days": 7,
            "audit_retention_days": 30,
        },
    )
    assert response.status_code == 200


def _create_private_conversation(client, title: str = "Private demo case") -> str:
    _enable_raw_storage(client)
    response = client.post(
        "/api/v1/conversations",
        json={
            "title": title,
            "mode": "support",
            "owner": "Taylor Quill",
            "participant_label": "Case participant",
            "goal": "Resolve a fictional issue.",
            "stage": "Intake",
            "retention_days": 1,
            "consent_confirmed": True,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_ad_hoc_analysis_defaults_to_no_persistence(client) -> None:
    repository = client.app.state.repository
    before = repository.db.query_one("SELECT COUNT(*) AS count FROM analyses")["count"]

    response = client.post(
        "/api/v1/analyze",
        json={
            "mode": "support",
            "turns": [
                {
                    "speaker": "Participant",
                    "role": "participant",
                    "text": "When will this be fixed?",
                }
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["persisted"] is False
    after = repository.db.query_one("SELECT COUNT(*) AS count FROM analyses")["count"]
    assert after == before


def test_raw_storage_requires_operator_setting(client) -> None:
    response = client.post(
        "/api/v1/conversations",
        json={
            "title": "Should fail",
            "mode": "sales",
            "owner": "Operator",
            "participant_label": "Participant",
            "goal": "",
            "stage": "",
            "retention_days": 2,
            "consent_confirmed": True,
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "raw_storage_disabled"


def test_conversation_purge_removes_content_and_keeps_content_free_receipt(client) -> None:
    conversation_id = _create_private_conversation(client)
    turn_text = "Fictional private detail unique-to-purge-test."
    assert (
        client.post(
            f"/api/v1/conversations/{conversation_id}/turns",
            json={
                "speaker": "Case participant",
                "role": "participant",
                "text": turn_text,
            },
        ).status_code
        == 201
    )
    conversation = client.get(f"/api/v1/conversations/{conversation_id}").json()
    analysis = client.post(
        "/api/v1/analyze",
        json={
            "mode": "support",
            "conversation_id": conversation_id,
            "turns": [
                {
                    "speaker": item["speaker"],
                    "role": item["role"],
                    "text": item["text"],
                    "timestamp": item["created_at"],
                }
                for item in conversation["turns"]
            ],
            "data_handling": {
                "persist_analysis": True,
                "store_raw_content": True,
                "retention_days": 1,
                "consent_confirmed": True,
            },
        },
    )
    assert analysis.status_code == 200

    purged = client.post(
        "/api/v1/privacy/purge",
        json={
            "scope": "conversation",
            "conversation_id": conversation_id,
            "confirm": True,
        },
    )
    assert purged.status_code == 200
    assert purged.json()["deleted"]["conversations"] == 1
    assert client.get(f"/api/v1/conversations/{conversation_id}").status_code == 404

    audit = client.get("/api/v1/audit").json()["items"]
    receipt = next(
        item
        for item in audit
        if item["event_type"] == "privacy.conversation_purged"
        and item["resource_id"] == conversation_id
    )
    assert receipt["details"]["transcript_text_in_audit"] is False
    assert turn_text not in str(audit)


def test_retention_endpoint_deletes_expired_non_demo_conversation(client) -> None:
    conversation_id = _create_private_conversation(client, "Expiring case")
    repository = client.app.state.repository
    repository.db.execute(
        "UPDATE conversations SET expires_at = ? WHERE id = ?",
        ((datetime.now(UTC) - timedelta(minutes=1)).isoformat(), conversation_id),
    )

    response = client.post("/api/v1/privacy/retention/run")

    assert response.status_code == 200
    assert response.json()["deleted"]["conversations"] == 1
    assert client.get(f"/api/v1/conversations/{conversation_id}").status_code == 404
