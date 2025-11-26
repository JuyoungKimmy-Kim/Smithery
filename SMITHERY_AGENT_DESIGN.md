# Smithery Agent 설계 문서

## 📋 개요

**Smithery Chatbot Agent** = VOC 수집 + 정보 안내 + Analytics 조회를 모두 처리하는 범용 챗봇

다양한 채널(MCP Hub, 웹사이트, Slack, Discord 등)에서 사용 가능한 통합 AI Agent

---

## 🏗️ 전체 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│  Multiple Channels (어디서든 사용 가능)                    │
├─────────────────────────────────────────────────────────┤
│  • Claude Desktop (MCP)                                 │
│  • Smithery Website (Chat Widget)                      │
│  • Slack Bot                                           │
│  • Discord Bot                                         │
│  • API (curl, Postman)                                 │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ 모두 같은 Agent 사용
                  ↓
┌─────────────────────────────────────────────────────────┐
│  Smithery Agent Core (Claude + ADK)                    │
│                                                         │
│  System Prompt:                                        │
│  "You are Smithery assistant. Help users with:        │
│   - Finding MCP servers                                │
│   - VOC collection (feedback, feature requests)        │
│   - Analytics insights                                 │
│   - General Q&A"                                       │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ Uses multiple MCP Tools
                  ↓
┌─────────────────────────────────────────────────────────┐
│  MCP Tools (Agent가 사용하는 기능들)                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  📊 Analytics Tools                                    │
│    - get_top_search_keywords                           │
│    - get_trending_servers                              │
│    - get_analytics_summary                             │
│                                                         │
│  🔍 Search & Browse Tools                              │
│    - search_servers                                    │
│    - get_server_details                                │
│    - list_servers_by_tag                               │
│    - get_popular_servers                               │
│                                                         │
│  💬 VOC & Feedback Tools                               │
│    - submit_feedback                                   │
│    - create_feature_request                            │
│    - report_bug                                        │
│    - get_user_suggestions                              │
│                                                         │
│  👤 User Management Tools                              │
│    - get_user_profile                                  │
│    - get_user_favorites                                │
│    - add_to_favorites                                  │
│                                                         │
│  📚 Knowledge Base Tools                               │
│    - search_documentation                              │
│    - get_faq_answer                                    │
│    - get_getting_started_guide                         │
│                                                         │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────┐
│  Smithery Backend API                                  │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ MCP Tools 상세 명세

### 1. 🔍 Search & Browse Tools

#### search_servers
```json
{
  "name": "search_servers",
  "description": "Search for MCP servers by keyword, tag, or description",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query"
      },
      "tags": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Filter by tags"
      },
      "limit": {
        "type": "number",
        "default": 10,
        "description": "Maximum number of results"
      }
    }
  }
}
```

#### get_server_details
```json
{
  "name": "get_server_details",
  "description": "Get detailed information about a specific MCP server",
  "inputSchema": {
    "type": "object",
    "properties": {
      "server_id": {
        "type": "number",
        "description": "MCP server ID"
      }
    },
    "required": ["server_id"]
  }
}
```

#### get_popular_servers
```json
{
  "name": "get_popular_servers",
  "description": "Get the most popular MCP servers",
  "inputSchema": {
    "type": "object",
    "properties": {
      "limit": {
        "type": "number",
        "default": 10
      },
      "time_period": {
        "type": "string",
        "enum": ["day", "week", "month", "all"],
        "default": "week"
      }
    }
  }
}
```

#### list_servers_by_tag
```json
{
  "name": "list_servers_by_tag",
  "description": "List all servers with a specific tag",
  "inputSchema": {
    "type": "object",
    "properties": {
      "tag": {
        "type": "string",
        "description": "Tag name"
      },
      "limit": {
        "type": "number",
        "default": 20
      }
    },
    "required": ["tag"]
  }
}
```

---

### 2. 💬 VOC & Feedback Tools

#### submit_feedback
```json
{
  "name": "submit_feedback",
  "description": "Submit user feedback about Smithery platform or a specific server",
  "inputSchema": {
    "type": "object",
    "properties": {
      "type": {
        "type": "string",
        "enum": ["bug", "feature_request", "general_feedback", "improvement"]
      },
      "title": {
        "type": "string",
        "description": "Feedback title"
      },
      "description": {
        "type": "string",
        "description": "Detailed feedback description"
      },
      "server_id": {
        "type": "number",
        "description": "Optional: related server ID"
      },
      "priority": {
        "type": "string",
        "enum": ["low", "medium", "high"],
        "default": "medium"
      },
      "user_email": {
        "type": "string",
        "description": "Optional: for follow-up"
      }
    },
    "required": ["type", "title", "description"]
  }
}
```

#### create_feature_request
```json
{
  "name": "create_feature_request",
  "description": "Create a new feature request",
  "inputSchema": {
    "type": "object",
    "properties": {
      "title": {
        "type": "string"
      },
      "description": {
        "type": "string"
      },
      "use_case": {
        "type": "string",
        "description": "Why you need this feature"
      },
      "category": {
        "type": "string",
        "enum": ["ui", "api", "search", "analytics", "other"]
      }
    },
    "required": ["title", "description"]
  }
}
```

#### report_bug
```json
{
  "name": "report_bug",
  "description": "Report a bug or issue",
  "inputSchema": {
    "type": "object",
    "properties": {
      "title": {
        "type": "string"
      },
      "description": {
        "type": "string"
      },
      "steps_to_reproduce": {
        "type": "string"
      },
      "expected_behavior": {
        "type": "string"
      },
      "actual_behavior": {
        "type": "string"
      },
      "severity": {
        "type": "string",
        "enum": ["critical", "major", "minor"],
        "default": "minor"
      }
    },
    "required": ["title", "description"]
  }
}
```

#### get_feedback_status
```json
{
  "name": "get_feedback_status",
  "description": "Check the status of submitted feedback",
  "inputSchema": {
    "type": "object",
    "properties": {
      "feedback_id": {
        "type": "string",
        "description": "Feedback tracking ID"
      }
    },
    "required": ["feedback_id"]
  }
}
```

---

### 3. 👤 User Management Tools

#### get_user_profile
```json
{
  "name": "get_user_profile",
  "description": "Get current user's profile information",
  "inputSchema": {
    "type": "object",
    "properties": {}
  }
}
```

#### get_user_favorites
```json
{
  "name": "get_user_favorites",
  "description": "Get user's favorite MCP servers",
  "inputSchema": {
    "type": "object",
    "properties": {}
  }
}
```

#### add_to_favorites
```json
{
  "name": "add_to_favorites",
  "description": "Add a server to user's favorites",
  "inputSchema": {
    "type": "object",
    "properties": {
      "server_id": {
        "type": "number"
      }
    },
    "required": ["server_id"]
  }
}
```

#### get_user_activity
```json
{
  "name": "get_user_activity",
  "description": "Get user's recent activity (views, favorites, comments)",
  "inputSchema": {
    "type": "object",
    "properties": {
      "limit": {
        "type": "number",
        "default": 20
      }
    }
  }
}
```

---

### 4. 📊 Analytics Tools

#### get_top_search_keywords
```json
{
  "name": "get_top_search_keywords",
  "description": "Retrieve the most popular search keywords for a given time period",
  "inputSchema": {
    "type": "object",
    "properties": {
      "limit": {
        "type": "number",
        "description": "Number of keywords to return (1-100)",
        "default": 10
      },
      "days": {
        "type": "number",
        "description": "Number of days to analyze (1-365)",
        "default": 7
      }
    }
  }
}
```

#### get_most_viewed_servers
```json
{
  "name": "get_most_viewed_servers",
  "description": "Get the most viewed MCP servers in a time period",
  "inputSchema": {
    "type": "object",
    "properties": {
      "limit": {
        "type": "number",
        "default": 10
      },
      "days": {
        "type": "number",
        "default": 7
      }
    }
  }
}
```

#### get_trending_servers
```json
{
  "name": "get_trending_servers",
  "description": "Find servers with rapidly growing view counts (trending up)",
  "inputSchema": {
    "type": "object",
    "properties": {
      "limit": {
        "type": "number",
        "default": 10
      },
      "days": {
        "type": "number",
        "description": "Recent period to analyze",
        "default": 7
      },
      "comparison_days": {
        "type": "number",
        "description": "Previous period to compare against",
        "default": 7
      }
    }
  }
}
```

#### get_search_to_view_conversion_rate
```json
{
  "name": "get_search_to_view_conversion_rate",
  "description": "Calculate the conversion rate from searches to server views",
  "inputSchema": {
    "type": "object",
    "properties": {
      "days": {
        "type": "number",
        "default": 7
      }
    }
  }
}
```

#### get_analytics_summary
```json
{
  "name": "get_analytics_summary",
  "description": "Get a comprehensive analytics dashboard summary with all key metrics",
  "inputSchema": {
    "type": "object",
    "properties": {
      "days": {
        "type": "number",
        "default": 7
      }
    }
  }
}
```

---

### 5. 📚 Knowledge Base Tools

#### search_documentation
```json
{
  "name": "search_documentation",
  "description": "Search Smithery documentation and guides",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string"
      },
      "category": {
        "type": "string",
        "enum": ["getting_started", "api", "mcp", "troubleshooting", "all"],
        "default": "all"
      }
    },
    "required": ["query"]
  }
}
```

#### get_faq_answer
```json
{
  "name": "get_faq_answer",
  "description": "Get answer to frequently asked questions",
  "inputSchema": {
    "type": "object",
    "properties": {
      "question": {
        "type": "string"
      }
    },
    "required": ["question"]
  }
}
```

#### get_getting_started_guide
```json
{
  "name": "get_getting_started_guide",
  "description": "Get getting started guide for using Smithery",
  "inputSchema": {
    "type": "object",
    "properties": {
      "topic": {
        "type": "string",
        "enum": ["overview", "first_server", "mcp_basics", "api_usage"],
        "default": "overview"
      }
    }
  }
}
```

---

## 💬 사용 시나리오

### 시나리오 1: 서버 찾기
```
User: "날씨 관련 MCP 서버 있어?"

Agent: [calls search_servers(query="날씨")]
Agent: "네! 날씨 관련 서버 3개를 찾았습니다:

       1. **Weather API Server** (#42)
          - OpenWeatherMap 통합
          - 전세계 날씨 정보 조회
          - ⭐ 인기도: 4.8/5.0

       2. **Climate Data Server** (#18)
          ...

       어떤 서버에 대해 더 알고 싶으신가요?"

User: "42번 자세히 보여줘"

Agent: [calls get_server_details(server_id=42)]
Agent: [상세 정보 표시]
```

### 시나리오 2: VOC 수집
```
User: "검색 기능이 좀 불편한데, 태그로도 검색할 수 있게 해주면 좋겠어"

Agent: [calls create_feature_request(
  title="태그 기반 검색 기능 추가",
  description="사용자가 태그로도 검색할 수 있으면 좋겠습니다",
  use_case="키워드 검색보다 태그 검색이 더 정확할 때가 있음",
  category="search"
)]

Agent: "피드백 감사합니다! 기능 요청이 등록되었습니다.
       추적 번호: #FR-2025-001

       현재 개발팀이 검토 중이며, 진행 상황은
       get_feedback_status('FR-2025-001')로 확인하실 수 있습니다."
```

### 시나리오 3: 버그 리포트
```
User: "서버 상세 페이지에서 즐겨찾기 버튼이 안 눌려"

Agent: "불편을 드려 죄송합니다. 버그 리포트를 작성해드릴게요.
       몇 가지 정보를 더 알려주시겠어요?

       1. 어떤 브라우저를 사용하고 계신가요?
       2. 어떤 서버 페이지에서 발생했나요?
       3. 에러 메시지가 있었나요?"

User: "크롬이고, 날씨 서버 페이지에서, 에러 메시지는 없었어"

Agent: [calls report_bug(
  title="즐겨찾기 버튼 동작 안 함 (크롬, 서버 #42)",
  description="...",
  steps_to_reproduce="1. 서버 #42 상세 페이지 접속\n2. 즐겨찾기 버튼 클릭\n3. 반응 없음",
  expected_behavior="즐겨찾기 추가됨",
  actual_behavior="버튼 클릭해도 반응 없음",
  severity="minor"
)]

Agent: "버그 리포트가 등록되었습니다. (Bug #BUG-2025-042)
       개발팀이 빠르게 수정하겠습니다!"
```

### 시나리오 4: Analytics 질문
```
User: "요즘 어떤 서버가 인기야?"

Agent: [calls get_trending_servers(limit=5, days=7)]
Agent: "이번 주 급상승 중인 서버 Top 5:

       1. 🔥 Weather API Server (#42) - 520% 증가
       2. 🔥 Finance Data Server (#18) - 410% 증가
       ..."
```

### 시나리오 5: 도움말
```
User: "MCP 서버 어떻게 사용하는 거야?"

Agent: [calls get_getting_started_guide(topic="mcp_basics")]
Agent: "MCP 서버 사용법을 알려드릴게요:

       1. **Claude Desktop 설치**
          ...

       2. **서버 추가**
          ...

       더 자세한 내용은 [MCP 가이드]를 참고하세요!"
```

---

## 🏗️ 프로젝트 구조

```
smithery-agent/
├── backend/
│   ├── mcp_server/                    # MCP Server (Tools 제공)
│   │   ├── __init__.py
│   │   ├── server.py                  # Main MCP server
│   │   ├── tools/
│   │   │   ├── search_tools.py        # 검색 관련 tools
│   │   │   ├── voc_tools.py           # VOC/피드백 tools
│   │   │   ├── analytics_tools.py     # Analytics tools
│   │   │   ├── user_tools.py          # 사용자 관리 tools
│   │   │   └── knowledge_tools.py     # 문서/FAQ tools
│   │   ├── api_client.py              # Smithery API client
│   │   └── config.py
│   │
│   ├── agent_service/                 # Agent Core (Claude + ADK)
│   │   ├── __init__.py
│   │   ├── agent.py                   # Agent 핵심 로직
│   │   ├── prompts.py                 # System prompts
│   │   └── conversation_manager.py    # 대화 상태 관리
│   │
│   ├── api/                           # REST API (웹/앱에서 호출)
│   │   ├── __init__.py
│   │   ├── chat_api.py                # POST /chat 엔드포인트
│   │   └── webhook_api.py             # Slack/Discord webhooks
│   │
│   └── database/
│       ├── models/
│       │   ├── feedback.py            # VOC 데이터 모델
│       │   ├── conversation.py        # 대화 기록
│       │   └── knowledge_base.py      # FAQ/문서
│       └── dao/
│           ├── feedback_dao.py
│           └── conversation_dao.py
│
├── frontend/
│   └── components/
│       └── chat-widget.tsx            # 웹사이트 채팅 위젯
│
├── integrations/                      # 다른 플랫폼 통합
│   ├── slack_bot.py
│   ├── discord_bot.py
│   └── telegram_bot.py
│
├── docs/
│   ├── knowledge_base/                # Agent가 참조할 문서
│   │   ├── faq.json
│   │   ├── getting_started.md
│   │   └── troubleshooting.md
│   └── api_docs.md
│
├── tests/
│   ├── test_mcp_tools.py
│   ├── test_agent.py
│   └── test_integrations.py
│
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## 🚀 배포 방식

### 1. MCP Server (Claude Desktop 등에서 사용)
```json
// ~/.config/claude/config.json
{
  "mcpServers": {
    "smithery-assistant": {
      "command": "python",
      "args": ["-m", "smithery_agent.mcp_server"],
      "env": {
        "SMITHERY_API_URL": "https://smithery.com/api/v1",
        "SMITHERY_API_KEY": "your_key"
      }
    }
  }
}
```

### 2. Web Chat Widget (웹사이트)
```tsx
// Frontend에서 사용
<SmitheryChat apiEndpoint="/api/chat" />
```

### 3. Slack Bot
```python
# Slack에서 사용
@app.event("message")
async def handle_message(event, say):
    response = await agent.chat(event["text"], user_id=event["user"])
    await say(response)
```

### 4. REST API (어디서든 호출 가능)
```bash
curl -X POST https://smithery.com/api/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message": "인기 서버 보여줘", "user_id": "user123"}'
```

---

## 📝 구현 우선순위

### Phase 1: Core (필수)
1. MCP Server 기본 구조
2. Search & Browse Tools (가장 자주 쓰일 기능)
3. Basic Agent (system prompt + tool calling)
4. REST API endpoint (`POST /api/chat`)

### Phase 2: VOC System
5. VOC Tools (feedback, bug report, feature request)
6. VOC 데이터베이스 모델
7. Admin dashboard (VOC 확인용)

### Phase 3: Analytics & Knowledge
8. Analytics Tools
9. Knowledge Base Tools
10. FAQ 데이터베이스

### Phase 4: Multi-Channel
11. Web Chat Widget
12. Slack Bot
13. Discord Bot

---

## 🔑 핵심 개념

### Agent vs MCP Tools

| 구성 요소 | 역할 | 비유 |
|---------|------|------|
| **Agent (Claude)** | 자연어 이해, 의도 파악, tool 선택 | 건축가 (설계) |
| **MCP Tools** | 실제 작업 수행 (API 호출, 계산 등) | 도구 (망치, 톱) |
| **MCP Server** | Tools를 제공하는 서버 | 도구 상자 |
| **Backend API** | 실제 데이터 소스 | 재료 창고 |

### 데이터 흐름

```
User Question
    ↓
Agent (자연어 이해, tool 선택)
    ↓
MCP Tool Call
    ↓
MCP Server (API 호출)
    ↓
Smithery Backend API
    ↓
Database (TimescaleDB, PostgreSQL)
    ↓
Response ← ← ← ← ←
    ↓
Agent (결과 해석)
    ↓
Natural Language Response
    ↓
User
```

---

## 💡 추가 아이디어

### 데이터 시각화
- ASCII charts로 트렌드 표시
- 간단한 그래프 생성

### Alert System
- 이상치 탐지 (급격한 변화)
- 자동 알림 생성

### Custom Reports
- 주간/월간 리포트 자동 생성
- Markdown/JSON 형식 지원

### AI-Powered Features
- 트렌드 예측 (simple regression)
- 추천 시스템 (비슷한 서버 추천)
- 자동 인사이트 생성

---

## 📚 참고 자료

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [Claude Agent SDK](https://github.com/anthropics/claude-code)
- Smithery 기존 Analytics 시스템 (`backend/service/analytics_service.py`)
- Smithery API 문서 (`CLAUDE.md`)
