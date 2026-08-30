"""Persistence operations with content-minimized audit records."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from conversation_success_coach.database import Database
from conversation_success_coach.schemas import (
    AnalysisResponse,
    ConversationCreate,
    ConversationMode,
    FeedbackCreate,
    FeedbackKind,
    PlaybookCreate,
    PlaybookUpdate,
    PrivacySettingsUpdate,
    Turn,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


def iso(value: datetime | None = None) -> str:
    return (value or utc_now()).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _row_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


class Repository:
    def __init__(self, database: Database) -> None:
        self.db = database
        now = iso()
        self.db.execute(
            """
            INSERT INTO privacy_settings (
                id, allow_raw_content_storage,
                default_analysis_retention_days, audit_retention_days, updated_at
            ) VALUES (1, 0, 7, 30, ?)
            ON CONFLICT(id) DO NOTHING
            """,
            (now,),
        )

    # Metadata and seed lifecycle

    def get_metadata(self, key: str) -> str | None:
        row = self.db.query_one("SELECT value FROM metadata WHERE key = ?", (key,))
        return str(row["value"]) if row else None

    def set_metadata(self, key: str, value: str) -> None:
        self.db.execute(
            """
            INSERT INTO metadata (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )

    def clear_all(self) -> None:
        with self.db.transaction() as conn:
            for table in (
                "feedback",
                "suggestions",
                "analyses",
                "turns",
                "conversations",
                "playbooks",
                "audit",
                "metadata",
            ):
                conn.execute(f"DELETE FROM {table}")
            conn.execute(
                """
                UPDATE privacy_settings
                SET allow_raw_content_storage = 0,
                    default_analysis_retention_days = 7,
                    audit_retention_days = 30,
                    updated_at = ?
                WHERE id = 1
                """,
                (iso(),),
            )

    # Audit

    def add_audit(
        self,
        event_type: str,
        *,
        actor: str = "local-operator",
        resource_type: str,
        resource_id: str | None,
        summary: str,
        details: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        audit_id: str | None = None,
    ) -> str:
        item_id = audit_id or f"aud_{uuid4().hex[:18]}"
        self.db.execute(
            """
            INSERT INTO audit (
                id, event_type, actor, resource_type, resource_id,
                summary, details_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id,
                event_type,
                actor,
                resource_type,
                resource_id,
                summary,
                _json(details or {}),
                iso(created_at),
            ),
        )
        return item_id

    def list_audit(
        self,
        *,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if event_type:
            rows = self.db.query_all(
                """
                SELECT * FROM audit
                WHERE event_type = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (event_type, limit),
            )
        else:
            rows = self.db.query_all(
                "SELECT * FROM audit ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
        return [
            {
                **_row_dict(row),
                "details": json.loads(row["details_json"]),
                "content_minimized": True,
            }
            for row in rows
        ]

    # Conversations and turns

    def insert_conversation(
        self,
        *,
        conversation_id: str,
        title: str,
        mode: ConversationMode | str,
        owner: str,
        participant_label: str,
        goal: str,
        stage: str,
        is_demo: bool,
        created_at: datetime,
        expires_at: datetime | None = None,
    ) -> str:
        mode_value = mode.value if isinstance(mode, ConversationMode) else mode
        self.db.execute(
            """
            INSERT INTO conversations (
                id, title, mode, owner, participant_label, goal, stage,
                status, is_demo, created_at, updated_at, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?)
            """,
            (
                conversation_id,
                title,
                mode_value,
                owner,
                participant_label,
                goal,
                stage,
                int(is_demo),
                iso(created_at),
                iso(created_at),
                iso(expires_at) if expires_at else None,
            ),
        )
        return conversation_id

    def create_conversation(self, data: ConversationCreate) -> dict[str, Any]:
        from datetime import timedelta

        now = utc_now()
        conversation_id = f"conv_{uuid4().hex[:16]}"
        self.insert_conversation(
            conversation_id=conversation_id,
            title=data.title,
            mode=data.mode,
            owner=data.owner,
            participant_label=data.participant_label,
            goal=data.goal,
            stage=data.stage,
            is_demo=False,
            created_at=now,
            expires_at=now + timedelta(days=data.retention_days),
        )
        self.add_audit(
            "conversation.created",
            resource_type="conversation",
            resource_id=conversation_id,
            summary="Created a consented local conversation workspace.",
            details={
                "mode": data.mode.value,
                "retention_days": data.retention_days,
                "raw_text_in_audit": False,
            },
        )
        return self.get_conversation(conversation_id) or {}

    def insert_turn(
        self,
        *,
        conversation_id: str,
        position: int,
        turn: Turn,
        created_at: datetime,
        turn_id: str | None = None,
    ) -> str:
        item_id = turn_id or f"turn_{uuid4().hex[:18]}"
        self.db.execute(
            """
            INSERT INTO turns (
                id, conversation_id, position, speaker, role, text, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id,
                conversation_id,
                position,
                turn.speaker,
                turn.role.value,
                turn.text,
                iso(turn.timestamp or created_at),
            ),
        )
        self.db.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (iso(created_at), conversation_id),
        )
        return item_id

    def add_turn(self, conversation_id: str, turn: Turn) -> dict[str, Any]:
        row = self.db.query_one(
            "SELECT COALESCE(MAX(position), -1) AS max_position FROM turns WHERE conversation_id = ?",
            (conversation_id,),
        )
        position = int(row["max_position"]) + 1 if row else 0
        now = utc_now()
        turn_id = self.insert_turn(
            conversation_id=conversation_id,
            position=position,
            turn=turn,
            created_at=now,
        )
        self.add_audit(
            "conversation.turn_added",
            resource_type="conversation",
            resource_id=conversation_id,
            summary="Added a turn to the local transcript.",
            details={
                "turn_id": turn_id,
                "role": turn.role.value,
                "character_count": len(turn.text),
                "raw_text_in_audit": False,
            },
        )
        return {
            "id": turn_id,
            "conversation_id": conversation_id,
            "position": position,
            **turn.model_dump(mode="json"),
        }

    def replace_turns(self, conversation_id: str, turns: list[Turn]) -> None:
        now = utc_now()
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM turns WHERE conversation_id = ?", (conversation_id,))
            conn.executemany(
                """
                INSERT INTO turns (
                    id, conversation_id, position, speaker, role, text, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        f"turn_{uuid4().hex[:18]}",
                        conversation_id,
                        position,
                        turn.speaker,
                        turn.role.value,
                        turn.text,
                        iso(turn.timestamp or now),
                    )
                    for position, turn in enumerate(turns)
                ],
            )
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (iso(now), conversation_id),
            )

    def get_conversation(self, conversation_id: str) -> dict[str, Any] | None:
        row = self.db.query_one(
            "SELECT * FROM conversations WHERE id = ?",
            (conversation_id,),
        )
        if not row:
            return None
        turns = self.db.query_all(
            """
            SELECT id, position, speaker, role, text, created_at
            FROM turns WHERE conversation_id = ?
            ORDER BY position
            """,
            (conversation_id,),
        )
        analysis = self.db.query_one(
            """
            SELECT result_json FROM analyses
            WHERE conversation_id = ?
            ORDER BY created_at DESC LIMIT 1
            """,
            (conversation_id,),
        )
        payload = _row_dict(row)
        payload["is_demo"] = bool(payload["is_demo"])
        payload["turns"] = [_row_dict(item) for item in turns]
        payload["latest_analysis"] = json.loads(analysis["result_json"]) if analysis else None
        return payload

    def list_conversations(
        self,
        mode: ConversationMode | None = None,
    ) -> list[dict[str, Any]]:
        params: tuple[Any, ...] = ()
        where = ""
        if mode:
            where = "WHERE c.mode = ?"
            params = (mode.value,)
        rows = self.db.query_all(
            f"""
            SELECT c.*,
                   COUNT(t.id) AS turn_count,
                   (
                       SELECT text FROM turns lt
                       WHERE lt.conversation_id = c.id
                       ORDER BY lt.position DESC LIMIT 1
                   ) AS last_message,
                   (
                       SELECT result_json FROM analyses la
                       WHERE la.conversation_id = c.id
                       ORDER BY la.created_at DESC LIMIT 1
                   ) AS latest_analysis_json
            FROM conversations c
            LEFT JOIN turns t ON t.conversation_id = c.id
            {where}
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            """,
            params,
        )
        output: list[dict[str, Any]] = []
        for row in rows:
            item = _row_dict(row)
            item["is_demo"] = bool(item["is_demo"])
            analysis_json = item.pop("latest_analysis_json")
            item["latest_analysis"] = json.loads(analysis_json) if analysis_json else None
            if item["last_message"]:
                item["last_message"] = str(item["last_message"])[:180]
            output.append(item)
        return output

    # Analyses and feedback

    def save_analysis(
        self,
        analysis: AnalysisResponse,
        *,
        raw_content_stored: bool,
        is_demo: bool = False,
    ) -> None:
        payload = analysis.model_dump(mode="json")
        self.db.execute(
            """
            INSERT INTO analyses (
                id, conversation_id, mode, fingerprint, result_json,
                raw_content_stored, is_demo, created_at, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                conversation_id = excluded.conversation_id,
                mode = excluded.mode,
                fingerprint = excluded.fingerprint,
                result_json = excluded.result_json,
                raw_content_stored = excluded.raw_content_stored,
                is_demo = excluded.is_demo,
                created_at = excluded.created_at,
                expires_at = excluded.expires_at
            """,
            (
                analysis.analysis_id,
                analysis.conversation_id,
                analysis.mode.value,
                analysis.fingerprint,
                _json(payload),
                int(raw_content_stored),
                int(is_demo),
                iso(analysis.created_at),
                iso(analysis.expires_at) if analysis.expires_at else None,
            ),
        )
        for suggestion in analysis.suggestions:
            suggestion_payload = suggestion.model_dump(mode="json")
            self.db.execute(
                """
                INSERT INTO suggestions (
                    id, analysis_id, conversation_id, mode, category,
                    title, action, confidence, status, payload_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    analysis_id = excluded.analysis_id,
                    conversation_id = excluded.conversation_id,
                    mode = excluded.mode,
                    category = excluded.category,
                    title = excluded.title,
                    action = excluded.action,
                    confidence = excluded.confidence,
                    payload_json = excluded.payload_json,
                    created_at = excluded.created_at
                """,
                (
                    suggestion.id,
                    analysis.analysis_id,
                    analysis.conversation_id,
                    analysis.mode.value,
                    suggestion.category,
                    suggestion.title,
                    suggestion.action,
                    suggestion.confidence,
                    _json(suggestion_payload),
                    iso(analysis.created_at),
                ),
            )
        self.add_audit(
            "analysis.generated",
            resource_type="analysis",
            resource_id=analysis.analysis_id,
            summary="Generated deterministic conversation coaching.",
            details={
                "conversation_id": analysis.conversation_id,
                "mode": analysis.mode.value,
                "fingerprint_prefix": analysis.fingerprint[:12],
                "suggestion_count": len(analysis.suggestions),
                "raw_content_stored": raw_content_stored,
                "blocked_capabilities": analysis.responsible_use.blocked_capabilities,
            },
            created_at=analysis.created_at,
        )

    def get_suggestion(self, suggestion_id: str) -> dict[str, Any] | None:
        row = self.db.query_one(
            "SELECT * FROM suggestions WHERE id = ?",
            (suggestion_id,),
        )
        if not row:
            return None
        item = _row_dict(row)
        item["payload"] = json.loads(item["payload_json"])
        return item

    def insert_feedback(
        self,
        feedback: FeedbackCreate,
        *,
        feedback_id: str | None = None,
        created_at: datetime | None = None,
        actor: str = "local-operator",
    ) -> dict[str, Any]:
        item_id = feedback_id or f"fb_{uuid4().hex[:18]}"
        now = created_at or utc_now()
        self.db.execute(
            """
            INSERT INTO feedback (
                id, suggestion_id, conversation_id, kind, outcome, note, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id,
                feedback.suggestion_id,
                feedback.conversation_id,
                feedback.kind.value,
                feedback.outcome.value if feedback.outcome else None,
                feedback.note,
                iso(now),
            ),
        )
        if feedback.suggestion_id and feedback.kind in {
            FeedbackKind.ACCEPTED,
            FeedbackKind.REJECTED,
        }:
            self.db.execute(
                "UPDATE suggestions SET status = ? WHERE id = ?",
                (feedback.kind.value, feedback.suggestion_id),
            )
        self.add_audit(
            f"feedback.{feedback.kind.value}",
            actor=actor,
            resource_type="feedback",
            resource_id=item_id,
            summary=f"Recorded {feedback.kind.value} coaching feedback.",
            details={
                "suggestion_id": feedback.suggestion_id,
                "conversation_id": feedback.conversation_id,
                "outcome": feedback.outcome.value if feedback.outcome else None,
                "note_recorded": bool(feedback.note),
                "note_in_audit": False,
            },
            created_at=now,
        )
        return {
            "id": item_id,
            **feedback.model_dump(mode="json"),
            "created_at": iso(now),
        }

    def list_feedback(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.db.query_all(
            "SELECT * FROM feedback ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        return [_row_dict(row) for row in rows]

    # Playbooks

    def list_playbooks(
        self,
        mode: ConversationMode | None = None,
        *,
        enabled_only: bool = False,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if mode:
            clauses.append("mode = ?")
            params.append(mode.value)
        if enabled_only:
            clauses.append("enabled = 1")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self.db.query_all(
            f"SELECT * FROM playbooks {where} ORDER BY mode, name",
            params,
        )
        return [
            {
                **_row_dict(row),
                "principles": json.loads(row["principles_json"]),
                "enabled": bool(row["enabled"]),
                "is_demo": bool(row["is_demo"]),
            }
            for row in rows
        ]

    def get_playbook(self, playbook_id: str) -> dict[str, Any] | None:
        row = self.db.query_one(
            "SELECT * FROM playbooks WHERE id = ?",
            (playbook_id,),
        )
        if not row:
            return None
        return {
            **_row_dict(row),
            "principles": json.loads(row["principles_json"]),
            "enabled": bool(row["enabled"]),
            "is_demo": bool(row["is_demo"]),
        }

    def insert_playbook(
        self,
        *,
        playbook_id: str,
        data: PlaybookCreate,
        is_demo: bool,
        created_at: datetime,
    ) -> str:
        self.db.execute(
            """
            INSERT INTO playbooks (
                id, name, mode, description, principles_json,
                enabled, is_demo, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                playbook_id,
                data.name,
                data.mode.value,
                data.description,
                _json(data.principles),
                int(data.enabled),
                int(is_demo),
                iso(created_at),
                iso(created_at),
            ),
        )
        return playbook_id

    def create_playbook(self, data: PlaybookCreate) -> dict[str, Any]:
        playbook_id = f"pb_{uuid4().hex[:16]}"
        self.insert_playbook(
            playbook_id=playbook_id,
            data=data,
            is_demo=False,
            created_at=utc_now(),
        )
        self.add_audit(
            "playbook.created",
            resource_type="playbook",
            resource_id=playbook_id,
            summary="Created a local coaching playbook.",
            details={"mode": data.mode.value, "principle_count": len(data.principles)},
        )
        return self.get_playbook(playbook_id) or {}

    def update_playbook(
        self,
        playbook_id: str,
        data: PlaybookUpdate,
    ) -> dict[str, Any] | None:
        current = self.get_playbook(playbook_id)
        if not current:
            return None
        updated = {
            "name": data.name if data.name is not None else current["name"],
            "description": (
                data.description if data.description is not None else current["description"]
            ),
            "principles": (
                data.principles if data.principles is not None else current["principles"]
            ),
            "enabled": data.enabled if data.enabled is not None else current["enabled"],
        }
        self.db.execute(
            """
            UPDATE playbooks
            SET name = ?, description = ?, principles_json = ?,
                enabled = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                updated["name"],
                updated["description"],
                _json(updated["principles"]),
                int(updated["enabled"]),
                iso(),
                playbook_id,
            ),
        )
        self.add_audit(
            "playbook.updated",
            resource_type="playbook",
            resource_id=playbook_id,
            summary="Updated a coaching playbook.",
            details={"changed_fields": list(data.model_fields_set)},
        )
        return self.get_playbook(playbook_id)

    def delete_playbook(self, playbook_id: str) -> bool:
        cursor = self.db.execute("DELETE FROM playbooks WHERE id = ?", (playbook_id,))
        if not cursor.rowcount:
            return False
        self.add_audit(
            "playbook.deleted",
            resource_type="playbook",
            resource_id=playbook_id,
            summary="Deleted a coaching playbook.",
            details={},
        )
        return True

    # Privacy

    def get_privacy_settings(self) -> dict[str, Any]:
        row = self.db.query_one("SELECT * FROM privacy_settings WHERE id = 1")
        assert row is not None
        return {
            "allow_raw_content_storage": bool(row["allow_raw_content_storage"]),
            "default_analysis_retention_days": row["default_analysis_retention_days"],
            "audit_retention_days": row["audit_retention_days"],
            "updated_at": row["updated_at"],
            "defaults": {
                "ad_hoc_analysis_persisted": False,
                "raw_content_stored": False,
                "audit_contains_transcript_text": False,
            },
        }

    def update_privacy_settings(
        self,
        data: PrivacySettingsUpdate,
    ) -> dict[str, Any]:
        self.db.execute(
            """
            UPDATE privacy_settings
            SET allow_raw_content_storage = ?,
                default_analysis_retention_days = ?,
                audit_retention_days = ?,
                updated_at = ?
            WHERE id = 1
            """,
            (
                int(data.allow_raw_content_storage),
                data.default_analysis_retention_days,
                data.audit_retention_days,
                iso(),
            ),
        )
        self.add_audit(
            "privacy.settings_updated",
            resource_type="privacy_settings",
            resource_id="1",
            summary="Updated local retention and raw-content controls.",
            details=data.model_dump(mode="json"),
        )
        return self.get_privacy_settings()

    def purge_conversation(self, conversation_id: str) -> dict[str, int]:
        counts = {
            "turns": int(
                self.db.query_one(
                    "SELECT COUNT(*) AS count FROM turns WHERE conversation_id = ?",
                    (conversation_id,),
                )["count"]
            ),
            "analyses": int(
                self.db.query_one(
                    "SELECT COUNT(*) AS count FROM analyses WHERE conversation_id = ?",
                    (conversation_id,),
                )["count"]
            ),
            "feedback": int(
                self.db.query_one(
                    "SELECT COUNT(*) AS count FROM feedback WHERE conversation_id = ?",
                    (conversation_id,),
                )["count"]
            ),
        }
        cursor = self.db.execute(
            "DELETE FROM conversations WHERE id = ?",
            (conversation_id,),
        )
        counts["conversations"] = cursor.rowcount
        self.add_audit(
            "privacy.conversation_purged",
            resource_type="conversation",
            resource_id=conversation_id,
            summary="Purged conversation content and derived records.",
            details={**counts, "transcript_text_in_audit": False},
        )
        return counts

    def purge_all_non_demo(self) -> dict[str, int]:
        row = self.db.query_one("SELECT COUNT(*) AS count FROM conversations WHERE is_demo = 0")
        conversation_count = int(row["count"]) if row else 0
        standalone = self.db.query_one(
            "SELECT COUNT(*) AS count FROM analyses WHERE is_demo = 0 AND conversation_id IS NULL"
        )
        standalone_count = int(standalone["count"]) if standalone else 0
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM conversations WHERE is_demo = 0")
            conn.execute("DELETE FROM analyses WHERE is_demo = 0 AND conversation_id IS NULL")
            conn.execute("DELETE FROM playbooks WHERE is_demo = 0")
        self.add_audit(
            "privacy.non_demo_purged",
            resource_type="dataset",
            resource_id="local",
            summary="Purged all non-demo content and derived analyses.",
            details={
                "conversations": conversation_count,
                "standalone_analyses": standalone_count,
                "transcript_text_in_audit": False,
            },
        )
        return {
            "conversations": conversation_count,
            "standalone_analyses": standalone_count,
        }

    def purge_expired(self, now: datetime | None = None) -> dict[str, int]:
        current = iso(now)
        settings = self.get_privacy_settings()
        from datetime import timedelta

        audit_cutoff = iso(
            (now or utc_now()) - timedelta(days=int(settings["audit_retention_days"]))
        )
        with self.db.transaction() as conn:
            expired_analyses = conn.execute(
                """
                DELETE FROM analyses
                WHERE is_demo = 0 AND expires_at IS NOT NULL AND expires_at <= ?
                """,
                (current,),
            ).rowcount
            expired_conversations = conn.execute(
                """
                DELETE FROM conversations
                WHERE is_demo = 0 AND expires_at IS NOT NULL AND expires_at <= ?
                """,
                (current,),
            ).rowcount
            expired_audit = conn.execute(
                "DELETE FROM audit WHERE created_at < ?",
                (audit_cutoff,),
            ).rowcount
        self.add_audit(
            "privacy.retention_run",
            resource_type="dataset",
            resource_id="local",
            summary="Applied configured retention limits.",
            details={
                "analyses": expired_analyses,
                "conversations": expired_conversations,
                "audit": expired_audit,
            },
        )
        return {
            "analyses": expired_analyses,
            "conversations": expired_conversations,
            "audit": expired_audit,
        }

    # Metrics

    def metrics(self, mode: ConversationMode | None = None) -> dict[str, Any]:
        mode_clause = " WHERE mode = ?" if mode else ""
        params: tuple[Any, ...] = (mode.value,) if mode else ()
        conversations = int(
            self.db.query_one(
                f"SELECT COUNT(*) AS count FROM conversations{mode_clause}",
                params,
            )["count"]
        )
        analyses_rows = self.db.query_all(
            f"SELECT result_json, mode, conversation_id FROM analyses{mode_clause}",
            params,
        )
        suggestions = int(
            self.db.query_one(
                f"SELECT COUNT(*) AS count FROM suggestions{mode_clause}",
                params,
            )["count"]
        )
        feedback_where = ""
        feedback_params: tuple[Any, ...] = ()
        if mode:
            feedback_where = (
                " WHERE suggestion_id IN (SELECT id FROM suggestions WHERE mode = ?)"
                " OR conversation_id IN (SELECT id FROM conversations WHERE mode = ?)"
            )
            feedback_params = (mode.value, mode.value)
        feedback_rows = self.db.query_all(
            f"SELECT kind, outcome FROM feedback{feedback_where}",
            feedback_params,
        )
        accepted = sum(row["kind"] == "accepted" for row in feedback_rows)
        rejected = sum(row["kind"] == "rejected" for row in feedback_rows)
        outcomes = [row["outcome"] for row in feedback_rows if row["kind"] == "outcome"]
        positive_outcomes = sum(outcome in {"advanced", "resolved"} for outcome in outcomes)
        acceptance_denominator = accepted + rejected

        latest_by_conversation: dict[str, dict[str, Any]] = {}
        signal_values: dict[str, list[int]] = {
            "momentum": [],
            "tone": [],
            "clarity": [],
            "empathy": [],
        }
        for row in analyses_rows:
            result = json.loads(row["result_json"])
            for name in signal_values:
                signal_values[name].append(int(result["signals"][name]["score"]))
            if row["conversation_id"]:
                latest_by_conversation[row["conversation_id"]] = result
        at_risk = sum(result["status"] == "at_risk" for result in latest_by_conversation.values())

        mode_rows = self.db.query_all(
            """
            SELECT mode, COUNT(*) AS count
            FROM conversations GROUP BY mode ORDER BY mode
            """
        )
        return {
            "scope": mode.value if mode else "all",
            "conversations_total": conversations,
            "active_conversations": conversations,
            "analyses_total": len(analyses_rows),
            "suggestions_generated": suggestions,
            "suggestions_accepted": accepted,
            "suggestions_rejected": rejected,
            "acceptance_rate": round(accepted / acceptance_denominator * 100, 1)
            if acceptance_denominator
            else 0.0,
            "outcomes_recorded": len(outcomes),
            "positive_outcomes": positive_outcomes,
            "at_risk_conversations": at_risk,
            "average_signals": {
                name: round(sum(values) / len(values), 1) if values else 0.0
                for name, values in signal_values.items()
            },
            "mode_breakdown": {row["mode"]: row["count"] for row in mode_rows},
            "limitations": [
                "Demo metrics describe fictional seeded and local operator activity.",
                "Acceptance is not proof that a suggestion caused an outcome.",
                "Small samples are directional and should not be used for employee ranking.",
            ],
        }
