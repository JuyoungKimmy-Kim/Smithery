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

    # Multi-hop reasoning constants
    MAX_ITERATIONS = 5  # Maximum number of tool calling rounds to prevent infinite loops

    # Shared OpenAI client (singleton pattern to reuse connections)
    _shared_client = None
    _client_config = None

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
            # Reuse shared client if config matches to avoid creating multiple connection pools
            current_config = (self.api_key, self.base_url)

            if PlaygroundService._shared_client is None or PlaygroundService._client_config != current_config:
                logger.info("Creating new shared OpenAI client")
                # Use default OpenAI client without custom http_client to avoid connection leaks
                # OpenAI SDK handles connection pooling internally
                if self.base_url:
                    PlaygroundService._shared_client = OpenAI(
                        api_key=self.api_key,
                        base_url=self.base_url,
                        max_retries=2,  # Limit retries to prevent excessive server load
                        timeout=180.0   # Overall timeout (3 minutes)
                    )
                else:
                    PlaygroundService._shared_client = OpenAI(
                        api_key=self.api_key,
                        max_retries=2,
                        timeout=180.0
                    )
                PlaygroundService._client_config = current_config

            self.client = PlaygroundService._shared_client
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

    async def get_mcp_tools(self, mcp_server_url: str, protocol: str, user_token: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch tools from MCP server

        Args:
            mcp_server_url: MCP server URL or command
            protocol: Protocol type (stdio, sse, http, etc.)
            user_token: Optional authentication token for MCP server

        Returns:
            List of tools in OpenAI function format
        """
        try:
            result = await MCPProxyService.fetch_tools(mcp_server_url, protocol, user_token)

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
            user_token: Optional authentication token for MCP server

        Returns:
            Tool execution result
        """
        try:
            # Use MCPProxyService to call the tool
            result = await MCPProxyService.call_tool(
                mcp_server_url,
                protocol,
                tool_name,
                arguments,
                user_token
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
        conversation_history: Optional[List[Dict[str, str]]] = None,
        user_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a chat message and get response with MCP tool integration

        Args:
            message: User message
            mcp_server_url: MCP server URL or command
            protocol: Protocol type
            conversation_history: Previous conversation messages
            user_token: Optional authentication token for MCP server

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
            # Must be less than endpoint timeout (180s) to allow proper cleanup
            return await asyncio.wait_for(
                self._chat_internal(message, mcp_server_url, protocol, conversation_history, user_token),
                timeout=170.0  # Maximum 170s (less than endpoint's 180s)
            )
        except asyncio.TimeoutError:
            logger.error("Chat operation timed out after 170 seconds")
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
        conversation_history: Optional[List[Dict[str, str]]] = None,
        user_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Internal chat implementation with error handling
        """
        try:
            # Get MCP tools
            tools = await self.get_mcp_tools(mcp_server_url, protocol, user_token)

            # Build messages
            messages = conversation_history or []

            # Add system prompt to encourage tool usage and multi-hop reasoning when tools are available
            if tools and (not messages or messages[0].get("role") != "system"):
                system_message = {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant with access to tools. "
                        "When answering questions, ALWAYS check if there are relevant tools available that could provide accurate information. "
                        "If a tool can help answer the user's question, you MUST use it instead of relying on general knowledge.\n\n"

                        "MULTI-STEP REASONING:\n"
                        "- You can call tools MULTIPLE TIMES in sequence to gather comprehensive information\n"
                        "- After seeing tool results, analyze if you need MORE information\n"
                        "- You can call different tools based on what you learned from previous tool calls\n"
                        f"- You have up to {self.MAX_ITERATIONS} rounds of tool calls available\n"
                        "- When you have sufficient information, provide your final answer\n\n"

                        "REASONING STRATEGY:\n"
                        "1. Identify what information you need to answer the question\n"
                        "2. Call relevant tools to gather that information\n"
                        "3. Analyze the results - do you need additional details or clarification?\n"
                        "4. If yes, call more tools based on what you learned\n"
                        "5. If no, synthesize the information and provide a complete answer\n\n"

                        "EXAMPLES:\n"
                        "- For 'How do I use feature X?': search_doc → read specific sections → get_examples\n"
                        "- For 'What are the differences between X and Y?': get_details(X) → get_details(Y) → compare\n"
                        "- For 'Find information about Z': search → analyze results → get_specific_info\n\n"

                        "Always use tools when available rather than guessing or using general knowledge."
                    )
                }
                messages.insert(0, system_message)

            messages.append({
                "role": "user",
                "content": message
            })

            # Initialize response data with iteration tracking
            response_data = {
                "success": True,
                "response": "",
                "tool_calls": [],
                "tokens_used": 0,
                "iterations": 0  # Track number of reasoning rounds
            }

            # Multi-hop reasoning loop: Allow LLM to call tools multiple times
            iteration = 0
            while iteration < self.MAX_ITERATIONS:
                iteration += 1
                response_data["iterations"] = iteration

                logger.info(f"Multi-hop iteration {iteration}/{self.MAX_ITERATIONS}")

                # LLM API call - run in executor to make it truly async
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
                response_data["tokens_used"] += completion.usage.total_tokens

                # Check if tool calls were made
                if response_message.tool_calls:
                    # LLM wants to call tools - continue loop
                    logger.info(f"LLM requested {len(response_message.tool_calls)} tool calls in iteration {iteration}")

                    # Ensure content field exists (some models omit it with tool calls)
                    # Convert response_message to dict format with guaranteed content field
                    response_message_dict = {
                        "role": "assistant",
                        "content": response_message.content if response_message.content else "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            } for tc in response_message.tool_calls
                        ]
                    }
                    messages.append(response_message_dict)

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
                                function_args,
                                user_token
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
                        "result": safe_tool_result,
                        "iteration": iteration  # Track which iteration this tool call belongs to
                    })

                    # Add tool response to messages (send as string for OpenAI)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_content
                    })

                    # After adding all tool results, loop will continue to next iteration
                    # LLM will see the tool results and decide whether to call more tools or provide final answer
                else:
                    # No tool calls - LLM provided final answer, exit loop
                    logger.info(f"LLM provided final answer in iteration {iteration}, exiting loop")
                    response_data["response"] = response_message.content
                    break  # Exit while loop

            # If we reach here, we hit MAX_ITERATIONS without a final answer
            # Force a final completion to get an answer based on gathered information
            if not response_data["response"]:
                logger.warning(f"Reached MAX_ITERATIONS ({self.MAX_ITERATIONS}) without final answer, forcing completion")

                try:
                    # Add a system message to encourage summarization
                    messages.append({
                        "role": "system",
                        "content": (
                            "You have reached the maximum number of tool calls. "
                            "Please provide a final answer based on the information you have gathered so far. "
                            "Summarize what you learned and answer the user's question to the best of your ability."
                        )
                    })

                    forced_completion = await asyncio.to_thread(
                        self.client.chat.completions.create,
                        model=self.model,
                        messages=messages
                    )

                    response_data["response"] = forced_completion.choices[0].message.content
                    response_data["tokens_used"] += forced_completion.usage.total_tokens
                    response_data["forced_completion"] = True  # Flag to indicate this was forced

                    logger.info("Successfully generated forced final response")
                except Exception as e:
                    logger.error(f"Failed to generate forced completion: {str(e)}", exc_info=True)
                    return {
                        "success": False,
                        "error": f"Reached maximum iterations and failed to generate final response: {str(e)}"
                    }

            return response_data

        except Exception as e:
            logger.error(f"Error in playground chat: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
