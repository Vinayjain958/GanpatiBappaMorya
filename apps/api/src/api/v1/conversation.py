"""Conversational discovery endpoints (Phase 5).

Text turns go through handle_text_turn (understand -> retrieve, one
Gemini call per turn). The tool-calls route is the voice-path bridge:
Gemini Live runs entirely browser<->Google, and the browser forwards each
tool_call here for real, backend-owned execution — the browser itself
never implements search_experiences (docs/AI_CONTEXT.md INV-3,
docs/DECISIONS.md ADR-034).

Ownership: every route requires CurrentUser and 404s (never discloses
existence via 403) for another user's conversation, matching the
non-disclosure pattern already used for provider-owned experiences.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.ai import AIAdapter
from src.adapters.embedding import EmbeddingAdapter
from src.adapters.errors import AdapterError, AdapterNoResultError, AdapterRateLimitedError, AdapterUnavailableError
from src.adapters.routing import RoutingAdapter
from src.core.ai import get_ai_adapter
from src.core.config import Settings, get_settings
from src.core.db import get_session
from src.core.deps import CurrentUser
from src.core.embedding import get_embedding_adapter
from src.core.errors import ApiError
from src.core.location import get_routing_adapter
from src.models.conversation_message import ConversationMessage
from src.models.conversation_session import ConversationSession
from src.repositories.conversation_repository import ConversationRepository
from src.schemas.conversation import (
    CheckFeasibilityArgs,
    ConversationCreateResponse,
    ConversationDetailResponse,
    ConversationMessagePublic,
    ConversationTurnRequest,
    ConversationTurnResponse,
    SearchExperiencesArgs,
    SearchExperiencesResult,
    ToolCallRequest,
    TravelerContext,
)
from src.schemas.feasibility import FeasibilityVerdict
from src.services import ai_tools
from src.services.conversation import create_conversation, handle_text_turn

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _translate_ai_error(exc: Exception) -> ApiError:
    if isinstance(exc, AdapterRateLimitedError):
        return ApiError("The AI service is temporarily rate-limited. Please try again shortly.", 503)
    if isinstance(exc, AdapterNoResultError):
        return ApiError("The AI service returned no usable result.", 503)
    if isinstance(exc, AdapterUnavailableError):
        return ApiError("The AI service is temporarily unavailable.", 503)
    if isinstance(exc, ValueError):
        return ApiError(str(exc), 422)
    return ApiError("Unexpected AI service error.", 503)


async def _get_owned_or_404(session: AsyncSession, conversation_id: str, user_id: str) -> ConversationSession:
    conversation = await ConversationRepository(session).get_owned_by_id(conversation_id, user_id)
    if conversation is None:
        # Deliberately identical to "does not exist" — never disclose that
        # a conversation exists but belongs to another user.
        raise ApiError("Conversation not found", status_code=404)
    return conversation


@router.post("", response_model=ConversationCreateResponse, status_code=201)
async def create_conversation_session(
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ConversationCreateResponse:
    conversation = await create_conversation(session, user.id, mode="text")
    return ConversationCreateResponse(id=conversation.id, created_at=conversation.created_at)


@router.post("/{conversation_id}/messages", response_model=ConversationTurnResponse)
async def send_message(
    conversation_id: str,
    payload: ConversationTurnRequest,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    ai: Annotated[AIAdapter, Depends(get_ai_adapter)],
    embedding_adapter: Annotated[EmbeddingAdapter, Depends(get_embedding_adapter)],
    routing: Annotated[RoutingAdapter, Depends(get_routing_adapter)],
) -> ConversationTurnResponse:
    conversation = await _get_owned_or_404(session, conversation_id, user.id)
    try:
        return await handle_text_turn(
            session, ai, settings, conversation, payload.message, embedding_adapter, routing
        )
    except AdapterError as exc:
        raise _translate_ai_error(exc) from exc
    except ValueError as exc:
        raise _translate_ai_error(exc) from exc


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ConversationDetailResponse:
    conversation = await _get_owned_or_404(session, conversation_id, user.id)
    messages = [ConversationMessagePublic.model_validate(m) for m in conversation.messages]
    latest_context = (
        TravelerContext.model_validate(conversation.latest_traveler_context)
        if conversation.latest_traveler_context is not None
        else None
    )
    return ConversationDetailResponse(
        id=conversation.id,
        created_at=conversation.created_at,
        messages=messages,
        latest_traveler_context=latest_context,
    )


_KNOWN_TOOLS = {"search_experiences", "check_feasibility"}


@router.post("/{conversation_id}/tool-calls", response_model=SearchExperiencesResult | FeasibilityVerdict)
async def execute_tool_call(
    conversation_id: str,
    payload: ToolCallRequest,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    routing: Annotated[RoutingAdapter, Depends(get_routing_adapter)],
) -> SearchExperiencesResult | FeasibilityVerdict:
    """Voice-path bridge: the browser forwards Gemini Live's tool_call
    here verbatim and forwards this response back to Gemini via
    session.send_tool_response(...). This endpoint — not the browser —
    is the only place search_experiences/check_feasibility actually
    execute; both tools are backend-owned per the allowlist above."""
    conversation = await _get_owned_or_404(session, conversation_id, user.id)

    if payload.name not in _KNOWN_TOOLS:
        raise ApiError(f"Unknown tool: {payload.name}", status_code=422)

    if payload.name == "search_experiences":
        try:
            args = SearchExperiencesArgs.model_validate(payload.args)
        except Exception as exc:  # noqa: BLE001 — never trust raw model tool arguments
            raise ApiError(f"Invalid tool arguments: {exc}", status_code=422) from exc

        # We also need traveler_id. In conversation.py, user may have traveler.
        # However, to be safe, we'll try to find the traveler_id for the user.
        from sqlalchemy import select
        from src.models.traveler import Traveler
        traveler_id = await session.scalar(select(Traveler.id).where(Traveler.user_id == user.id))
        
        # We need embedding_adapter.
        from src.core.embedding import get_embedding_adapter
        embedding_adapter = get_embedding_adapter(settings)
        
        result = await ai_tools.execute_search_experiences(
            session=session, 
            settings=settings, 
            args=args,
            traveler_id=traveler_id,
            context=conversation.latest_traveler_context,
            routing_adapter=routing,
            embedding_adapter=embedding_adapter,
        )

        session.add(
            ConversationMessage(
                session_id=conversation.id,
                role="assistant",
                text=f"[voice tool call] search_experiences -> {len(result.items)} result(s)",
                tool_call_metadata={
                    "tool": "search_experiences",
                    "args": args.model_dump(exclude_none=True),
                    "result_count": len(result.items),
                },
            )
        )
        await session.commit()
        return result

    # check_feasibility
    try:
        feasibility_args = CheckFeasibilityArgs.model_validate(payload.args)
    except Exception as exc:  # noqa: BLE001 — never trust raw model tool arguments
        raise ApiError(f"Invalid tool arguments: {exc}", status_code=422) from exc

    verdict = await ai_tools.execute_check_feasibility(session, routing, settings, feasibility_args)

    session.add(
        ConversationMessage(
            session_id=conversation.id,
            role="assistant",
            text=f"[voice tool call] check_feasibility -> {verdict.status}",
            tool_call_metadata={
                "tool": "check_feasibility",
                "args": feasibility_args.model_dump(exclude_none=True),
                "status": verdict.status,
            },
        )
    )
    await session.commit()
    return verdict
