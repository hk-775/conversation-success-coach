"""Validated API and domain schemas."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ShortText = Annotated[str, Field(min_length=1, max_length=240)]
Identifier = Annotated[str, Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9._:-]+$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ConversationMode(StrEnum):
    SALES = "sales"
    SUPPORT = "support"
    RECRUITING = "recruiting"
    COMMUNITY = "community"


class SpeakerRole(StrEnum):
    OPERATOR = "operator"
    PARTICIPANT = "participant"
    OBSERVER = "observer"


class FeedbackKind(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    OUTCOME = "outcome"


class OutcomeKind(StrEnum):
    ADVANCED = "advanced"
    RESOLVED = "resolved"
    NO_CHANGE = "no_change"
    ESCALATED = "escalated"
    DECLINED = "declined"


class Turn(StrictModel):
    speaker: Annotated[str, Field(min_length=1, max_length=80)]
    role: SpeakerRole
    text: Annotated[str, Field(min_length=1, max_length=4000)]
    timestamp: datetime | None = None


class ConversationContext(StrictModel):
    goal: Annotated[str, Field(max_length=500)] = ""
    stage: Annotated[str, Field(max_length=120)] = ""
    known_facts: list[Annotated[str, Field(max_length=240)]] = Field(
        default_factory=list,
        max_length=20,
    )


class DataHandling(StrictModel):
    """Per-request persistence controls.

    Stateless analysis is the default. Raw text can only be retained with
    explicit persistence, explicit consent, and a bounded retention period.
    """

    persist_analysis: bool = False
    store_raw_content: bool = False
    retention_days: Annotated[int, Field(ge=0, le=30)] = 0
    consent_confirmed: bool = False

    @model_validator(mode="after")
    def validate_retention(self) -> DataHandling:
        if not self.persist_analysis:
            if self.store_raw_content or self.retention_days or self.consent_confirmed:
                raise ValueError("retention options require persist_analysis=true")
            return self
        if self.retention_days < 1:
            raise ValueError("persisted analysis requires retention_days between 1 and 30")
        if self.store_raw_content and not self.consent_confirmed:
            raise ValueError("raw content storage requires consent_confirmed=true")
        return self


class AnalyzeRequest(StrictModel):
    mode: ConversationMode
    turns: Annotated[list[Turn], Field(min_length=1, max_length=80)]
    conversation_id: Identifier | None = None
    context: ConversationContext = Field(default_factory=ConversationContext)
    data_handling: DataHandling = Field(default_factory=DataHandling)


class Signal(StrictModel):
    score: Annotated[int, Field(ge=0, le=100)]
    label: ShortText
    explanation: Annotated[str, Field(min_length=1, max_length=600)]
    evidence: list[Annotated[str, Field(max_length=180)]] = Field(
        default_factory=list,
        max_length=6,
    )
    confidence: Annotated[float, Field(ge=0, le=1)]


class UnansweredQuestion(StrictModel):
    question: Annotated[str, Field(min_length=1, max_length=300)]
    topic: ShortText
    asked_by: ShortText
    turn_index: Annotated[int, Field(ge=0)]
    confidence: Annotated[float, Field(ge=0, le=1)]


class RiskSignal(StrictModel):
    category: ShortText
    severity: Literal["low", "medium", "high", "critical"]
    explanation: Annotated[str, Field(min_length=1, max_length=600)]
    evidence: list[Annotated[str, Field(max_length=180)]] = Field(
        default_factory=list,
        max_length=5,
    )
    recommended_boundary: Annotated[str, Field(min_length=1, max_length=500)]


class ResponsibleUse(StrictModel):
    suggestions_only: Literal[True] = True
    requires_human_review: Literal[True] = True
    can_auto_send: Literal[False] = False
    impersonation_allowed: Literal[False] = False
    protected_attribute_inference_allowed: Literal[False] = False
    blocked_capabilities: list[ShortText] = Field(default_factory=list)
    behavior: Literal["standard", "redirected"]
    explanation: Annotated[str, Field(min_length=1, max_length=700)]


class Suggestion(StrictModel):
    id: Identifier
    category: ShortText
    priority: Literal["now", "next", "optional"]
    title: ShortText
    action: Annotated[str, Field(min_length=1, max_length=800)]
    example_language: Annotated[str, Field(min_length=1, max_length=800)]
    rationale: Annotated[str, Field(min_length=1, max_length=800)]
    evidence: list[Annotated[str, Field(max_length=180)]] = Field(
        default_factory=list,
        max_length=6,
    )
    confidence: Annotated[float, Field(ge=0, le=1)]
    limitations: list[Annotated[str, Field(max_length=280)]] = Field(
        default_factory=list,
        max_length=8,
    )
    playbook_refs: list[Identifier] = Field(default_factory=list, max_length=8)
    requires_human_review: Literal[True] = True
    delivery: Literal["manual_only"] = "manual_only"
    can_auto_send: Literal[False] = False


class AnalysisResponse(StrictModel):
    analysis_id: Identifier
    conversation_id: Identifier | None
    mode: ConversationMode
    fingerprint: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
    created_at: datetime
    overall_score: Annotated[int, Field(ge=0, le=100)]
    status: Literal["healthy", "watch", "at_risk"]
    signals: dict[Literal["momentum", "tone", "clarity", "empathy"], Signal]
    unanswered_questions: list[UnansweredQuestion]
    risks: list[RiskSignal]
    suggestions: list[Suggestion]
    responsible_use: ResponsibleUse
    limitations: list[Annotated[str, Field(max_length=300)]]
    persisted: bool = False
    expires_at: datetime | None = None


class SuggestionRequest(AnalyzeRequest):
    max_suggestions: Annotated[int, Field(ge=1, le=5)] = 3


class SuggestionResponse(StrictModel):
    analysis_id: Identifier
    conversation_id: Identifier | None
    mode: ConversationMode
    suggestions: list[Suggestion]
    responsible_use: ResponsibleUse
    limitations: list[Annotated[str, Field(max_length=300)]]


class ConversationCreate(StrictModel):
    title: Annotated[str, Field(min_length=1, max_length=160)]
    mode: ConversationMode
    owner: Annotated[str, Field(min_length=1, max_length=80)]
    participant_label: Annotated[str, Field(min_length=1, max_length=80)]
    goal: Annotated[str, Field(max_length=500)] = ""
    stage: Annotated[str, Field(max_length=120)] = ""
    retention_days: Annotated[int, Field(ge=1, le=30)] = 7
    consent_confirmed: Literal[True]


class TurnCreate(Turn):
    pass


class FeedbackCreate(StrictModel):
    kind: FeedbackKind
    suggestion_id: Identifier | None = None
    conversation_id: Identifier | None = None
    outcome: OutcomeKind | None = None
    note: Annotated[str, Field(max_length=500)] = ""

    @model_validator(mode="after")
    def validate_feedback(self) -> FeedbackCreate:
        if self.kind in {FeedbackKind.ACCEPTED, FeedbackKind.REJECTED} and not self.suggestion_id:
            raise ValueError("accepted/rejected feedback requires suggestion_id")
        if self.kind is FeedbackKind.OUTCOME and (not self.conversation_id or self.outcome is None):
            raise ValueError("outcome feedback requires conversation_id and outcome")
        return self


class PlaybookCreate(StrictModel):
    name: Annotated[str, Field(min_length=1, max_length=120)]
    mode: ConversationMode
    description: Annotated[str, Field(min_length=1, max_length=600)]
    principles: Annotated[
        list[Annotated[str, Field(min_length=1, max_length=240)]],
        Field(min_length=1, max_length=12),
    ]
    enabled: bool = True


class PlaybookUpdate(StrictModel):
    name: Annotated[str, Field(min_length=1, max_length=120)] | None = None
    description: Annotated[str, Field(min_length=1, max_length=600)] | None = None
    principles: (
        Annotated[
            list[Annotated[str, Field(min_length=1, max_length=240)]],
            Field(min_length=1, max_length=12),
        ]
        | None
    ) = None
    enabled: bool | None = None


class PrivacySettingsUpdate(StrictModel):
    allow_raw_content_storage: bool
    default_analysis_retention_days: Annotated[int, Field(ge=1, le=30)]
    audit_retention_days: Annotated[int, Field(ge=7, le=365)]


class PurgeRequest(StrictModel):
    scope: Literal["conversation", "expired", "all_non_demo"]
    conversation_id: Identifier | None = None
    confirm: Literal[True]

    @model_validator(mode="after")
    def validate_scope(self) -> PurgeRequest:
        if self.scope == "conversation" and not self.conversation_id:
            raise ValueError("conversation purge requires conversation_id")
        if self.scope != "conversation" and self.conversation_id:
            raise ValueError("conversation_id is only valid for conversation purge")
        return self


class AuditQuery(StrictModel):
    event_type: Annotated[str, Field(max_length=80)] | None = None
    limit: Annotated[int, Field(ge=1, le=500)] = 100
