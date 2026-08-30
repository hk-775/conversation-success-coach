"""Deterministic conversation analysis and mode-specific coaching."""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from collections.abc import Iterable
from datetime import UTC, datetime

from conversation_success_coach.safety import SafetyPolicy, redact_evidence
from conversation_success_coach.schemas import (
    AnalysisResponse,
    AnalyzeRequest,
    ConversationMode,
    ResponsibleUse,
    Signal,
    SpeakerRole,
    Suggestion,
    UnansweredQuestion,
)

WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z'-]*")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
ALL_CAPS_RE = re.compile(r"\b[A-Z]{4,}\b")
VAGUE_WORDS = {
    "thing",
    "things",
    "stuff",
    "somehow",
    "maybe",
    "whatever",
    "soon",
    "later",
    "probably",
    "basically",
}
WARMTH_WORDS = {
    "thanks",
    "thank",
    "appreciate",
    "glad",
    "welcome",
    "happy",
    "please",
    "understand",
    "sorry",
}
FRICTION_WORDS = {
    "unacceptable",
    "angry",
    "furious",
    "frustrated",
    "ridiculous",
    "clueless",
    "stupid",
    "hate",
    "broken",
    "still",
}
EMPATHY_PHRASES = (
    "i understand",
    "i can see",
    "that sounds",
    "i'm sorry",
    "i am sorry",
    "appreciate how",
    "thanks for explaining",
    "impact this has",
    "frustrating",
    "your concern",
)
POSITIVE_MOVEMENT = {
    "agree",
    "works",
    "helpful",
    "next",
    "schedule",
    "resolved",
    "confirm",
    "interested",
    "available",
    "thanks",
}
STALLING_WORDS = {
    "maybe",
    "later",
    "unsure",
    "whatever",
    "nevermind",
    "still",
    "waiting",
    "hello?",
}
STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "and",
    "are",
    "because",
    "been",
    "before",
    "could",
    "does",
    "for",
    "from",
    "have",
    "how",
    "into",
    "just",
    "like",
    "look",
    "more",
    "our",
    "that",
    "the",
    "their",
    "then",
    "there",
    "they",
    "this",
    "was",
    "what",
    "when",
    "where",
    "which",
    "with",
    "would",
    "you",
    "your",
}

TOPICS: dict[str, set[str]] = {
    "pricing": {"price", "pricing", "cost", "budget", "fee", "quote", "rate"},
    "timeline": {"when", "timeline", "timeframe", "long", "date", "soon", "deadline"},
    "location_or_remote": {"remote", "hybrid", "location", "office", "onsite"},
    "implementation": {
        "migration",
        "migrate",
        "setup",
        "implementation",
        "integrate",
        "integration",
        "install",
    },
    "status": {"status", "update", "progress", "happening", "waiting"},
    "policy_or_process": {"policy", "process", "steps", "interview", "review", "rules"},
    "refund_or_remedy": {"refund", "credit", "replace", "remedy", "compensation"},
    "security_or_privacy": {"security", "privacy", "data", "retain", "delete", "access"},
}

MODE_COPY: dict[ConversationMode, dict[str, str]] = {
    ConversationMode.SALES: {
        "advance_title": "Close the discovery loop",
        "advance_category": "discovery_next_step",
        "advance_action": (
            "Summarize the stated need, answer the highest-value open question, "
            "then ask permission to agree on one concrete next step."
        ),
        "advance_example": (
            "Draft to adapt: “I heard that reliability and a predictable rollout matter "
            "most. I’ll answer that directly, then—if useful—we can decide together "
            "whether a short technical review is the right next step.”"
        ),
        "advance_rationale": (
            "Transparent synthesis and a permission-based next step maintain momentum "
            "without manufacturing urgency."
        ),
    },
    ConversationMode.SUPPORT: {
        "advance_title": "Stabilize the issue and set a checkpoint",
        "advance_category": "resolution_path",
        "advance_action": (
            "Acknowledge the operational impact, state the next diagnostic or remedy, "
            "name who owns it, and give a realistic update checkpoint."
        ),
        "advance_example": (
            "Draft to adapt: “I can see this is blocking your deadline. I’m checking the "
            "export job first; I’ll update you by the stated checkpoint even if the "
            "investigation is still in progress.”"
        ),
        "advance_rationale": (
            "Support conversations regain trust when impact, ownership, and the next "
            "update are all explicit."
        ),
    },
    ConversationMode.RECRUITING: {
        "advance_title": "Make the process legible",
        "advance_category": "candidate_clarity",
        "advance_action": (
            "Answer the candidate’s process question consistently, separate confirmed "
            "facts from estimates, and invite job-relevant questions or accommodation requests."
        ),
        "advance_example": (
            "Draft to adapt: “The confirmed next step is the panel review on Tuesday. "
            "The timing after that is an estimate, and I’ll tell you if it changes. "
            "What else would help you evaluate the role?”"
        ),
        "advance_rationale": (
            "A consistent, transparent process supports candidate agency and reduces "
            "avoidable uncertainty."
        ),
    },
    ConversationMode.COMMUNITY: {
        "advance_title": "Moderate the behavior, not the person",
        "advance_category": "de_escalation",
        "advance_action": (
            "Name the specific behavior, connect it to a published norm, request one "
            "concrete change, and offer a pause or appeal path."
        ),
        "advance_example": (
            "Draft to adapt: “Please address the idea without personal labels or repeated "
            "tagging. That applies to everyone here. Pause this thread for now; you can "
            "ask for a review through the normal moderation channel.”"
        ),
        "advance_rationale": (
            "Behavior-specific, consistently applied moderation lowers temperature and "
            "avoids speculation about a member’s identity or motives."
        ),
    },
}

COMMON_LIMITATIONS = [
    "Heuristic analysis can miss context, irony, power dynamics, and organization-specific policy.",
    "Tone and empathy scores describe observable language patterns, not hidden emotion or intent.",
    "Suggestions are drafts for human judgment and are never sent automatically.",
]


def _clamp(value: float) -> int:
    return max(0, min(100, round(value)))


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text).strip()


def _words(text: str) -> list[str]:
    return [word.lower() for word in WORD_RE.findall(text)]


def _question_segments(text: str) -> list[str]:
    segments: list[str] = []
    start = 0
    for match in re.finditer(r"\?", text):
        part = text[start : match.end()].strip()
        start = match.end()
        if part:
            # A combined question often contains independently answerable topics.
            subparts = re.split(
                r"\s+(?:and|also)\s+(?=(?:what|when|where|how|do|does|is|are|can|could|will)\b)",
                part,
                flags=re.I,
            )
            segments.extend(piece.strip() for piece in subparts if piece.strip())
    return segments


class ConversationAnalyzer:
    """Pure, deterministic analysis engine.

    No network calls, learned profiles, demographic inference, or message
    delivery are involved. Equal normalized inputs produce equal fingerprints,
    scores, and suggestions.
    """

    def __init__(self, safety_policy: SafetyPolicy | None = None) -> None:
        self.safety_policy = safety_policy or SafetyPolicy()

    def analyze(
        self,
        request: AnalyzeRequest,
        *,
        created_at: datetime | None = None,
        playbook_refs: Iterable[str] = (),
    ) -> AnalysisResponse:
        now = created_at or datetime.now(UTC)
        fingerprint = self._fingerprint(request)
        analysis_id = f"ana_{fingerprint[:20]}"
        turns = request.turns
        confidence = min(0.9, 0.48 + len(turns) * 0.035)

        unanswered = self._unanswered_questions(turns)
        risks = self.safety_policy.detect_risks(turn.text for turn in turns)
        responsible_text = " ".join(
            [request.context.goal, request.context.stage]
            + request.context.known_facts
            + [turn.text for turn in turns]
        )
        responsible_use = self.safety_policy.evaluate_responsible_use(responsible_text)

        momentum = self._momentum_signal(request, unanswered, confidence)
        tone = self._tone_signal(request, confidence)
        clarity = self._clarity_signal(request, confidence)
        empathy = self._empathy_signal(request, confidence)
        signals = {
            "momentum": momentum,
            "tone": tone,
            "clarity": clarity,
            "empathy": empathy,
        }

        severity_penalty = {
            "low": 3,
            "medium": 8,
            "high": 18,
            "critical": 30,
        }
        risk_penalty = sum(severity_penalty[risk.severity] for risk in risks[:2])
        overall = _clamp(
            momentum.score * 0.35
            + tone.score * 0.2
            + clarity.score * 0.22
            + empathy.score * 0.23
            - risk_penalty
        )
        if responsible_use.behavior == "redirected":
            overall = min(overall, 45)
        status = "healthy" if overall >= 72 else "watch" if overall >= 46 else "at_risk"

        suggestions = self._build_suggestions(
            request=request,
            fingerprint=fingerprint,
            unanswered=unanswered,
            signals=signals,
            responsible_use=responsible_use,
            risks=risks,
            playbook_refs=list(playbook_refs),
        )

        persisted = request.data_handling.persist_analysis
        expires_at = None
        if persisted:
            from datetime import timedelta

            expires_at = now + timedelta(days=request.data_handling.retention_days)

        return AnalysisResponse(
            analysis_id=analysis_id,
            conversation_id=request.conversation_id,
            mode=request.mode,
            fingerprint=fingerprint,
            created_at=now,
            overall_score=overall,
            status=status,
            signals=signals,
            unanswered_questions=unanswered,
            risks=risks,
            suggestions=suggestions,
            responsible_use=responsible_use,
            limitations=COMMON_LIMITATIONS,
            persisted=persisted,
            expires_at=expires_at,
        )

    def _fingerprint(self, request: AnalyzeRequest) -> str:
        canonical = {
            "mode": request.mode.value,
            "turns": [
                {
                    "speaker": _normalize(turn.speaker).casefold(),
                    "role": turn.role.value,
                    "text": _normalize(turn.text),
                }
                for turn in request.turns
            ],
            "context": {
                "goal": _normalize(request.context.goal),
                "stage": _normalize(request.context.stage),
                "known_facts": [_normalize(item) for item in request.context.known_facts],
            },
        }
        encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()

    def _momentum_signal(
        self,
        request: AnalyzeRequest,
        unanswered: list[UnansweredQuestion],
        confidence: float,
    ) -> Signal:
        turns = request.turns
        roles = Counter(turn.role for turn in turns)
        active_roles = roles[SpeakerRole.OPERATOR] + roles[SpeakerRole.PARTICIPANT]
        balance = 0.0
        if active_roles:
            balance = (
                1 - abs(roles[SpeakerRole.OPERATOR] - roles[SpeakerRole.PARTICIPANT]) / active_roles
            )
        words = _words(" ".join(turn.text for turn in turns))
        movement = sum(1 for word in words if word in POSITIVE_MOVEMENT)
        stalling = sum(1 for word in words if word in STALLING_WORDS)
        last_participant = next(
            (turn for turn in reversed(turns) if turn.role is SpeakerRole.PARTICIPANT),
            None,
        )
        engagement_bonus = 0
        if last_participant:
            engagement_bonus = min(8, len(_words(last_participant.text)) / 4)
        score = (
            43
            + min(len(turns), 12) * 1.7
            + balance * 17
            + min(movement, 6) * 2
            + engagement_bonus
            - min(stalling, 5) * 4
            - len(unanswered) * 8
        )
        final = _clamp(score)
        label = (
            "building"
            if final >= 72
            else "steady"
            if final >= 52
            else "fragile"
            if final >= 32
            else "stalled"
        )
        evidence = [
            f"{roles[SpeakerRole.OPERATOR]} operator and {roles[SpeakerRole.PARTICIPANT]} participant turns",
        ]
        if unanswered:
            evidence.append(f"{len(unanswered)} participant question(s) remain open")
        if movement:
            evidence.append(f"{movement} observable forward-motion cue(s)")
        return Signal(
            score=final,
            label=label,
            explanation=(
                "Momentum combines turn balance, observable forward-motion language, "
                "recent engagement, stalling cues, and unanswered questions."
            ),
            evidence=evidence,
            confidence=round(confidence, 2),
        )

    def _tone_signal(self, request: AnalyzeRequest, confidence: float) -> Signal:
        combined = " ".join(turn.text for turn in request.turns)
        words = _words(combined)
        warmth = sum(1 for word in words if word in WARMTH_WORDS)
        friction = sum(1 for word in words if word in FRICTION_WORDS)
        caps = len(ALL_CAPS_RE.findall(combined))
        exclamations = min(combined.count("!"), 5)
        score = _clamp(68 + warmth * 4 - friction * 8 - caps * 6 - exclamations * 2)
        label = (
            "supportive"
            if score >= 76
            else "neutral"
            if score >= 55
            else "strained"
            if score >= 30
            else "hostile"
        )
        evidence: list[str] = []
        if warmth:
            evidence.append(f"{warmth} warmth or courtesy cue(s)")
        if friction:
            evidence.append(f"{friction} frustration or friction cue(s)")
        if caps or exclamations:
            evidence.append(f"{caps} all-caps token(s), {exclamations} exclamation mark(s)")
        if not evidence:
            evidence.append("No strong warmth or friction cue dominates the transcript")
        return Signal(
            score=score,
            label=label,
            explanation=(
                "Tone reflects visible courtesy, frustration, emphasis, and hostile-language "
                "cues; it does not claim to identify anyone's emotional state."
            ),
            evidence=evidence,
            confidence=round(confidence * 0.94, 2),
        )

    def _clarity_signal(self, request: AnalyzeRequest, confidence: float) -> Signal:
        operator_turns = [turn.text for turn in request.turns if turn.role is SpeakerRole.OPERATOR]
        source = operator_turns or [turn.text for turn in request.turns]
        words = [word for text in source for word in _words(text)]
        sentences = [
            sentence for text in source for sentence in SENTENCE_RE.split(text) if sentence.strip()
        ]
        avg_sentence = len(words) / max(1, len(sentences))
        vague = sum(1 for word in words if word in VAGUE_WORDS)
        specificity = len(
            re.findall(
                r"\b(?:\d{1,2}:\d{2}|(?:mon|tues|wednes|thurs|fri|satur|sun)day|today|tomorrow|\d+\s+(?:minutes?|hours?|days?))\b",
                " ".join(source),
                re.I,
            )
        )
        score = 78 - max(0, avg_sentence - 20) * 1.8 - vague * 5 + min(specificity, 4) * 4
        if not operator_turns:
            score -= 12
        final = _clamp(score)
        label = (
            "crisp"
            if final >= 78
            else "clear"
            if final >= 60
            else "mixed"
            if final >= 40
            else "unclear"
        )
        evidence = [
            f"Average operator sentence length: {avg_sentence:.1f} words",
            f"{vague} vague qualifier(s); {specificity} concrete time or quantity cue(s)",
        ]
        return Signal(
            score=final,
            label=label,
            explanation=(
                "Clarity considers sentence length, vague qualifiers, and concrete "
                "time/quantity cues in operator language."
            ),
            evidence=evidence,
            confidence=round(confidence * 0.9, 2),
        )

    def _empathy_signal(self, request: AnalyzeRequest, confidence: float) -> Signal:
        operator_text = " ".join(
            turn.text.lower() for turn in request.turns if turn.role is SpeakerRole.OPERATOR
        )
        participant_text = " ".join(
            turn.text.lower() for turn in request.turns if turn.role is SpeakerRole.PARTICIPANT
        )
        empathy_hits = sum(operator_text.count(phrase) for phrase in EMPATHY_PHRASES)
        impact_present = any(
            word in participant_text
            for word in (
                "frustrated",
                "worried",
                "deadline",
                "blocked",
                "concerned",
                "confused",
                "upset",
                "unsafe",
            )
        )
        acknowledgment = any(
            phrase in operator_text
            for phrase in (
                "you mentioned",
                "i heard",
                "it sounds",
                "that impact",
                "your deadline",
                "your concern",
            )
        )
        score = 58 + empathy_hits * 14 + (10 if acknowledgment else 0)
        if impact_present and not (empathy_hits or acknowledgment):
            score -= 24
        if not operator_text:
            score = 38
        final = _clamp(score)
        label = (
            "attuned"
            if final >= 76
            else "present"
            if final >= 58
            else "thin"
            if final >= 38
            else "missing"
        )
        evidence = [f"{empathy_hits} explicit acknowledgment phrase(s)"]
        if impact_present:
            evidence.append("Participant language includes an impact or concern cue")
        else:
            evidence.append("No strong impact cue was detected; empathy may be less salient here")
        return Signal(
            score=final,
            label=label,
            explanation=(
                "Empathy measures explicit acknowledgment of stated impact or concern. "
                "It never diagnoses emotion or personality."
            ),
            evidence=evidence,
            confidence=round(confidence * (0.9 if impact_present else 0.78), 2),
        )

    def _unanswered_questions(self, turns: list) -> list[UnansweredQuestion]:
        unanswered: list[UnansweredQuestion] = []
        for index, turn in enumerate(turns):
            if turn.role is not SpeakerRole.PARTICIPANT:
                continue
            for question in _question_segments(turn.text):
                later_operator = " ".join(
                    later.text.lower()
                    for later in turns[index + 1 :]
                    if later.role is SpeakerRole.OPERATOR
                )
                question_words = set(_words(question))
                topics = [
                    topic
                    for topic, synonyms in TOPICS.items()
                    if question_words.intersection(synonyms)
                ]
                if topics:
                    missing_topics = [
                        topic
                        for topic in topics
                        if not set(_words(later_operator)).intersection(TOPICS[topic])
                    ]
                    for topic in missing_topics:
                        unanswered.append(
                            UnansweredQuestion(
                                question=redact_evidence(question, 280),
                                topic=topic.replace("_", " "),
                                asked_by=turn.speaker,
                                turn_index=index,
                                confidence=0.88,
                            )
                        )
                    continue

                meaningful = question_words - STOPWORDS
                overlap = meaningful.intersection(_words(later_operator))
                answered = bool(later_operator) and (
                    len(overlap) >= max(1, math.ceil(len(meaningful) * 0.25))
                )
                if not answered:
                    unanswered.append(
                        UnansweredQuestion(
                            question=redact_evidence(question, 280),
                            topic="general question",
                            asked_by=turn.speaker,
                            turn_index=index,
                            confidence=0.68,
                        )
                    )
        # Preserve order while preventing repeated topic records from one turn.
        unique: dict[tuple[int, str], UnansweredQuestion] = {}
        for item in unanswered:
            unique.setdefault((item.turn_index, item.topic), item)
        return list(unique.values())[:12]

    def _build_suggestions(
        self,
        *,
        request: AnalyzeRequest,
        fingerprint: str,
        unanswered: list[UnansweredQuestion],
        signals: dict[str, Signal],
        responsible_use: ResponsibleUse,
        risks: list,
        playbook_refs: list[str],
    ) -> list[Suggestion]:
        suggestions: list[Suggestion] = []
        base_confidence = min(0.9, 0.5 + len(request.turns) * 0.035)

        def add(
            category: str,
            priority: str,
            title: str,
            action: str,
            example: str,
            rationale: str,
            evidence: list[str],
            confidence: float,
        ) -> None:
            number = len(suggestions) + 1
            suggestions.append(
                Suggestion(
                    id=f"sug_{fingerprint[:16]}_{number}",
                    category=category,
                    priority=priority,
                    title=title,
                    action=action,
                    example_language=example,
                    rationale=rationale,
                    evidence=evidence[:6],
                    confidence=round(max(0.35, min(0.92, confidence)), 2),
                    limitations=COMMON_LIMITATIONS,
                    playbook_refs=playbook_refs[:8],
                )
            )

        if responsible_use.behavior == "redirected":
            add(
                "responsible_use_boundary",
                "now",
                "Replace the unsafe objective",
                responsible_use.explanation,
                (
                    "Draft to adapt: “I can help make this clear and effective while keeping "
                    "the message transparent, voluntary, and based only on relevant facts.”"
                ),
                (
                    "The requested objective included a prohibited capability. Coaching can "
                    "continue only with a transparent, non-discriminatory, human-controlled goal."
                ),
                [f"Boundary: {capability}" for capability in responsible_use.blocked_capabilities],
                0.94,
            )

        if risks:
            top_risk = sorted(
                risks,
                key=lambda item: {
                    "low": 0,
                    "medium": 1,
                    "high": 2,
                    "critical": 3,
                }[item.severity],
                reverse=True,
            )[0]
            add(
                "safety_and_escalation",
                "now",
                "Use the safety boundary before coaching",
                top_risk.recommended_boundary,
                (
                    "Draft to adapt: “I’m pausing the normal conversation path so this can "
                    "be reviewed through the appropriate safety or escalation process.”"
                ),
                top_risk.explanation,
                top_risk.evidence,
                0.9,
            )

        if unanswered:
            topics = ", ".join(dict.fromkeys(item.topic for item in unanswered[:3]))
            evidence = [item.question for item in unanswered[:3]]
            add(
                "answer_open_question",
                "now",
                "Answer the open loop directly",
                (
                    f"Address the outstanding {topics} question(s) before introducing a "
                    "new ask. If the answer is unknown, state what is known, what is not, "
                    "and when a verified answer will be available."
                ),
                (
                    "Draft to adapt: “You asked about "
                    f"{topics}. Here is the confirmed answer; where it is still uncertain, "
                    "I’ll label the estimate and the next verification point.”"
                ),
                "Direct answers reduce avoidable friction and show that the participant was heard.",
                evidence,
                base_confidence + 0.05,
            )

        if signals["empathy"].score < 58:
            participant_evidence = [
                redact_evidence(turn.text)
                for turn in request.turns
                if turn.role is SpeakerRole.PARTICIPANT
                and any(
                    cue in turn.text.lower()
                    for cue in (
                        "frustrated",
                        "deadline",
                        "blocked",
                        "concern",
                        "confused",
                        "upset",
                    )
                )
            ]
            add(
                "acknowledge_impact",
                "next",
                "Acknowledge impact without overclaiming",
                (
                    "Reflect the specific impact the participant stated, then move to facts "
                    "or action. Avoid claiming to know how they feel."
                ),
                (
                    "Draft to adapt: “I hear that this is affecting your deadline. "
                    "I’ll focus on the next concrete step and keep the uncertainty explicit.”"
                ),
                "Specific acknowledgment can restore trust while avoiding emotional inference.",
                participant_evidence or signals["empathy"].evidence,
                base_confidence,
            )

        mode_copy = MODE_COPY[request.mode]
        add(
            mode_copy["advance_category"],
            "next",
            mode_copy["advance_title"],
            mode_copy["advance_action"],
            mode_copy["advance_example"],
            mode_copy["advance_rationale"],
            [
                f"Mode: {request.mode.value}",
                f"Momentum: {signals['momentum'].label} ({signals['momentum'].score})",
            ],
            base_confidence,
        )

        if signals["clarity"].score < 62 and len(suggestions) < 5:
            add(
                "clarify_commitment",
                "optional",
                "Turn the next step into a checkable commitment",
                (
                    "Use one owner, one action, and one realistic checkpoint. Remove vague "
                    "qualifiers unless the uncertainty itself is important."
                ),
                (
                    "Draft to adapt: “I own the next check. I’ll update you by [realistic "
                    "time], including what is confirmed and what is still open.”"
                ),
                "Concrete ownership and timing improve clarity without making promises the operator cannot keep.",
                signals["clarity"].evidence,
                base_confidence - 0.04,
            )

        return suggestions[:5]
