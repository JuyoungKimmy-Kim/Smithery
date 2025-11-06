# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DS Smithery is a full-stack MCP (Model Context Protocol) Server Marketplace that allows users to discover, register, and manage MCP servers. The application consists of a FastAPI backend (Python) and Next.js frontend (TypeScript/React).

## Development Commands

### Backend (FastAPI - Port 8000)

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend server
python main.py

# Run tests
pytest

# Run specific test
pytest test/unit_test/test_specific.py -v

# Initialize database
python init_database.py

# Insert dummy data for development
PYTHONPATH=. python tools/test_insert_dummy.py
```

### Frontend (Next.js - Port 3000)

```bash
# Change to frontend directory
cd frontend

# Set Node.js version
nvm use 18

# Install dependencies
npm install

# Development server
npm run dev

# Production build
npm run build

# Production server
npm run start

# Lint
npm run lint
```

### MCP Testing

```bash
# Test MCP proxy service
cd backend
python test_mcp_proxy.py http://localhost:8000/mcp

# Test STDIO-based MCP server
python test_mcp_proxy.py --stdio "node my_mcp_server.js"

# Run all MCP tests
chmod +x test_mcp_commands.sh
./test_mcp_commands.sh
```

## Architecture

### Backend Structure (backend/)

The backend follows a layered architecture:

**Database Layer** (`backend/database/`)
- **Models** (`model/`): SQLAlchemy ORM models defining database schema
  - `MCPServer`: Core MCP server information with github_link, name, description, transport type
  - `MCPServerTool`: Tools exposed by MCP servers
  - `MCPServerProperty`: Additional properties for MCP servers
  - `User`: User accounts with email authentication
  - `Tag`: Tags for categorizing servers (many-to-many with MCPServer via mcp_server_tags)
  - `Comment`: User comments on MCP servers
  - `UserFavorite`: User favorites tracking
  - `PlaygroundUsage`: Tracks playground query usage per user per day for rate limiting
- **DAOs** (`dao/`): Data Access Objects for database operations
  - `MCPServerDAO`: CRUD operations for MCP servers
  - `UserDAO`: User management operations
- **Database** (`database.py`): SQLAlchemy session management and connection
- **Init** (`init_db.py`): Database initialization and table creation

**Service Layer** (`backend/service/`)
- `mcp_proxy_service.py`: **Core service** - Proxies MCP server requests to handle CORS and mixed content issues. Implements multiple transport types (STDIO, HTTP, HTTP-Stream, WebSocket, SSE) using abstract MCPTransport base class pattern inspired by the inspector module. Now includes `call_tool()` method for executing MCP tools
- `mcp_server_service.py`: Business logic for MCP server operations
- `github_api_service.py`: GitHub API integration for fetching server metadata
- `user_service.py`: User authentication and management
- `playground_service.py`: **NEW** - Integrates LLM (OpenAI GPT) with MCP servers for interactive playground feature. Handles rate limiting, tool calling, and conversation management

**API Layer** (`backend/api/`)
- `endpoints/mcp_servers.py`: RESTful endpoints for MCP server CRUD operations
- `endpoints/auth.py`: Authentication endpoints
- `endpoints/comments.py`: Comment management endpoints
- `endpoints/playground.py`: **NEW** - Playground endpoints for chat and rate limiting
- `auth.py`: JWT authentication utilities
- `schemas.py`: Pydantic request/response schemas (includes playground schemas)

**Main Entry** (`backend/main.py`)
- FastAPI app initialization
- CORS middleware configuration
- Router registration with `/api/v1` prefix
- Database initialization on startup
- Runs on port 8000

### Frontend Structure (frontend/src/)

**Pages** (`app/`)
- Next.js 13+ App Router structure
- Server and client components
- API routes that proxy to backend

**Components** (`components/`)
- Reusable React UI components
- Tailwind CSS styling
- `playground-chat.tsx`: **NEW** - Interactive chat UI for testing MCP servers with LLM

**Contexts** (`contexts/`)
- React Context providers for global state management

**Types** (`types/`)
- TypeScript type definitions matching backend Pydantic models

**Libraries** (`lib/`)
- Utility functions and helpers

**Content** (`content/`)
- Static content and blog posts

### Inspector Module (inspector/)

A separate MCP Inspector tool (appears to be a git submodule) for testing and debugging MCP servers. The backend's MCP proxy service architecture is inspired by the inspector's transport patterns.

## Key Technical Details

### MCP Transport Types

The application supports multiple MCP transport protocols:
- **STDIO**: Command-line based communication via stdin/stdout
- **HTTP**: Standard HTTP JSON-RPC
- **HTTP-Stream**: Streaming responses (NDJSON or SSE)
- **WebSocket**: Bidirectional real-time communication
- **SSE**: Server-Sent Events

Each transport type implements the `MCPTransport` abstract base class with `connect()`, `send_request()`, and `close()` methods.

### Database

- **Engine**: SQLite (`mcp_market.db` in project root)
- **ORM**: SQLAlchemy with declarative Base
- **Schema**: See `database_structure.md` for full schema documentation
- Database automatically initializes on backend startup via `init_database()` in main.py

### API Communication

- Backend runs on port 8000, frontend on port 3000
- Frontend proxies API calls through Next.js API routes to avoid CORS issues
- All API endpoints prefixed with `/api/v1` on backend
- Frontend uses `/api` routes that forward to backend

### Authentication

- JWT-based authentication
- User model stores email, hashed passwords, and profile data
- Auth utilities in `backend/api/auth.py`

### Playground Feature

**NEW**: Interactive MCP testing with LLM integration
- Located in MCP server detail pages (`/mcp/[id]`)
- Requires user authentication
- Rate limited to 10 queries per user per server per day
- Integrates OpenAI GPT models with MCP server tools
- Supports DeepSeek and custom internal LLM APIs (see `PLAYGROUND_SETUP.md`)

**Environment Variables Required:**
- `OPENAI_API_KEY`: Your OpenAI API key (or custom LLM API key)
- `OPENAI_MODEL`: Model to use (default: `gpt-4-turbo-preview`)

**Architecture Flow:**
1. User sends message in PlaygroundChat component
2. Frontend → Next.js API route → Backend playground endpoint
3. Backend fetches MCP tools via `mcp_proxy_service`
4. Backend calls OpenAI with tools as function definitions
5. LLM decides which tools to call (if any)
6. Backend executes tool calls on MCP server
7. Backend sends final response back to frontend

**Documentation:** See `PLAYGROUND_SETUP.md` for detailed setup and configuration

## Development Workflow

1. **Always activate the virtual environment** before working with backend code
2. **Run backend first** (port 8000) before frontend (port 3000)
3. **Database migrations**: Currently manual - modify models and reinitialize if needed
4. **Testing MCP servers**: Use `test_mcp_proxy.py` or `test_mcp_commands.sh` to verify connectivity before integrating
5. **Frontend API calls**: Always go through Next.js API routes, never directly to backend from client components

## Common Issues

### Port Conflicts
Check and kill processes using ports 3000 or 8000:
```bash
ss -tlnp | grep :8000
pkill -f "python main.py"
```

### Database Issues
If tables are missing, reinitialize:
```bash
python init_database.py
```

### MCP Proxy Issues
When MCP servers fail to return tools, use the MCP Test Guide (`backend/MCP_TEST_GUIDE.md`) to debug transport-specific issues. Check Content-Type headers and response formats.

## File Naming Conventions

- Python: snake_case (e.g., `mcp_proxy_service.py`)
- TypeScript/React: camelCase for variables, PascalCase for components
- Database models: PascalCase classes (e.g., `MCPServer`)
- SQL files: snake_case with descriptive names (e.g., `add_comments_table.sql`)
