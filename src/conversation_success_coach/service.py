"""Application service coordinating analysis, state, and responsible use."""

from __future__ import annotations

from conversation_success_coach.analysis import ConversationAnalyzer
from conversation_success_coach.repository import Repository
from conversation_success_coach.schemas import (
    AnalysisResponse,
    AnalyzeRequest,
    FeedbackCreate,
    SuggestionRequest,
    SuggestionResponse,
)


class PolicyConflictError(ValueError):
    pass


class NotFoundError(LookupError):
    pass


class CoachService:
    def __init__(
        self,
        repository: Repository,
        analyzer: ConversationAnalyzer | None = None,
    ) -> None:
        self.repository = repository
        self.analyzer = analyzer or ConversationAnalyzer()

    def analyze(self, request: AnalyzeRequest) -> AnalysisResponse:
        if request.conversation_id and not self.repository.get_conversation(
            request.conversation_id
        ):
            raise NotFoundError("conversation not found")

        settings = self.repository.get_privacy_settings()
        if request.data_handling.store_raw_content and not settings["allow_raw_content_storage"]:
            raise PolicyConflictError("raw content storage is disabled by privacy settings")

        playbook_refs = [
            item["id"]
            for item in self.repository.list_playbooks(
                request.mode,
                enabled_only=True,
            )
        ]
        result = self.analyzer.analyze(
            request,
            playbook_refs=playbook_refs,
        )
        if request.data_handling.persist_analysis:
            if request.data_handling.store_raw_content:
                if not request.conversation_id:
                    raise PolicyConflictError(
                        "raw content storage requires an existing conversation_id"
                    )
                self.repository.replace_turns(request.conversation_id, request.turns)
            self.repository.save_analysis(
                result,
                raw_content_stored=request.data_handling.store_raw_content,
            )
        return result

    def suggestions(self, request: SuggestionRequest) -> SuggestionResponse:
        result = self.analyze(
            AnalyzeRequest(
                mode=request.mode,
                turns=request.turns,
                conversation_id=request.conversation_id,
                context=request.context,
                data_handling=request.data_handling,
            )
        )
        return SuggestionResponse(
            analysis_id=result.analysis_id,
            conversation_id=result.conversation_id,
            mode=result.mode,
            suggestions=result.suggestions[: request.max_suggestions],
            responsible_use=result.responsible_use,
            limitations=result.limitations,
        )

    def record_feedback(self, feedback: FeedbackCreate) -> dict:
        if feedback.suggestion_id and not self.repository.get_suggestion(feedback.suggestion_id):
            raise NotFoundError("suggestion not found")
        if feedback.conversation_id and not self.repository.get_conversation(
            feedback.conversation_id
        ):
            raise NotFoundError("conversation not found")
        return self.repository.insert_feedback(feedback)
