from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
import asyncio
import os
import logging

from backend.api.schemas import (
    PlaygroundChatRequest,
    PlaygroundChatResponse,
    PlaygroundRateLimitResponse
)
from backend.api.auth import get_current_user
from backend.database.database import get_db
from backend.database.dao.mcp_server_dao import MCPServerDAO
from backend.service.playground_service import PlaygroundService
from backend.database.model.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

# Semaphore to limit concurrent LLM requests to prevent server overload
# Only allow 5 concurrent playground requests at a time
_playground_semaphore = asyncio.Semaphore(5)


@router.get("/mcp-servers/{server_id}/playground/rate-limit")
async def get_rate_limit(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> PlaygroundRateLimitResponse:
    """
    Get rate limit status for current user and MCP server
    """
    user_id = current_user.id

    rate_limit = PlaygroundService.check_rate_limit(db, user_id, server_id)

    return PlaygroundRateLimitResponse(
        allowed=rate_limit["allowed"],
        remaining=rate_limit["remaining"],
        used=rate_limit["used"]
    )


@router.post("/mcp-servers/{server_id}/playground/chat")
async def playground_chat(
    server_id: int,
    chat_request: PlaygroundChatRequest,
    request: Request,  # Add Request object for disconnect detection
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> PlaygroundChatResponse:
    """
    Send a chat message to the playground with MCP integration
    Includes timeout handling and client disconnect detection
    """
    user_id = current_user.id

    try:
        # Check if client is already disconnected before processing
        if await request.is_disconnected():
            logger.warning(f"[Playground] Client disconnected before processing (user_id={user_id}, server_id={server_id})")
            raise HTTPException(status_code=499, detail="Client closed request")

        # Check rate limit
        rate_limit = PlaygroundService.check_rate_limit(db, user_id, server_id)
        if not rate_limit["allowed"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. You have used {rate_limit['used']} out of {PlaygroundService.DAILY_QUERY_LIMIT} queries today."
            )

        # Get MCP server
        mcp_server_dao = MCPServerDAO(db)
        mcp_server = mcp_server_dao.get_mcp_server_by_id(server_id)
        if not mcp_server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MCP server not found"
            )

        # Get server URL from server_url field or config
        server_url = mcp_server.server_url
        logger.info(f"[Playground] MCP Server ID: {server_id}, Name: {mcp_server.name}")
        logger.info(f"[Playground] server_url: {server_url}, protocol: {mcp_server.protocol}")
        logger.info(f"[Playground] config: {mcp_server.config}")

        if not server_url and mcp_server.config:
            # Try to get from config if server_url is empty
            config = mcp_server.config
            if isinstance(config, dict):
                # Check various possible config structures
                if "command" in config:
                    server_url = config["command"]
                    if "args" in config and isinstance(config["args"], list):
                        server_url += " " + " ".join(config["args"])
                elif "url" in config:
                    server_url = config["url"]

        if not server_url:
            logger.error(f"[Playground] No server_url found for MCP server {server_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MCP server URL not found in server_url or config"
            )

        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OpenAI API key not configured on server"
            )

        # Create playground service
        playground_service = PlaygroundService(api_key=api_key, model=model)

        # Convert conversation history to dict format
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in chat_request.conversation_history
        ]

        # Use semaphore to limit concurrent LLM requests
        async with _playground_semaphore:
            logger.info(f"[Playground] Acquired semaphore. Starting chat for user_id={user_id}, server_id={server_id}")

            # Send chat message with timeout (3 minutes max for entire operation)
            try:
                result = await asyncio.wait_for(
                    playground_service.chat(
                        message=chat_request.message,
                        mcp_server_url=server_url,
                        protocol=mcp_server.protocol,
                        conversation_history=conversation_history
                    ),
                    timeout=180  # 3 minutes max for entire playground request
                )
                logger.info(f"[Playground] Chat completed for user_id={user_id}, server_id={server_id}")
            except asyncio.TimeoutError:
                logger.error(f"[Playground] Request timed out after 180s (user_id={user_id}, server_id={server_id})")
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="Playground request timed out after 180 seconds"
                )

        # Check if client disconnected during processing
        if await request.is_disconnected():
            logger.warning(f"[Playground] Client disconnected during processing (user_id={user_id}, server_id={server_id})")
            # Don't increment usage if client disconnected
            raise HTTPException(status_code=499, detail="Client closed request")

        # Increment usage if successful
        if result.get("success"):
            PlaygroundService.increment_usage(db, user_id, server_id)

        # Convert result to response schema
        if result.get("success"):
            return PlaygroundChatResponse(
                success=True,
                response=result.get("response"),
                tool_calls=result.get("tool_calls", []),
                tokens_used=result.get("tokens_used")
            )
        else:
            return PlaygroundChatResponse(
                success=False,
                error=result.get("error", "Unknown error occurred")
            )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except asyncio.CancelledError:
        logger.warning(f"[Playground] Request cancelled (user_id={user_id}, server_id={server_id})")
        raise HTTPException(status_code=499, detail="Request cancelled")
    except Exception as e:
        logger.error(f"[Playground] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
