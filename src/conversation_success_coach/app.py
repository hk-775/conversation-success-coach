"""FastAPI application factory and local product surface."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from conversation_success_coach.analysis import ConversationAnalyzer
from conversation_success_coach.config import Settings
from conversation_success_coach.database import Database
from conversation_success_coach.repository import Repository
from conversation_success_coach.schemas import (
    AnalysisResponse,
    AnalyzeRequest,
    ConversationCreate,
    ConversationMode,
    FeedbackCreate,
    PlaybookCreate,
    PlaybookUpdate,
    PrivacySettingsUpdate,
    PurgeRequest,
    SuggestionRequest,
    SuggestionResponse,
    TurnCreate,
)
from conversation_success_coach.seed import SEED_VERSION, seed_demo
from conversation_success_coach.service import (
    CoachService,
    NotFoundError,
    PolicyConflictError,
)
from conversation_success_coach.version import __version__


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime = settings or Settings.from_env()
    database = Database(runtime.database_path)
    repository = Repository(database)
    analyzer = ConversationAnalyzer()
    service = CoachService(repository, analyzer)

    if runtime.demo_seed:
        seed_demo(repository, analyzer)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        try:
            yield
        finally:
            database.close()

    app = FastAPI(
        title="Conversation Success Coach API",
        version=__version__,
        summary="Explainable, human-controlled coaching for consequential conversations",
        description=(
            "A local deterministic service for sales, support, recruiting, and "
            "community moderation. It produces editable suggestions only and has "
            "no message-delivery capability."
        ),
        docs_url="/docs" if runtime.docs_enabled else None,
        redoc_url="/redoc" if runtime.docs_enabled else None,
        openapi_url="/openapi.json" if runtime.docs_enabled else None,
        lifespan=lifespan,
    )
    app.state.settings = runtime
    app.state.database = database
    app.state.repository = repository
    app.state.service = service

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "font-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "frame-ancestors 'none'"
        )
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        issues = []
        for error in exc.errors():
            issues.append(
                {
                    "field": ".".join(str(part) for part in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"],
                }
            )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "The request did not match the API contract.",
                    "issues": issues,
                }
            },
        )

    def require_conversation(conversation_id: str) -> dict:
        conversation = repository.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "conversation_not_found",
                    "message": "Conversation not found.",
                },
            )
        return conversation

    @app.get("/api/v1/health", tags=["system"])
    def health() -> dict:
        return {
            "status": "ok",
            "service": "conversation-success-coach",
            "version": __version__,
            "engine": "local-deterministic",
            "external_network_calls": False,
            "message_delivery_capability": False,
            "demo_seed": runtime.demo_seed,
            "seed_version": repository.get_metadata("seed_version"),
        }

    @app.get("/api/v1/responsible-use", tags=["system"])
    def responsible_use() -> dict:
        return {
            "human_agency": {
                "suggestions_only": True,
                "requires_review": True,
                "auto_send": False,
                "impersonation": False,
            },
            "prohibited": [
                "covert manipulation",
                "protected-attribute inference or targeting",
                "mental-health diagnosis",
                "deceptive urgency or fabricated scarcity",
                "optimization for dependency",
                "automatic sending or impersonation",
            ],
            "data_defaults": repository.get_privacy_settings()["defaults"],
        }

    @app.get("/api/v1/conversations", tags=["conversations"])
    def list_conversations(
        mode: ConversationMode | None = None,
    ) -> dict:
        return {"items": repository.list_conversations(mode)}

    @app.post(
        "/api/v1/conversations",
        tags=["conversations"],
        status_code=201,
    )
    def create_conversation(data: ConversationCreate) -> dict:
        settings_data = repository.get_privacy_settings()
        if not settings_data["allow_raw_content_storage"]:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "raw_storage_disabled",
                    "message": (
                        "Enable raw content storage in privacy settings before "
                        "creating a retained conversation workspace."
                    ),
                },
            )
        return repository.create_conversation(data)

    @app.get("/api/v1/conversations/{conversation_id}", tags=["conversations"])
    def get_conversation(conversation_id: str) -> dict:
        return require_conversation(conversation_id)

    @app.post(
        "/api/v1/conversations/{conversation_id}/turns",
        tags=["conversations"],
        status_code=201,
    )
    def add_turn(conversation_id: str, turn: TurnCreate) -> dict:
        require_conversation(conversation_id)
        conversation = repository.get_conversation(conversation_id)
        if conversation and not conversation["is_demo"]:
            settings_data = repository.get_privacy_settings()
            if not settings_data["allow_raw_content_storage"]:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "code": "raw_storage_disabled",
                        "message": "Raw content storage is disabled.",
                    },
                )
        return repository.add_turn(conversation_id, turn)

    @app.post(
        "/api/v1/analyze",
        tags=["coaching"],
        response_model=AnalysisResponse,
    )
    def analyze(request: AnalyzeRequest) -> AnalysisResponse:
        try:
            return service.analyze(request)
        except NotFoundError as exc:
            raise HTTPException(
                status_code=404,
                detail={"code": "not_found", "message": str(exc)},
            ) from exc
        except PolicyConflictError as exc:
            raise HTTPException(
                status_code=409,
                detail={"code": "privacy_policy_conflict", "message": str(exc)},
            ) from exc

    @app.post(
        "/api/v1/suggestions",
        tags=["coaching"],
        response_model=SuggestionResponse,
    )
    def suggestions(request: SuggestionRequest) -> SuggestionResponse:
        try:
            return service.suggestions(request)
        except NotFoundError as exc:
            raise HTTPException(
                status_code=404,
                detail={"code": "not_found", "message": str(exc)},
            ) from exc
        except PolicyConflictError as exc:
            raise HTTPException(
                status_code=409,
                detail={"code": "privacy_policy_conflict", "message": str(exc)},
            ) from exc

    @app.post("/api/v1/feedback", tags=["feedback"], status_code=201)
    def feedback(data: FeedbackCreate) -> dict:
        try:
            return service.record_feedback(data)
        except NotFoundError as exc:
            raise HTTPException(
                status_code=404,
                detail={"code": "not_found", "message": str(exc)},
            ) from exc

    @app.get("/api/v1/feedback", tags=["feedback"])
    def list_feedback(
        limit: Annotated[int, Query(ge=1, le=500)] = 100,
    ) -> dict:
        return {"items": repository.list_feedback(limit)}

    @app.get("/api/v1/playbooks", tags=["playbooks"])
    def list_playbooks(
        mode: ConversationMode | None = None,
        enabled_only: bool = False,
    ) -> dict:
        return {
            "items": repository.list_playbooks(
                mode,
                enabled_only=enabled_only,
            )
        }

    @app.post("/api/v1/playbooks", tags=["playbooks"], status_code=201)
    def create_playbook(data: PlaybookCreate) -> dict:
        return repository.create_playbook(data)

    @app.patch("/api/v1/playbooks/{playbook_id}", tags=["playbooks"])
    def update_playbook(playbook_id: str, data: PlaybookUpdate) -> dict:
        result = repository.update_playbook(playbook_id, data)
        if not result:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "playbook_not_found",
                    "message": "Playbook not found.",
                },
            )
        return result

    @app.delete(
        "/api/v1/playbooks/{playbook_id}",
        tags=["playbooks"],
        status_code=204,
    )
    def delete_playbook(playbook_id: str) -> None:
        if not repository.delete_playbook(playbook_id):
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "playbook_not_found",
                    "message": "Playbook not found.",
                },
            )

    @app.get("/api/v1/metrics", tags=["observability"])
    def metrics(mode: ConversationMode | None = None) -> dict:
        return repository.metrics(mode)

    @app.get("/api/v1/audit", tags=["observability"])
    def audit(
        event_type: Annotated[str | None, Query(max_length=80)] = None,
        limit: Annotated[int, Query(ge=1, le=500)] = 100,
    ) -> dict:
        return {"items": repository.list_audit(event_type=event_type, limit=limit)}

    @app.get("/api/v1/privacy/settings", tags=["privacy"])
    def privacy_settings() -> dict:
        return repository.get_privacy_settings()

    @app.put("/api/v1/privacy/settings", tags=["privacy"])
    def update_privacy_settings(data: PrivacySettingsUpdate) -> dict:
        return repository.update_privacy_settings(data)

    @app.post("/api/v1/privacy/purge", tags=["privacy"])
    def purge(data: PurgeRequest) -> dict:
        if data.scope == "conversation":
            require_conversation(data.conversation_id or "")
            deleted = repository.purge_conversation(data.conversation_id or "")
        elif data.scope == "all_non_demo":
            deleted = repository.purge_all_non_demo()
        else:
            deleted = repository.purge_expired()
        return {
            "status": "completed",
            "scope": data.scope,
            "deleted": deleted,
            "audit_retained": True,
            "audit_contains_transcript_text": False,
        }

    @app.post("/api/v1/privacy/retention/run", tags=["privacy"])
    def run_retention() -> dict:
        return {
            "status": "completed",
            "deleted": repository.purge_expired(),
        }

    @app.post("/api/v1/demo/reset", tags=["demo"])
    def reset_demo() -> dict:
        seed_demo(repository, analyzer, reset=True)
        return {
            "status": "reset",
            "seed_version": SEED_VERSION,
            "conversations": len(repository.list_conversations()),
            "playbooks": len(repository.list_playbooks()),
            "fictional_data": True,
        }

    static_dir = Path(runtime.static_dir)
    assets_dir = static_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    def page(name: str) -> FileResponse:
        path = static_dir / name
        if not path.exists():
            raise HTTPException(status_code=404, detail="Page not found")
        return FileResponse(path)

    @app.get("/", include_in_schema=False)
    @app.get("/index.html", include_in_schema=False)
    def landing() -> FileResponse:
        return page("index.html")

    @app.get("/dashboard", include_in_schema=False)
    @app.get("/dashboard.html", include_in_schema=False)
    def dashboard() -> FileResponse:
        return page("dashboard.html")

    @app.get("/architecture", include_in_schema=False)
    @app.get("/architecture.html", include_in_schema=False)
    def architecture() -> FileResponse:
        return page("architecture.html")

    return app
