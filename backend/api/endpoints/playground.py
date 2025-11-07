from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import os

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

router = APIRouter()


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
    request: PlaygroundChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> PlaygroundChatResponse:
    """
    Send a chat message to the playground with MCP integration
    """
    user_id = current_user.id

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

    # Check if server has config
    if not mcp_server.config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MCP server does not have a valid configuration"
        )

    # Get server URL from config
    server_url = mcp_server.server_url
    if not server_url:
        # Try to get from config
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MCP server URL not found in configuration"
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
        for msg in request.conversation_history
    ]

    # Send chat message
    result = await playground_service.chat(
        message=request.message,
        mcp_server_url=server_url,
        protocol=mcp_server.protocol,
        conversation_history=conversation_history
    )

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
