from __future__ import annotations

import pytest

from conversation_success_coach.analysis import ConversationAnalyzer
from conversation_success_coach.schemas import (
    AnalyzeRequest,
    ConversationContext,
    ConversationMode,
    SpeakerRole,
    Turn,
)


@pytest.mark.parametrize(
    ("mode", "expected_title"),
    [
        (ConversationMode.SALES, "Close the discovery loop"),
        (ConversationMode.SUPPORT, "Stabilize the issue and set a checkpoint"),
        (ConversationMode.RECRUITING, "Make the process legible"),
        (ConversationMode.COMMUNITY, "Moderate the behavior, not the person"),
    ],
)
def test_mode_specific_coaching(mode: ConversationMode, expected_title: str) -> None:
    request = AnalyzeRequest(
        mode=mode,
        turns=[
            Turn(
                speaker="Alex Rowan",
                role=SpeakerRole.PARTICIPANT,
                text="This matters for our timeline. What happens next?",
            ),
            Turn(
                speaker="Morgan Vale",
                role=SpeakerRole.OPERATOR,
                text="Thanks for explaining. I am reviewing the details now.",
            ),
        ],
        context=ConversationContext(goal="Reach a transparent next step."),
    )

    result = ConversationAnalyzer().analyze(request)

    assert any(item.title == expected_title for item in result.suggestions)
    assert all(item.requires_human_review for item in result.suggestions)
    assert all(item.can_auto_send is False for item in result.suggestions)
    assert all(item.delivery == "manual_only" for item in result.suggestions)


def test_analysis_is_deterministic_for_equal_normalized_input() -> None:
    analyzer = ConversationAnalyzer()
    request = AnalyzeRequest(
        mode=ConversationMode.SALES,
        turns=[
            Turn(
                speaker="Maya Chen",
                role=SpeakerRole.OPERATOR,
                text="Which outcome matters most?",
            ),
            Turn(
                speaker="Theo Brooks",
                role=SpeakerRole.PARTICIPANT,
                text="What does pricing look like, and when could migration begin?",
            ),
            Turn(
                speaker="Maya Chen",
                role=SpeakerRole.OPERATOR,
                text="Migration begins with a read-only review.",
            ),
        ],
    )

    first = analyzer.analyze(request)
    second = analyzer.analyze(request)

    assert first.analysis_id == second.analysis_id
    assert first.fingerprint == second.fingerprint
    assert first.overall_score == second.overall_score
    assert first.signals == second.signals
    assert first.unanswered_questions == second.unanswered_questions
    assert first.suggestions == second.suggestions
    assert {item.topic for item in first.unanswered_questions} == {
        "pricing",
        "timeline",
    }


def test_analysis_reports_confidence_explanations_and_limitations() -> None:
    result = ConversationAnalyzer().analyze(
        AnalyzeRequest(
            mode=ConversationMode.SUPPORT,
            turns=[
                Turn(
                    speaker="Rowan Hart",
                    role=SpeakerRole.PARTICIPANT,
                    text="The export is still broken and this is blocking our deadline.",
                ),
                Turn(
                    speaker="Imani Cole",
                    role=SpeakerRole.OPERATOR,
                    text="I can see the prior ticket and I am checking the worker.",
                ),
            ],
        )
    )

    assert set(result.signals) == {"momentum", "tone", "clarity", "empathy"}
    assert all(signal.explanation for signal in result.signals.values())
    assert all(0 <= signal.confidence <= 1 for signal in result.signals.values())
    assert result.limitations
    assert (
        "hidden emotion"
        in " ".join([*result.limitations, result.signals["tone"].explanation]).lower()
    )
