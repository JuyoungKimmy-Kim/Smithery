"""
Playground Service for integrating MCP servers with LLM
"""

import logging
import json
import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import pytz
from sqlalchemy.orm import Session
from openai import OpenAI

from backend.database.model.playground_usage import PlaygroundUsage
from backend.service.mcp_proxy_service import MCPProxyService

logger = logging.getLogger(__name__)

# KST timezone
KST = pytz.timezone('Asia/Seoul')


class PlaygroundService:
    """
    Service for running playground chat sessions with MCP server integration
    """

    # Rate limiting constants
    DAILY_QUERY_LIMIT = 5

    def __init__(self, api_key: str = None, model: str = "gpt-4-turbo-preview", base_url: str = None):
        """
        Initialize PlaygroundService

        Args:
            api_key: OpenAI API key (defaults to env var OPENAI_API_KEY)
            model: Model to use (defaults to gpt-4-turbo-preview)
            base_url: API base URL (defaults to env var LLM_BASE_URL or OpenAI default)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.base_url = base_url or os.getenv("LLM_BASE_URL")

        if self.api_key:
            # Use default OpenAI client without custom http_client to avoid connection leaks
            # OpenAI SDK handles connection pooling internally
            if self.base_url:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    max_retries=2,  # Limit retries to prevent hanging
                    timeout=180.0   # Overall timeout (3 minutes)
                )
            else:
                self.client = OpenAI(
                    api_key=self.api_key,
                    max_retries=2,
                    timeout=180.0
                )
        else:
            self.client = None

    @staticmethod
    def check_rate_limit(db: Session, user_id: int, mcp_server_id: int) -> Dict[str, Any]:
        """
        Check if user has exceeded rate limit for today (KST timezone)

        Returns:
            Dict with 'allowed' bool and 'remaining' int
        """
        # Get current date in KST
        today_kst = datetime.now(KST).date()

        usage = db.query(PlaygroundUsage).filter(
            PlaygroundUsage.user_id == user_id,
            PlaygroundUsage.mcp_server_id == mcp_server_id,
            PlaygroundUsage.date == today_kst
        ).first()

        if not usage:
            return {"allowed": True, "remaining": PlaygroundService.DAILY_QUERY_LIMIT, "used": 0}

        remaining = PlaygroundService.DAILY_QUERY_LIMIT - usage.query_count
        allowed = remaining > 0

        return {
            "allowed": allowed,
            "remaining": max(0, remaining),
            "used": usage.query_count
        }

    @staticmethod
    def increment_usage(db: Session, user_id: int, mcp_server_id: int):
        """
        Increment usage count for user and MCP server for today (KST timezone)
        """
        # Get current date in KST
        today_kst = datetime.now(KST).date()

        usage = db.query(PlaygroundUsage).filter(
            PlaygroundUsage.user_id == user_id,
            PlaygroundUsage.mcp_server_id == mcp_server_id,
            PlaygroundUsage.date == today_kst
        ).first()

        if usage:
            usage.query_count += 1
        else:
            usage = PlaygroundUsage(
                user_id=user_id,
                mcp_server_id=mcp_server_id,
                query_count=1,
                date=today_kst
            )
            db.add(usage)

        db.commit()

    async def get_mcp_tools(self, mcp_server_url: str, protocol: str) -> List[Dict[str, Any]]:
        """
        Fetch tools from MCP server

        Args:
            mcp_server_url: MCP server URL or command
            protocol: Protocol type (stdio, sse, http, etc.)

        Returns:
            List of tools in OpenAI function format
        """
        try:
            result = await MCPProxyService.fetch_tools(mcp_server_url, protocol)

            if not result.get("success"):
                logger.error(f"Failed to fetch MCP tools: {result.get('message')}")
                return []

            # Convert MCP tools to OpenAI function format
            tools = result.get("tools", [])
            openai_tools = []

            for tool in tools:
                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": tool.get("name"),
                        "description": tool.get("description", ""),
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                }

                # Convert input schema if available
                input_schema = tool.get("inputSchema", {})
                if input_schema:
                    openai_tool["function"]["parameters"] = input_schema

                openai_tools.append(openai_tool)

            return openai_tools

        except Exception as e:
            logger.error(f"Error fetching MCP tools: {str(e)}", exc_info=True)
            return []

    async def call_mcp_tool(
        self,
        mcp_server_url: str,
        protocol: str,
        tool_name: str,
        arguments: Dict[str, Any],
        user_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call a specific tool on the MCP server

        Args:
            mcp_server_url: MCP server URL or command
            protocol: Protocol type
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Tool execution result
        """
        try:
            # Use MCPProxyService to call the tool
            result = await MCPProxyService.call_tool(
                mcp_server_url,
                protocol,
                tool_name,
                arguments
            )

            return result

        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    async def chat(
        self,
        message: str,
        mcp_server_url: str,
        protocol: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Send a chat message and get response with MCP tool integration

        Args:
            message: User message
            mcp_server_url: MCP server URL or command
            protocol: Protocol type
            conversation_history: Previous conversation messages

        Returns:
            Dict with response, tool_calls, and metadata
        """
        if not self.client:
            return {
                "success": False,
                "error": "OpenAI API key not configured"
            }

        try:
            # Wrap entire chat logic in a timeout to prevent hanging
            return await asyncio.wait_for(
                self._chat_internal(message, mcp_server_url, protocol, conversation_history),
                timeout=240.0  # Maximum 4 minutes for entire operation
            )
        except asyncio.TimeoutError:
            logger.error("Chat operation timed out after 240 seconds")
            return {
                "success": False,
                "error": "Request timed out. The operation took too long to complete."
            }
        except Exception as e:
            logger.error(f"Unexpected error in chat: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"An unexpected error occurred: {str(e)}"
            }

    async def _chat_internal(
        self,
        message: str,
        mcp_server_url: str,
        protocol: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Internal chat implementation with error handling
        """
        try:
            # Get MCP tools
            tools = await self.get_mcp_tools(mcp_server_url, protocol)

            # Build messages
            messages = conversation_history or []

            # Add system prompt to encourage tool usage when tools are available
            if tools and (not messages or messages[0].get("role") != "system"):
                system_message = {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant with access to tools. "
                        "When answering questions, ALWAYS check if there are relevant tools available that could provide accurate information. "
                        "If a tool can help answer the user's question, you MUST use it instead of relying on general knowledge. "
                        "For example, if the user asks about documentation, usage, or specific information that a tool like 'search_doc' can provide, "
                        "you should call that tool first and base your answer on the tool's results."
                    )
                }
                messages.insert(0, system_message)

            messages.append({
                "role": "user",
                "content": message
            })

            # Call OpenAI with tools
            response_data = {
                "success": True,
                "response": "",
                "tool_calls": [],
                "tokens_used": 0
            }

            # First API call - run in executor to make it truly async
            try:
                if tools:
                    completion = await asyncio.to_thread(
                        self.client.chat.completions.create,
                        model=self.model,
                        messages=messages,
                        tools=tools,
                        tool_choice="auto"
                    )
                else:
                    completion = await asyncio.to_thread(
                        self.client.chat.completions.create,
                        model=self.model,
                        messages=messages
                    )
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                logger.error(f"OpenAI API call failed - Type: {error_type}, Message: {error_msg}", exc_info=True)
                logger.error(f"Model: {self.model}, Base URL: {self.base_url}, Messages count: {len(messages)}")
                return {
                    "success": False,
                    "error": f"Failed to get response from LLM: [{error_type}] {error_msg}"
                }

            response_message = completion.choices[0].message
            response_data["tokens_used"] = completion.usage.total_tokens

            # Check if tool calls were made
            if response_message.tool_calls:
                # Execute tool calls
                messages.append(response_message)

                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse tool arguments: {str(e)}")
                        function_args = {}

                    logger.info(f"Calling tool: {function_name} with args: {function_args}")

                    # Call MCP tool with timeout
                    try:
                        tool_result = await asyncio.wait_for(
                            self.call_mcp_tool(
                                mcp_server_url,
                                protocol,
                                function_name,
                                function_args
                            ),
                            timeout=60.0  # 60 second timeout per tool call
                        )
                    except asyncio.TimeoutError:
                        logger.error(f"Tool {function_name} timed out after 60 seconds")
                        tool_result = {
                            "success": False,
                            "error": f"Tool execution timed out after 60 seconds"
                        }
                    except Exception as e:
                        logger.error(f"Tool {function_name} failed: {str(e)}", exc_info=True)
                        tool_result = {
                            "success": False,
                            "error": f"Tool execution failed: {str(e)}"
                        }

                    logger.info(f"Tool {function_name} result type: {type(tool_result)}")
                    logger.info(f"Tool {function_name} result: {str(tool_result)[:500]}")

                    # Extract actual content from MCP result
                    tool_content = ""
                    try:
                        if isinstance(tool_result, dict):
                            if tool_result.get("success"):
                                result_data = tool_result.get("result", {})
                                logger.info(f"Result data type: {type(result_data)}")

                                # MCP result.content is usually a list of content items
                                if isinstance(result_data, list):
                                    # Extract text from content items
                                    text_parts = []
                                    for item in result_data:
                                        if isinstance(item, dict):
                                            # Dict format: {"type": "text", "text": "..."}
                                            if "text" in item:
                                                text_parts.append(str(item["text"]))
                                            elif "type" in item and item["type"] == "text":
                                                text_parts.append(str(item.get("text", "")))
                                        elif hasattr(item, 'text'):
                                            # Object format: TextContent(type='text', text='...')
                                            text_parts.append(str(item.text))
                                        elif hasattr(item, '__dict__'):
                                            # Other object with __dict__
                                            if 'text' in item.__dict__:
                                                text_parts.append(str(item.__dict__['text']))
                                            else:
                                                # Try str() on the whole object
                                                text_parts.append(str(item))
                                        else:
                                            # Unknown type, convert to string
                                            text_parts.append(str(item))

                                    if text_parts:
                                        tool_content = "\n".join(text_parts)
                                    else:
                                        # Fallback: convert to string representation
                                        try:
                                            tool_content = json.dumps(result_data, ensure_ascii=False, default=str)
                                        except (TypeError, ValueError) as e:
                                            logger.error(f"JSON serialization failed: {e}")
                                            tool_content = str(result_data)
                                elif isinstance(result_data, dict):
                                    # Try to serialize dict
                                    try:
                                        tool_content = json.dumps(result_data, ensure_ascii=False, default=str)
                                    except (TypeError, ValueError) as e:
                                        logger.error(f"JSON serialization failed: {e}")
                                        tool_content = str(result_data)
                                else:
                                    # Other types: convert to string
                                    tool_content = str(result_data)
                            else:
                                tool_content = f"Error: {tool_result.get('error', 'Unknown error')}"
                        else:
                            tool_content = str(tool_result)
                    except Exception as e:
                        logger.error(f"Error parsing tool result: {e}", exc_info=True)
                        tool_content = f"Error parsing result: {str(e)}"

                    logger.info(f"Parsed tool content length: {len(tool_content)}")
                    logger.info(f"Parsed tool content preview: {tool_content[:500]}...")

                    # Safely serialize tool_result for response
                    # Convert to fully JSON-serializable format
                    def make_serializable(obj):
                        """Recursively convert object to JSON-serializable format"""
                        if obj is None or isinstance(obj, (str, int, float, bool)):
                            return obj
                        elif isinstance(obj, dict):
                            return {str(k): make_serializable(v) for k, v in obj.items()}
                        elif isinstance(obj, (list, tuple)):
                            return [make_serializable(item) for item in obj]
                        else:
                            # For any other type, convert to string
                            return str(obj)

                    safe_tool_result = make_serializable(tool_result)

                    # Verify it's actually serializable
                    try:
                        json.dumps(safe_tool_result)
                        logger.info(f"Tool result successfully serialized")
                    except (TypeError, ValueError) as e:
                        logger.error(f"Tool result STILL not serializable: {e}, using fallback")
                        safe_tool_result = {
                            "success": False,
                            "error": "Result serialization failed",
                            "raw": str(tool_result)
                        }

                    response_data["tool_calls"].append({
                        "name": function_name,
                        "arguments": function_args,
                        "result": safe_tool_result
                    })

                    # Add tool response to messages (send as string for OpenAI)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_content
                    })

                # Get final response after tool execution
                try:
                    second_completion = await asyncio.to_thread(
                        self.client.chat.completions.create,
                        model=self.model,
                        messages=messages
                    )

                    response_data["response"] = second_completion.choices[0].message.content
                    response_data["tokens_used"] += second_completion.usage.total_tokens
                except Exception as e:
                    logger.error(f"Second OpenAI API call failed: {str(e)}", exc_info=True)
                    return {
                        "success": False,
                        "error": f"Failed to get final response from LLM: {str(e)}"
                    }
            else:
                # No tool calls, just return the response
                response_data["response"] = response_message.content

            return response_data

        except Exception as e:
            logger.error(f"Error in playground chat: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
