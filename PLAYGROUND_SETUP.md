# Playground Feature Setup Guide

This guide explains how to set up and configure the Playground feature for the MCP Server Marketplace.

## Overview

The Playground feature allows authenticated users to test MCP servers directly in the browser by chatting with an LLM (Language Learning Model) that has access to the MCP server's tools.

## Architecture

```
User Browser
    ↓
Next.js Frontend (PlaygroundChat component)
    ↓
Next.js API Routes (/api/mcps/[id]/playground/*)
    ↓
FastAPI Backend (/api/v1/mcp-servers/{id}/playground/*)
    ↓
PlaygroundService (LLM + MCP Integration)
    ↓
┌─────────────┬─────────────────────┐
│   OpenAI    │   MCP Server        │
│   GPT-4     │   (via MCP Proxy)   │
└─────────────┴─────────────────────┘
```

## Environment Variables

### Backend Configuration

Add these environment variables to your backend environment (`.env` file or system environment):

```bash
# Required: OpenAI API Key
OPENAI_API_KEY=sk-...your-openai-api-key...

# Optional: Model Selection (default: gpt-4-turbo-preview)
OPENAI_MODEL=gpt-4-turbo-preview

# Alternative models you can use:
# OPENAI_MODEL=gpt-3.5-turbo          # Cheaper, faster, less capable
# OPENAI_MODEL=gpt-4                  # Standard GPT-4
# OPENAI_MODEL=gpt-4-turbo-preview    # Recommended
```

### Using Internal Company LLM APIs

If you're using internal company APIs (DeepSeek, internal GPT deployment, etc.), you need to modify `backend/service/playground_service.py`:

#### Option 1: OpenAI-Compatible API

If your internal API is OpenAI-compatible (supports the same API format):

```python
# In PlaygroundService.__init__()
self.client = OpenAI(
    api_key=self.api_key,
    base_url="https://your-internal-api.company.com/v1"  # Add this line
)
```

#### Option 2: Custom API Integration

For DeepSeek or other custom APIs, modify the `chat()` method in `playground_service.py`:

```python
# Replace OpenAI client calls with your API client
# Example for DeepSeek:
import requests

response = requests.post(
    "https://api.deepseek.com/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json"
    },
    json={
        "model": "deepseek-chat",
        "messages": messages,
        "tools": tools,  # Make sure your API supports function calling
    }
)
```

## Features

### Rate Limiting

- **Daily Limit**: 10 queries per user per MCP server per day
- Limit resets at midnight (UTC)
- Usage tracked in `playground_usage` table

To adjust the limit, modify `DAILY_QUERY_LIMIT` in `backend/service/playground_service.py`:

```python
class PlaygroundService:
    DAILY_QUERY_LIMIT = 10  # Change this value
```

### Database Schema

The playground uses a new table:

```sql
CREATE TABLE playground_usage (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    mcp_server_id INTEGER NOT NULL,
    query_count INTEGER DEFAULT 0,
    date DATE NOT NULL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (mcp_server_id) REFERENCES mcp_servers(id)
);
```

This table is automatically created when the backend starts.

## Testing the Playground

### 1. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY=sk-...your-key...
export OPENAI_MODEL=gpt-4-turbo-preview

# Run backend
python main.py
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run frontend
npm run dev
```

### 3. Test the Feature

1. Navigate to any MCP server detail page: `http://localhost:3000/mcp/[server-id]`
2. Scroll down to the "🎮 Try it out!" section
3. Log in if not authenticated
4. Start chatting!

Example queries:
- "What tools are available?"
- "Can you fetch weather data for Tokyo?"
- "List all the available resources"

## Troubleshooting

### Error: "OpenAI API key not configured on server"

**Solution**: Make sure `OPENAI_API_KEY` environment variable is set in the backend.

```bash
# Check if set
echo $OPENAI_API_KEY

# Set it
export OPENAI_API_KEY=sk-...
```

### Error: "MCP server URL not found in configuration"

**Solution**: The MCP server must have a valid `server_url` or `config` with connection details.

Check the server's config:
```sql
SELECT id, name, server_url, config FROM mcp_servers WHERE id = [server-id];
```

### Error: "Rate limit exceeded"

**Solution**: User has used all 10 daily queries. They need to wait until tomorrow or you can manually reset:

```sql
-- Check usage
SELECT * FROM playground_usage WHERE user_id = [user-id] AND date = CURRENT_DATE;

-- Reset usage
DELETE FROM playground_usage WHERE user_id = [user-id] AND mcp_server_id = [server-id] AND date = CURRENT_DATE;
```

### Tool calls not working

**Solution**: Ensure:
1. MCP server is running and accessible
2. MCP server exposes tools via `list_tools()`
3. Tools have proper `inputSchema` definitions
4. LLM model supports function calling (GPT-4, GPT-3.5-turbo do)

## Cost Estimation

Using OpenAI GPT-4 Turbo:
- Input: $0.01 per 1K tokens
- Output: $0.03 per 1K tokens
- Average query: ~1,000 tokens = $0.04

With 100 users × 10 queries/day:
- Daily cost: ~$40
- Monthly cost: ~$1,200

**Cost reduction strategies:**
1. Use GPT-3.5-turbo (70% cheaper)
2. Lower daily query limit
3. Use internal company LLM APIs
4. Implement caching for common queries

## Security Considerations

1. **API Key Security**: Never expose OpenAI API key to frontend
2. **Rate Limiting**: Prevents abuse and cost overruns
3. **Authentication Required**: Only logged-in users can access
4. **Input Validation**: All user inputs are validated
5. **Timeout Protection**: 120s timeout for MCP calls

## Future Enhancements

- [ ] WebSocket support for real-time streaming responses
- [ ] Conversation history persistence in database
- [ ] Support for multiple LLM providers (Claude, Gemini, etc.)
- [ ] Playground sharing feature (share conversation links)
- [ ] Admin dashboard for usage analytics
- [ ] Token usage tracking and billing
- [ ] Custom system prompts per MCP server
- [ ] Example prompts/queries for each MCP server

## API Reference

### Get Rate Limit

```
GET /api/v1/mcp-servers/{server_id}/playground/rate-limit
Authorization: Bearer {token}

Response:
{
  "allowed": true,
  "remaining": 8,
  "used": 2
}
```

### Send Chat Message

```
POST /api/v1/mcp-servers/{server_id}/playground/chat
Authorization: Bearer {token}
Content-Type: application/json

Request:
{
  "message": "What tools are available?",
  "conversation_history": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi! How can I help?"}
  ]
}

Response:
{
  "success": true,
  "response": "This server has 5 tools available: fetch_data, process_text, ...",
  "tool_calls": [
    {
      "name": "list_tools",
      "arguments": {},
      "result": {...}
    }
  ],
  "tokens_used": 450
}
```

## Support

For issues or questions:
1. Check backend logs: `tail -f backend.log`
2. Check browser console for frontend errors
3. Review this documentation
4. Check MCP server connectivity with existing tools
