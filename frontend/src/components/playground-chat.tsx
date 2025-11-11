"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  PaperAirplaneIcon,
  ArrowPathIcon,
  WrenchScrewdriverIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
} from "@heroicons/react/24/outline";
import { useAuth } from "@/contexts/AuthContext";
import { apiFetch } from "@/lib/api-client";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  tool_calls?: Array<{
    name: string;
    arguments: any;
    result: any;
  }>;
  tokens_used?: number;
}

interface Tool {
  name: string;
  description: string;
}

interface PlaygroundChatProps {
  mcpServerId: number;
  tools?: Tool[];
}

export default function PlaygroundChat({ mcpServerId, tools = [] }: PlaygroundChatProps) {
  const { isAuthenticated } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [rateLimit, setRateLimit] = useState<{
    allowed: boolean;
    remaining: number;
    used: number;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [authToken, setAuthToken] = useState("");
  const [tokenInputVisible, setTokenInputVisible] = useState(false);
  const [tokenSaved, setTokenSaved] = useState(false);
  const [onboardingStep, setOnboardingStep] = useState<number>(0);
  const [hasUsedPlayground, setHasUsedPlayground] = useState(false);
  const [showUsageLimitExplanation, setShowUsageLimitExplanation] = useState(false);
  const [showAuthExplanation, setShowAuthExplanation] = useState(false);
  const [showInputExplanation, setShowInputExplanation] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      fetchRateLimit();

      // Check if user has used playground before (using localStorage)
      const playgroundUsedKey = `playground_used_${mcpServerId}`;
      const hasUsed = localStorage.getItem(playgroundUsedKey);
      if (!hasUsed) {
        setOnboardingStep(1); // Start onboarding
      } else {
        setHasUsedPlayground(true);
      }
    }
  }, [isAuthenticated, mcpServerId]);

  const fetchRateLimit = async () => {
    try {
      const response = await apiFetch(
        `/api/mcps/${mcpServerId}/playground/rate-limit`,
        { requiresAuth: true }
      );

      if (response.ok) {
        const data = await response.json();
        setRateLimit(data);
      }
    } catch (error) {
      console.error("Failed to fetch rate limit:", error);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    if (!rateLimit?.allowed) {
      setError("You have reached your daily query limit. Please try again tomorrow.");
      return;
    }

    // Mark playground as used
    if (!hasUsedPlayground) {
      const playgroundUsedKey = `playground_used_${mcpServerId}`;
      localStorage.setItem(playgroundUsedKey, "true");
      setHasUsedPlayground(true);
    }

    const userMessage: Message = {
      role: "user",
      content: inputMessage,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiFetch(
        `/api/mcps/${mcpServerId}/playground/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: inputMessage,
            conversation_history: messages.map((m) => ({
              role: m.role,
              content: m.content,
            })),
            mcp_auth_token: authToken || undefined,
          }),
          requiresAuth: true,
        }
      );

      if (response.ok) {
        const data = await response.json();

        if (data.success) {
          const assistantMessage: Message = {
            role: "assistant",
            content: data.response || "No response",
            tool_calls: data.tool_calls || [],
            tokens_used: data.tokens_used,
          };

          setMessages((prev) => [...prev, assistantMessage]);

          // Refresh rate limit
          await fetchRateLimit();
        } else {
          setError(data.error || "Failed to get response");
        }
      } else {
        const errorData = await response.json();
        setError(errorData.detail || "Failed to send message");
      }
    } catch (error) {
      console.error("Error sending message:", error);
      setError("An error occurred while sending the message");
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    setError(null);
  };

  const handleUsageLimitClick = () => {
    if (onboardingStep === 1) {
      setShowUsageLimitExplanation(true);
    }
  };

  const handleUsageLimitOk = () => {
    setShowUsageLimitExplanation(false);
    setOnboardingStep(2);
  };

  const handleAuthSectionClick = () => {
    if (onboardingStep === 2) {
      setTokenInputVisible(true);
      setShowAuthExplanation(true);
    } else {
      setTokenInputVisible(!tokenInputVisible);
    }
  };

  const handleAuthOk = () => {
    setShowAuthExplanation(false);
    setOnboardingStep(3);
  };

  const handleInputClick = () => {
    if (onboardingStep === 3) {
      setShowInputExplanation(true);
    }
  };

  const handleInputOk = () => {
    setShowInputExplanation(false);
    setOnboardingStep(0);
    const playgroundUsedKey = `playground_used_${mcpServerId}`;
    localStorage.setItem(playgroundUsedKey, "true");
    setHasUsedPlayground(true);
  };

  if (!isAuthenticated) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
        <ExclamationTriangleIcon className="h-12 w-12 text-yellow-600 mx-auto mb-3" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Login Required
        </h3>
        <p className="text-gray-600">
          Please log in to try the playground feature.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col h-[600px]">
      {/* Info Banner */}
      <div className="bg-yellow-50 border-b border-yellow-100 px-4 py-3">
        <div className="flex items-start gap-2">
          <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-yellow-800">
            <strong className="font-semibold">Note:</strong> This playground uses an LLM to test MCP tools interactively.
            Results may differ from native MCP clients (Claude Desktop, Roo Code, etc.) due to different prompting strategies and tool calling implementations.
          </div>
        </div>
      </div>

      {/* Header */}
      <div className="border-b border-gray-200 p-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <WrenchScrewdriverIcon className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            Playground (Beta)
          </h3>
        </div>
        <div className="flex items-center gap-4">
          {rateLimit && (
            <div
              onClick={handleUsageLimitClick}
              className={`text-sm ${onboardingStep === 1 ? 'cursor-pointer animate-pulse bg-blue-50 px-3 py-1.5 rounded-md relative' : ''}`}
            >
              <span className="text-gray-600">Usage: </span>
              <span
                className={`font-semibold ${
                  rateLimit.remaining <= 2 ? "text-red-600" : onboardingStep === 1 ? "text-blue-700" : "text-gray-900"
                }`}
              >
                {rateLimit.used}/{rateLimit.used + rateLimit.remaining}
              </span>
              <span className={`ml-1 ${onboardingStep === 1 ? 'text-blue-700' : 'text-gray-500'}`}>queries today</span>
              {onboardingStep === 1 && (
                <span className="absolute -top-6 right-0 text-xs bg-blue-600 text-white px-2 py-0.5 rounded-full animate-pulse whitespace-nowrap">
                  Click here!
                </span>
              )}
            </div>
          )}
          <button
            onClick={handleClearChat}
            className="text-sm text-gray-600 hover:text-gray-800 transition-colors"
            disabled={messages.length === 0}
          >
            Clear
          </button>
        </div>
      </div>

      {/* Step 1: Usage Limit Explanation */}
      {showUsageLimitExplanation && (
        <div className="bg-blue-50 border-b border-blue-200 px-4 py-3">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="text-lg">📊</span>
              <span className="font-semibold text-sm text-gray-900">Step 1: Usage Limits</span>
              <span className="text-sm text-gray-700">- This playground has a daily usage limit (5 queries per server per day).</span>
            </div>
            <button
              onClick={handleUsageLimitOk}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium whitespace-nowrap flex-shrink-0"
            >
              OK
            </button>
          </div>
        </div>
      )}

      {/* Auth Token Section */}
      <div className={`border-b border-gray-200 bg-gray-50 ${onboardingStep === 2 ? 'relative' : ''}`}>
        <button
          onClick={handleAuthSectionClick}
          className={`w-full px-4 py-3 flex items-center justify-between hover:bg-gray-100 transition-colors ${
            onboardingStep === 2 ? 'animate-pulse bg-blue-50' : ''
          }`}
        >
          <div className="flex items-center gap-2">
            <span className={`text-sm font-medium ${onboardingStep === 2 ? 'text-blue-700' : 'text-gray-700'}`}>
              🔑 Authentication (Optional)
            </span>
            {tokenSaved && (
              <CheckCircleIcon className="h-4 w-4 text-green-600" />
            )}
            {onboardingStep === 2 && (
              <span className="text-xs bg-blue-600 text-white px-2 py-0.5 rounded-full animate-pulse">
                Click here!
              </span>
            )}
          </div>
          <svg
            className={`h-5 w-5 text-gray-500 transition-transform ${
              tokenInputVisible ? "rotate-180" : ""
            }`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>

        {tokenInputVisible && showAuthExplanation && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 mb-3 mt-3 mx-4">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <span className="text-lg">🔑</span>
                <span className="font-semibold text-sm text-gray-900">Step 2: Authentication</span>
                <span className="text-sm text-gray-700">- Some MCP servers require authentication. Enter your API token here if needed.</span>
              </div>
              <button
                onClick={handleAuthOk}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium whitespace-nowrap flex-shrink-0"
              >
                OK
              </button>
            </div>
          </div>
        )}

        {tokenInputVisible && !showAuthExplanation && (
          <div className="px-4 pb-4 space-y-2">
            <p className="text-xs text-gray-600">
              Some MCP servers require authentication. Enter your API token here if needed.
            </p>
            <div className="flex gap-2">
              <input
                type="password"
                value={authToken}
                onChange={(e) => setAuthToken(e.target.value)}
                placeholder="Enter API token..."
                className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={() => setTokenSaved(!!authToken)}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
              >
                Save
              </button>
            </div>
            {tokenSaved && authToken && (
              <p className="text-xs text-green-600 flex items-center gap-1">
                <CheckCircleIcon className="h-3 w-3" />
                Token configured. It will be included in requests.
              </p>
            )}
            {tokenSaved && !authToken && (
              <p className="text-xs text-gray-500">
                Token cleared.
              </p>
            )}
          </div>
        )}
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <p className="mb-2">Start a conversation!</p>
            <p className="text-sm">
              Ask questions and the AI will use this MCP server's tools to help
              you.
            </p>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${
              message.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                message.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-900"
              }`}
            >
              <div className="prose prose-sm max-w-none break-words">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    // Custom styling for markdown elements
                    p: ({ node, ...props }) => (
                      <p className="mb-2 last:mb-0" {...props} />
                    ),
                    code: ({ node, inline, ...props }: any) =>
                      inline ? (
                        <code
                          className={`${
                            message.role === "user"
                              ? "bg-blue-700 text-white"
                              : "bg-gray-200 text-gray-900"
                          } px-1 py-0.5 rounded text-sm`}
                          {...props}
                        />
                      ) : (
                        <code
                          className="block bg-gray-800 text-gray-100 p-2 rounded text-sm overflow-x-auto"
                          {...props}
                        />
                      ),
                    pre: ({ node, ...props }) => (
                      <pre className="my-2 overflow-x-auto" {...props} />
                    ),
                    ul: ({ node, ...props }) => (
                      <ul className="list-disc list-inside mb-2" {...props} />
                    ),
                    ol: ({ node, ...props }) => (
                      <ol className="list-decimal list-inside mb-2" {...props} />
                    ),
                    li: ({ node, ...props }) => (
                      <li className="mb-1" {...props} />
                    ),
                    a: ({ node, ...props }) => (
                      <a
                        className={`underline ${
                          message.role === "user"
                            ? "text-blue-200 hover:text-blue-100"
                            : "text-blue-600 hover:text-blue-800"
                        }`}
                        target="_blank"
                        rel="noopener noreferrer"
                        {...props}
                      />
                    ),
                    blockquote: ({ node, ...props }) => (
                      <blockquote
                        className={`border-l-4 pl-3 my-2 italic ${
                          message.role === "user"
                            ? "border-blue-400"
                            : "border-gray-400"
                        }`}
                        {...props}
                      />
                    ),
                    h1: ({ node, ...props }) => (
                      <h1 className="text-xl font-bold mb-2 mt-2" {...props} />
                    ),
                    h2: ({ node, ...props }) => (
                      <h2 className="text-lg font-bold mb-2 mt-2" {...props} />
                    ),
                    h3: ({ node, ...props }) => (
                      <h3 className="text-md font-bold mb-1 mt-1" {...props} />
                    ),
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>

              {/* Tool Calls */}
              {message.tool_calls && message.tool_calls.length > 0 && (
                <div className="mt-3 space-y-2">
                  {message.tool_calls.map((toolCall, idx) => (
                    <div
                      key={idx}
                      className="bg-white bg-opacity-10 rounded p-2 text-sm"
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <CheckCircleIcon className="h-4 w-4" />
                        <span className="font-semibold">
                          Tool: {toolCall.name}
                        </span>
                      </div>
                      <div className="text-xs opacity-80">
                        Arguments: {JSON.stringify(toolCall.arguments)}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Token usage */}
              {message.tokens_used && (
                <div className="mt-2 text-xs opacity-70">
                  {message.tokens_used} tokens used
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-3">
              <div className="flex items-center gap-2">
                <ArrowPathIcon className="h-4 w-4 animate-spin text-gray-600" />
                <span className="text-gray-600">Thinking...</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="px-4 py-2 bg-red-50 border-t border-red-200">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Input Area */}
      <div className="border-t border-gray-200 p-4">
        {showInputExplanation && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-3">
            <div className="text-sm text-gray-700 mb-3">
              <p className="font-semibold mb-2 text-gray-900">💬 Step 3: Start Chatting</p>
              <p className="mb-3">
                Type your message in the input box below. Check the <strong>Tools tab</strong> above to see available capabilities.
              </p>
              <div className="bg-white border border-blue-200 rounded-lg p-3">
                <p className="text-sm font-medium text-gray-700 mb-2">Example questions:</p>
                <ul className="space-y-1.5 text-sm text-gray-600">
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 mt-0.5">•</span>
                    <span>
                      If you have <span className="font-mono text-xs bg-blue-100 px-1 py-0.5 rounded">search_doc</span>, try: "Can you search for information about..."
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 mt-0.5">•</span>
                    <span>
                      If you have <span className="font-mono text-xs bg-blue-100 px-1 py-0.5 rounded">get_weather</span>, try: "What's the weather today?"
                    </span>
                  </li>
                </ul>
              </div>
            </div>
            <div className="flex justify-end">
              <button
                onClick={handleInputOk}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
              >
                OK
              </button>
            </div>
          </div>
        )}

        <div className={`flex gap-2 ${onboardingStep === 3 ? 'relative' : ''}`}>
          <div className="flex-1 relative">
            {onboardingStep === 3 ? (
              <div
                onClick={handleInputClick}
                className="w-full px-4 py-2 border-2 border-blue-400 rounded-lg animate-pulse cursor-pointer bg-white flex items-center"
              >
                <span className="text-gray-400">Type your message...</span>
              </div>
            ) : (
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                disabled={isLoading || !rateLimit?.allowed}
              />
            )}
            {onboardingStep === 3 && (
              <span className="absolute -top-8 left-0 text-xs bg-blue-600 text-white px-2 py-1 rounded-full animate-pulse">
                Click here to continue!
              </span>
            )}
          </div>
          <button
            onClick={handleSendMessage}
            disabled={isLoading || !inputMessage.trim() || !rateLimit?.allowed || !hasUsedPlayground || onboardingStep > 0}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <PaperAirplaneIcon className="h-4 w-4" />
            Send
          </button>
        </div>

        {rateLimit && !rateLimit.allowed && (
          <p className="text-sm text-red-600 mt-2">
            Daily limit reached. Try again tomorrow!
          </p>
        )}
      </div>

    </div>
  );
}
