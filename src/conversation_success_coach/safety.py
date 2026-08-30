"""Responsible-use detection and evidence redaction.

This module does not attempt to infer hidden intent or personal traits. It only
matches explicit text patterns that request prohibited behavior or reveal
obvious sensitive-data shapes.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from conversation_success_coach.schemas import ResponsibleUse, RiskSignal

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}(?!\d)")
CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
LONG_NUMBER_RE = re.compile(r"\b\d{8,}\b")


def redact_evidence(value: str, limit: int = 160) -> str:
    """Return a short excerpt with common direct identifiers removed."""

    redacted = EMAIL_RE.sub("[email]", value)
    redacted = PHONE_RE.sub("[phone]", redacted)
    redacted = SSN_RE.sub("[government-id]", redacted)
    redacted = CARD_RE.sub("[payment-number]", redacted)
    redacted = LONG_NUMBER_RE.sub("[long-number]", redacted)
    compact = re.sub(r"\s+", " ", redacted).strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


@dataclass(frozen=True, slots=True)
class ProhibitedPattern:
    capability: str
    patterns: tuple[re.Pattern[str], ...]
    safe_alternative: str


PROHIBITED_PATTERNS: tuple[ProhibitedPattern, ...] = (
    ProhibitedPattern(
        capability="covert_manipulation",
        patterns=(
            re.compile(r"\b(manipulat(?:e|ion)|trick|guilt[- ]?trip)\b", re.I),
            re.compile(r"\bpressure (?:them|the person|the customer).{0,30}\buntil\b", re.I),
        ),
        safe_alternative=(
            "Use transparent, permission-based language and leave the other person "
            "a genuine, low-friction way to decline."
        ),
    ),
    ProhibitedPattern(
        capability="protected_attribute_inference",
        patterns=(
            re.compile(
                r"\b(infer|guess|deduce|predict|rank by).{0,35}"
                r"\b(race|ethnicity|religion|gender|sex|age|disability|"
                r"sexual orientation|nationality)\b",
                re.I,
            ),
            re.compile(
                r"\b(exclude|avoid|target only).{0,35}"
                r"\b(women|men|older|younger|disabled|muslim|christian|jewish|"
                r"gay|straight|black|white|asian|latino)\b",
                re.I,
            ),
        ),
        safe_alternative=(
            "Base decisions on stated, job- or policy-relevant criteria and use the "
            "same documented process for everyone."
        ),
    ),
    ProhibitedPattern(
        capability="mental_health_diagnosis",
        patterns=(
            re.compile(
                r"\bdiagnos(?:e|is).{0,30}\b(mental|person|candidate|customer|member)\b", re.I
            ),
            re.compile(
                r"\b(is|sounds|seems).{0,12}\b(bipolar|psychotic|a psychopath|narcissistic)\b", re.I
            ),
        ),
        safe_alternative=(
            "Describe observable communication or safety behavior without assigning "
            "a diagnosis, and use qualified support channels when appropriate."
        ),
    ),
    ProhibitedPattern(
        capability="deceptive_urgency",
        patterns=(
            re.compile(
                r"\b(fake|invent|pretend).{0,30}\b(deadline|scarcity|expires|last chance)\b", re.I
            ),
            re.compile(
                r"\bsay.{0,30}\b(expires today|last chance).{0,30}\b(even if|though it)\b", re.I
            ),
        ),
        safe_alternative=(
            "State only real deadlines, constraints, and consequences; distinguish "
            "known facts from estimates."
        ),
    ),
    ProhibitedPattern(
        capability="dependency_optimization",
        patterns=(
            re.compile(
                r"\b(make|keep).{0,25}\b(them|users?|members?).{0,20}\b(dependent|hooked)\b", re.I
            ),
            re.compile(r"\boptimi[sz]e.{0,30}\bdependency\b", re.I),
        ),
        safe_alternative=(
            "Optimize for informed choice, durable value, and easy disengagement—not "
            "compulsion or dependency."
        ),
    ),
    ProhibitedPattern(
        capability="impersonation_or_auto_send",
        patterns=(
            re.compile(
                r"\b(impersonate|pretend to be).{0,30}\b(me|manager|recruiter|moderator|agent)\b",
                re.I,
            ),
            re.compile(r"\b(auto[- ]?send|send automatically|send as me)\b", re.I),
        ),
        safe_alternative=(
            "Provide an editable draft for the operator to review and send through "
            "their normal, clearly identified channel."
        ),
    ),
)


RISK_PATTERNS: tuple[
    tuple[str, str, tuple[re.Pattern[str], ...], str],
    ...,
] = (
    (
        "threat_or_immediate_safety",
        "critical",
        (
            re.compile(r"\b(kill|hurt|attack|shoot|stab|bomb|doxx)\b", re.I),
            re.compile(r"\bi know where you live\b", re.I),
        ),
        "Pause ordinary coaching and follow the organization's immediate-safety escalation process.",
    ),
    (
        "harassment_or_personal_attack",
        "high",
        (
            re.compile(r"\b(idiot|stupid|moron|clueless|shut up|worthless)\b", re.I),
            re.compile(r"\bkeep tagging you until\b", re.I),
        ),
        "Address the specific behavior, preserve evidence, and apply published rules consistently.",
    ),
    (
        "escalation_or_trust_break",
        "medium",
        (
            re.compile(r"\b(unacceptable|furious|angry|frustrated|ridiculous)\b", re.I),
            re.compile(
                r"\b(manager|supervisor|lawyer|lawsuit|chargeback|formal complaint)\b", re.I
            ),
        ),
        "Acknowledge the impact, avoid defensiveness, and offer a clear escalation or review path.",
    ),
    (
        "sensitive_data_exposure",
        "high",
        (EMAIL_RE, PHONE_RE, CARD_RE, SSN_RE),
        "Minimize or redact direct identifiers and move sensitive details to an approved secure channel.",
    ),
)


class SafetyPolicy:
    """Evaluate explicit responsible-use boundaries."""

    def evaluate_responsible_use(self, text: str) -> ResponsibleUse:
        blocked: list[str] = []
        alternatives: list[str] = []
        for rule in PROHIBITED_PATTERNS:
            if any(pattern.search(text) for pattern in rule.patterns):
                blocked.append(rule.capability)
                alternatives.append(rule.safe_alternative)

        if blocked:
            explanation = "The requested direction crosses a responsible-use boundary. " + " ".join(
                dict.fromkeys(alternatives)
            )
            behavior = "redirected"
        else:
            explanation = (
                "Coaching is advisory only. The operator chooses whether and how to "
                "adapt any draft; this service never sends messages or impersonates a person."
            )
            behavior = "standard"

        return ResponsibleUse(
            blocked_capabilities=blocked,
            behavior=behavior,
            explanation=explanation,
        )

    def detect_risks(self, turns: Iterable[str]) -> list[RiskSignal]:
        combined = "\n".join(turns)
        risks: list[RiskSignal] = []
        for category, severity, patterns, boundary in RISK_PATTERNS:
            evidence: list[str] = []
            for line in turns:
                if any(pattern.search(line) for pattern in patterns):
                    evidence.append(redact_evidence(line))
            if not evidence:
                continue
            if category == "sensitive_data_exposure":
                explanation = (
                    "The transcript appears to contain a direct identifier or sensitive "
                    "number shape. Detection is heuristic and may include false positives."
                )
            elif category == "threat_or_immediate_safety":
                explanation = (
                    "Explicit language may indicate a threat or immediate-safety concern; "
                    "do not treat ordinary coaching as sufficient."
                )
            elif category == "harassment_or_personal_attack":
                explanation = (
                    "The transcript contains language consistent with a personal attack "
                    "or persistent unwanted contact."
                )
            else:
                explanation = (
                    "The conversation contains signs of frustration, formal escalation, "
                    "or a material loss of trust."
                )
            risks.append(
                RiskSignal(
                    category=category,
                    severity=severity,
                    explanation=explanation,
                    evidence=list(dict.fromkeys(evidence))[:5],
                    recommended_boundary=boundary,
                )
            )

        # A prohibited request is represented separately by ResponsibleUse and
        # is deliberately not inferred from mere sentiment.
        _ = combined
        return risks
