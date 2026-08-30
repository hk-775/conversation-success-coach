"""Fictional, deterministic demo scenarios."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from conversation_success_coach.analysis import ConversationAnalyzer
from conversation_success_coach.repository import Repository
from conversation_success_coach.schemas import (
    AnalyzeRequest,
    ConversationContext,
    ConversationMode,
    DataHandling,
    FeedbackCreate,
    FeedbackKind,
    OutcomeKind,
    PlaybookCreate,
    SpeakerRole,
    Turn,
)

SEED_VERSION = "2026-08-30.1"


PLAYBOOKS: tuple[tuple[str, PlaybookCreate], ...] = (
    (
        "pb_sales_discovery",
        PlaybookCreate(
            name="Transparent discovery",
            mode=ConversationMode.SALES,
            description="Advance a buying conversation without pressure or hidden persuasion.",
            principles=[
                "Answer pricing and feasibility questions before introducing a new ask.",
                "Summarize the buyer's stated needs; do not invent hidden motives.",
                "Use permission-based next steps and only real deadlines.",
            ],
        ),
    ),
    (
        "pb_support_recovery",
        PlaybookCreate(
            name="Impact, ownership, checkpoint",
            mode=ConversationMode.SUPPORT,
            description="Restore trust during incidents with clear ownership and realistic updates.",
            principles=[
                "Acknowledge the stated impact without diagnosing emotion.",
                "Name the next action, owner, and update checkpoint.",
                "Escalate safety, privacy, or formal complaint signals through policy.",
            ],
        ),
    ),
    (
        "pb_recruiting_fair_process",
        PlaybookCreate(
            name="Fair and legible candidate process",
            mode=ConversationMode.RECRUITING,
            description="Keep candidate communication consistent, relevant, and reviewable.",
            principles=[
                "Use job-relevant criteria and the same documented process for everyone.",
                "Never infer protected attributes or mental-health status.",
                "Distinguish confirmed process facts from timeline estimates.",
            ],
        ),
    ),
    (
        "pb_community_deescalation",
        PlaybookCreate(
            name="Behavior-specific moderation",
            mode=ConversationMode.COMMUNITY,
            description="De-escalate conflict while preserving consistent, appealable norms.",
            principles=[
                "Moderate observable behavior, not identity, personality, or assumed intent.",
                "Apply the same published rule to all participants.",
                "Preserve a pause, review, or appeal path.",
            ],
        ),
    ),
)


SCENARIOS: tuple[dict, ...] = (
    {
        "id": "conv_sales_northstar",
        "title": "Northstar analytics discovery",
        "mode": ConversationMode.SALES,
        "owner": "Maya Chen",
        "participant_label": "Theo Brooks",
        "goal": "Determine fit and agree on a transparent technical next step.",
        "stage": "Discovery",
        "age_hours": 18,
        "turns": [
            (
                SpeakerRole.OPERATOR,
                "Maya Chen",
                "Thanks for walking me through the reporting bottleneck. Which part is creating the most rework?",
            ),
            (
                SpeakerRole.PARTICIPANT,
                "Theo Brooks",
                "The handoff from our warehouse is fragile, and finance spends two days reconciling every month.",
            ),
            (
                SpeakerRole.OPERATOR,
                "Maya Chen",
                "That helps. Our connector can validate the handoff before the finance workflow starts.",
            ),
            (
                SpeakerRole.PARTICIPANT,
                "Theo Brooks",
                "How would migration work, and what does pricing look like for 40 analysts?",
            ),
            (
                SpeakerRole.OPERATOR,
                "Maya Chen",
                "Migration usually starts with a read-only schema review and a staged parallel run.",
            ),
        ],
        "feedback": ("accepted", "advanced"),
    },
    {
        "id": "conv_support_bluebird",
        "title": "Bluebird export incident",
        "mode": ConversationMode.SUPPORT,
        "owner": "Imani Cole",
        "participant_label": "Rowan Hart",
        "goal": "Restore export access and establish a trustworthy update cadence.",
        "stage": "Escalated investigation",
        "age_hours": 7,
        "turns": [
            (
                SpeakerRole.PARTICIPANT,
                "Rowan Hart",
                "The CSV export has failed three times since the update. This is blocking our board deadline and I am frustrated.",
            ),
            (
                SpeakerRole.OPERATOR,
                "Imani Cole",
                "Can you share the job ID and browser version?",
            ),
            (
                SpeakerRole.PARTICIPANT,
                "Rowan Hart",
                "Job 48317, Firefox 128. I already sent this yesterday. When will someone own the fix?",
            ),
            (
                SpeakerRole.OPERATOR,
                "Imani Cole",
                "I can see the previous ticket. I am checking whether the export worker retried after the release.",
            ),
        ],
        "feedback": ("accepted", "resolved"),
    },
    {
        "id": "conv_recruiting_harborline",
        "title": "Harborline engineering screen",
        "mode": ConversationMode.RECRUITING,
        "owner": "Jordan Vale",
        "participant_label": "Nia Mercer",
        "goal": "Give the candidate an accurate, fair view of the role and process.",
        "stage": "Post-screen follow-up",
        "age_hours": 30,
        "turns": [
            (
                SpeakerRole.OPERATOR,
                "Jordan Vale",
                "Thank you for the thoughtful architecture discussion. The team appreciated the tradeoffs you surfaced.",
            ),
            (
                SpeakerRole.PARTICIPANT,
                "Nia Mercer",
                "I enjoyed it too. Is the role fully remote, and what is the interview timeline from here?",
            ),
            (
                SpeakerRole.OPERATOR,
                "Jordan Vale",
                "The panel review is Tuesday, and I expect to have an update within two business days after that.",
            ),
            (
                SpeakerRole.PARTICIPANT,
                "Nia Mercer",
                "Great, thank you. The remote policy is important for me before I schedule the next stage.",
            ),
        ],
        "feedback": ("rejected", "no_change"),
    },
    {
        "id": "conv_community_cedar",
        "title": "Cedar Commons heated thread",
        "mode": ConversationMode.COMMUNITY,
        "owner": "Sam Ortiz",
        "participant_label": "Cedar Commons members",
        "goal": "De-escalate the thread and apply community norms consistently.",
        "stage": "Active moderation",
        "age_hours": 3,
        "turns": [
            (
                SpeakerRole.PARTICIPANT,
                "Avery Moss",
                "That proposal ignores every concern raised last week.",
            ),
            (
                SpeakerRole.PARTICIPANT,
                "Drew Lane",
                "Your idea is clueless. I will keep tagging you until you answer.",
            ),
            (
                SpeakerRole.OPERATOR,
                "Sam Ortiz",
                "Please keep the discussion productive.",
            ),
            (
                SpeakerRole.PARTICIPANT,
                "Avery Moss",
                "Can a moderator explain which rule applies here and whether the thread should pause?",
            ),
        ],
        "feedback": ("accepted", "resolved"),
    },
)


def seed_demo(
    repository: Repository,
    analyzer: ConversationAnalyzer,
    *,
    reset: bool = False,
    now: datetime | None = None,
) -> None:
    if repository.get_metadata("seed_version") == SEED_VERSION and not reset:
        return
    if reset:
        repository.clear_all()

    base = now or datetime.now(UTC)
    for playbook_id, playbook in PLAYBOOKS:
        repository.insert_playbook(
            playbook_id=playbook_id,
            data=playbook,
            is_demo=True,
            created_at=base - timedelta(days=14),
        )

    first_suggestions: dict[str, str] = {}
    for scenario_index, scenario in enumerate(SCENARIOS):
        created = base - timedelta(hours=scenario["age_hours"])
        repository.insert_conversation(
            conversation_id=scenario["id"],
            title=scenario["title"],
            mode=scenario["mode"],
            owner=scenario["owner"],
            participant_label=scenario["participant_label"],
            goal=scenario["goal"],
            stage=scenario["stage"],
            is_demo=True,
            created_at=created,
        )
        turns: list[Turn] = []
        for position, (role, speaker, text) in enumerate(scenario["turns"]):
            turn = Turn(
                speaker=speaker,
                role=role,
                text=text,
                timestamp=created + timedelta(minutes=position * 7),
            )
            turns.append(turn)
            repository.insert_turn(
                conversation_id=scenario["id"],
                position=position,
                turn=turn,
                created_at=turn.timestamp or created,
                turn_id=f"turn_seed_{scenario_index}_{position}",
            )

        request = AnalyzeRequest(
            mode=scenario["mode"],
            turns=turns,
            conversation_id=scenario["id"],
            context=ConversationContext(
                goal=scenario["goal"],
                stage=scenario["stage"],
            ),
            data_handling=DataHandling(
                persist_analysis=True,
                retention_days=30,
            ),
        )
        playbook_refs = [
            item["id"]
            for item in repository.list_playbooks(
                scenario["mode"],
                enabled_only=True,
            )
        ]
        analysis = analyzer.analyze(
            request,
            created_at=created + timedelta(minutes=45),
            playbook_refs=playbook_refs,
        ).model_copy(update={"expires_at": None})
        repository.save_analysis(
            analysis,
            raw_content_stored=True,
            is_demo=True,
        )
        first_suggestions[scenario["id"]] = analysis.suggestions[0].id

    for index, scenario in enumerate(SCENARIOS):
        feedback_kind, outcome = scenario["feedback"]
        repository.insert_feedback(
            FeedbackCreate(
                kind=FeedbackKind(feedback_kind),
                suggestion_id=first_suggestions[scenario["id"]],
            ),
            feedback_id=f"fb_seed_{index}_suggestion",
            created_at=base - timedelta(hours=max(1, scenario["age_hours"] - 1)),
            actor="demo-operator",
        )
        repository.insert_feedback(
            FeedbackCreate(
                kind=FeedbackKind.OUTCOME,
                conversation_id=scenario["id"],
                outcome=OutcomeKind(outcome),
                note="Fictional demo outcome.",
            ),
            feedback_id=f"fb_seed_{index}_outcome",
            created_at=base - timedelta(minutes=30),
            actor="demo-operator",
        )

    repository.set_metadata("seed_version", SEED_VERSION)
    repository.set_metadata("seeded_at", base.isoformat())
    repository.add_audit(
        "demo.seeded",
        actor="system",
        resource_type="dataset",
        resource_id=SEED_VERSION,
        summary="Loaded the fictional local demo dataset.",
        details={
            "scenario_count": len(SCENARIOS),
            "playbook_count": len(PLAYBOOKS),
            "external_calls": 0,
            "fictional_data": True,
        },
        created_at=base,
    )
