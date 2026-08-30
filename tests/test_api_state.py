from __future__ import annotations


def test_health_pages_and_default_port_contract(client) -> None:
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["external_network_calls"] is False
    assert health.json()["message_delivery_capability"] is False
    assert client.app.state.settings.port == 8103

    assert "Better conversations" in client.get("/").text
    assert "Better conversations" in client.get("/index.html").text
    assert "Live conversation workspace" in client.get("/dashboard.html").text
    assert "Interactive architecture" in client.get("/architecture.html").text


def test_playbook_crud_changes_api_state(client) -> None:
    created = client.post(
        "/api/v1/playbooks",
        json={
            "name": "Clear next checkpoints",
            "mode": "support",
            "description": "A fictional test playbook.",
            "principles": [
                "Name one owner.",
                "Give one realistic update checkpoint.",
            ],
            "enabled": True,
        },
    )
    assert created.status_code == 201
    playbook_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/playbooks/{playbook_id}",
        json={"enabled": False, "name": "Paused checkpoint playbook"},
    )
    assert updated.status_code == 200
    assert updated.json()["enabled"] is False
    assert updated.json()["name"] == "Paused checkpoint playbook"

    listed = client.get("/api/v1/playbooks").json()["items"]
    assert any(item["id"] == playbook_id for item in listed)

    deleted = client.delete(f"/api/v1/playbooks/{playbook_id}")
    assert deleted.status_code == 204
    assert all(
        item["id"] != playbook_id for item in client.get("/api/v1/playbooks").json()["items"]
    )


def test_structured_validation_errors(client) -> None:
    response = client.post(
        "/api/v1/analyze",
        json={
            "mode": "unknown",
            "turns": [],
            "unexpected": "field",
        },
    )

    assert response.status_code == 422
    payload = response.json()["error"]
    assert payload["code"] == "validation_error"
    assert payload["issues"]
    assert all({"field", "message", "type"} <= set(item) for item in payload["issues"])


def test_seed_reset_restores_canonical_state(client) -> None:
    before = client.get("/api/v1/conversations/conv_support_bluebird").json()["turns"]
    assert len(before) == 4

    added = client.post(
        "/api/v1/conversations/conv_support_bluebird/turns",
        json={
            "speaker": "Rowan Hart",
            "role": "participant",
            "text": "A temporary fictional turn.",
        },
    )
    assert added.status_code == 201
    assert len(client.get("/api/v1/conversations/conv_support_bluebird").json()["turns"]) == 5

    reset = client.post("/api/v1/demo/reset")
    assert reset.status_code == 200
    assert reset.json()["conversations"] == 4
    assert reset.json()["playbooks"] == 4
    assert len(client.get("/api/v1/conversations/conv_support_bluebird").json()["turns"]) == 4
