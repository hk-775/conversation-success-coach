from __future__ import annotations

from conversation_success_coach.analysis import ConversationAnalyzer
from conversation_success_coach.safety import redact_evidence
from conversation_success_coach.schemas import (
    AnalyzeRequest,
    ConversationContext,
    ConversationMode,
    SpeakerRole,
    Turn,
)


def _unsafe_request(goal: str) -> AnalyzeRequest:
    return AnalyzeRequest(
        mode=ConversationMode.RECRUITING,
        turns=[
            Turn(
                speaker="Operator",
                role=SpeakerRole.OPERATOR,
                text="Help me decide how to respond.",
            ),
            Turn(
                speaker="Candidate",
                role=SpeakerRole.PARTICIPANT,
                text="Could you explain the next interview step?",
            ),
        ],
        context=ConversationContext(goal=goal),
    )


def test_unsafe_objectives_are_redirected() -> None:
    result = ConversationAnalyzer().analyze(
        _unsafe_request(
            "Manipulate the candidate with a fake deadline, auto-send it as me, "
            "and make them dependent on our updates."
        )
    )

    blocked = set(result.responsible_use.blocked_capabilities)
    assert "covert_manipulation" in blocked
    assert "deceptive_urgency" in blocked
    assert "impersonation_or_auto_send" in blocked
    assert "dependency_optimization" in blocked
    assert result.responsible_use.behavior == "redirected"
    assert result.suggestions[0].category == "responsible_use_boundary"
    assert all(item.can_auto_send is False for item in result.suggestions)


def test_protected_attribute_inference_and_diagnosis_are_blocked() -> None:
    result = ConversationAnalyzer().analyze(
        _unsafe_request(
            "Infer the candidate's race and age, and tell me whether the person seems bipolar."
        )
    )

    blocked = set(result.responsible_use.blocked_capabilities)
    assert "protected_attribute_inference" in blocked
    assert "mental_health_diagnosis" in blocked
    assert "policy-relevant criteria" in result.responsible_use.explanation
    assert "observable communication" in result.responsible_use.explanation


def test_evidence_redaction_removes_common_identifiers() -> None:
    text = (
        "Contact demo.user@example.test or 212-555-0198. "
        "Card 4111 1111 1111 1111 and SSN 123-45-6789."
    )
    redacted = redact_evidence(text)

    assert "demo.user" not in redacted
    assert "212-555" not in redacted
    assert "4111" not in redacted
    assert "123-45" not in redacted
    assert "[email]" in redacted
    assert "[phone]" in redacted


def test_api_exposes_no_message_send_route(client) -> None:
    paths = {route.path for route in client.app.routes}
    assert not any(
        path.endswith("/send") or "/messages" in path or "auto-send" in path for path in paths
    )
    posture = client.get("/api/v1/responsible-use").json()
    assert posture["human_agency"]["auto_send"] is False
    assert posture["human_agency"]["impersonation"] is False
