# Prompt-Based Tool Calling for Non-OpenAI Models

## 문제 상황

### 현재 상태
- `deepseek-v3-0324`: OpenAI Function/Tool Calling 형식 지원 ✅
- `gpt-oss-40`: OpenAI Function/Tool Calling 형식 미지원 ❌
  - 에러: `Error code: 400/422 - BadRequestError`
  - `tools` 파라미터를 포함한 요청이 거부됨

### 발견 과정
1. `test_llm_connection.py`로 테스트 시 두 모델 모두 정상 작동
   - 단순 메시지만 보내면 성공
2. Playground에서 `gpt-oss-40` 사용 시 에러 발생
   - MCP 도구와 함께 요청하면 실패

### 핵심 이슈
- **MCP 서버 사용 불가능한 것이 아님**
- **OpenAI의 Tool Calling API 형식**을 지원하지 않는 것

```python
# 이 형식을 지원하지 않음
client.chat.completions.create(
    model="gpt-oss-40",
    messages=[...],
    tools=[{"type": "function", "function": {...}}],  # ❌ 422 에러
    tool_choice="auto"
)
```

## 해결 방안: Prompt-Based Tool Calling

### 개념
OpenAI Tool Calling API 대신, **프롬프트에 도구 정보를 텍스트로 포함**하여 LLM이 도구를 사용하도록 유도

### 비교

#### Native OpenAI Tool Calling (deepseek, gpt-4 등)
```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_doc",
            "description": "Search documentation",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    }
]

response = client.chat.completions.create(
    model="deepseek-v3",
    messages=[{"role": "user", "content": "How do I use the API?"}],
    tools=tools,
    tool_choice="auto"
)

# LLM이 자동으로 tool_calls 반환
if response.choices[0].message.tool_calls:
    # 도구 실행
    ...
```

#### Prompt-Based Tool Calling (gpt-oss-40 등)
```python
# 도구 정보를 텍스트로 프롬프트에 포함
system_prompt = """
You are a helpful assistant with access to tools via MCP (Model Context Protocol).

Available Tools:

search_doc:
  Description: Search documentation
  Parameters:
    - query (string): Search query

IMPORTANT: When you need to use a tool, respond with ONLY a JSON object in this exact format:
{"tool_name": "search_doc", "arguments": {"query": "your search query"}}

After I execute the tool and give you the result, provide your final answer based on that result.
If you don't need a tool, just answer the question directly.
"""

response = client.chat.completions.create(
    model="gpt-oss-40",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "How do I use the API?"}
    ]
    # tools 파라미터 없음 ✅
)

# 응답 파싱
content = response.choices[0].message.content
try:
    parsed = json.loads(content)
    if "tool_name" in parsed and "arguments" in parsed:
        # 도구 실행
        tool_name = parsed["tool_name"]
        args = parsed["arguments"]
        result = execute_mcp_tool(tool_name, args)

        # 결과를 다시 LLM에게 전달
        final_response = client.chat.completions.create(
            model="gpt-oss-40",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "How do I use the API?"},
                {"role": "assistant", "content": content},
                {"role": "user", "content": f"Tool result: {result}"}
            ]
        )
except json.JSONDecodeError:
    # JSON이 아니면 직접 답변한 것
    final_answer = content
```

## 구현 계획

### 1. 모델 호환성 체크
```python
class PlaygroundService:
    @staticmethod
    def _model_supports_native_tools(model: str) -> bool:
        """Check if model supports OpenAI native tool calling"""
        # 환경 변수로 설정 가능
        disabled_models = os.getenv("DISABLE_NATIVE_TOOLS_FOR_MODELS", "")
        if disabled_models:
            disabled_list = [m.strip() for m in disabled_models.split(",")]
            return model not in disabled_list
        return True
```

### 2. 도구 설명 생성 (텍스트 형식)
```python
@staticmethod
def _generate_tools_prompt(tools: List[Dict]) -> str:
    """Generate text description of tools for prompt"""
    tools_text = "Available Tools:\n\n"
    for tool in tools:
        func = tool.get("function", {})
        name = func.get("name")
        desc = func.get("description", "")
        params = func.get("parameters", {}).get("properties", {})

        tools_text += f"{name}:\n"
        tools_text += f"  Description: {desc}\n"
        if params:
            tools_text += f"  Parameters:\n"
            for param_name, param_info in params.items():
                param_type = param_info.get("type", "any")
                param_desc = param_info.get("description", "")
                tools_text += f"    - {param_name} ({param_type}): {param_desc}\n"
        tools_text += "\n"

    return tools_text
```

### 3. 시스템 프롬프트 분기
```python
async def _chat_internal(...):
    tools = await self.get_mcp_tools(mcp_server_url, protocol)
    use_native = self._model_supports_native_tools(self.model)

    if use_native:
        # OpenAI Tool Calling 사용
        system_prompt = "You are a helpful assistant with access to tools..."
        api_tools = tools
    else:
        # Prompt-based 사용
        tools_description = self._generate_tools_prompt(tools)
        system_prompt = f"""
You are a helpful assistant with access to tools via MCP.

{tools_description}

When you need to use a tool, respond with JSON:
{{"tool_name": "function_name", "arguments": {{"arg": "value"}}}}
"""
        api_tools = None  # API에 tools 파라미터 전달 안 함
```

### 4. 응답 파싱
```python
# LLM 응답 받은 후
if use_native:
    # Native tool calls 처리
    if response.choices[0].message.tool_calls:
        for tool_call in response.choices[0].message.tool_calls:
            # 기존 로직
            ...
else:
    # Prompt-based tool call 파싱
    content = response.choices[0].message.content
    try:
        parsed = json.loads(content.strip())
        if "tool_name" in parsed and "arguments" in parsed:
            # 도구 실행
            tool_name = parsed["tool_name"]
            arguments = parsed["arguments"]
            result = await self.call_mcp_tool(...)

            # 결과를 메시지에 추가
            messages.append({
                "role": "assistant",
                "content": content
            })
            messages.append({
                "role": "user",
                "content": f"Tool execution result:\n{result}"
            })

            # 최종 답변 생성
            final_response = await self.client.chat.completions.create(...)
    except json.JSONDecodeError:
        # JSON이 아니면 직접 답변
        final_answer = content
```

## 환경 변수 설정

```bash
# .env 파일

# 방법 1: Native tool calling 비활성화할 모델 지정
DISABLE_NATIVE_TOOLS_FOR_MODELS=gpt-oss-40,other-model

# 방법 2: 빈 값 = 모든 모델 native tool calling 시도
# (실패 시 자동 retry로 처리)
DISABLE_NATIVE_TOOLS_FOR_MODELS=
```

## 장단점

### Native OpenAI Tool Calling
**장점:**
- LLM이 자동으로 도구 선택
- 응답 형식이 표준화됨
- 에러 처리가 깔끔함

**단점:**
- 모델이 지원해야 함
- 특정 API 형식에 종속

### Prompt-Based Tool Calling
**장점:**
- 모든 LLM에서 작동 가능
- API 형식에 독립적
- 커스터마이징 가능

**단점:**
- LLM이 JSON 형식을 정확히 따라야 함
- 파싱 에러 가능성
- 프롬프트가 복잡해짐

## 테스트 계획

### 1. Native Tool Calling (deepseek-v3)
```bash
OPENAI_MODEL=deepseek-v3-0324
# Playground에서 MCP 도구 사용 테스트
```

### 2. Prompt-Based Tool Calling (gpt-oss-40)
```bash
OPENAI_MODEL=gpt-oss-40
DISABLE_NATIVE_TOOLS_FOR_MODELS=gpt-oss-40
# Playground에서 같은 질문으로 테스트
# 로그에서 "Prompt-based tool call detected" 확인
```

### 3. Fallback 테스트
```bash
OPENAI_MODEL=gpt-oss-40
# DISABLE_NATIVE_TOOLS_FOR_MODELS 설정 안 함
# 첫 요청 실패 → 자동 retry 확인
```

## 참고사항

- 이 방식은 **LLM의 instruction following 능력**에 의존
- GPT-4, Claude, Deepseek 등 성능 좋은 모델에서 잘 작동
- 작은 모델은 JSON 형식을 정확히 따르지 못할 수 있음
- Few-shot 예시를 프롬프트에 추가하면 성공률 향상

## 다음 단계

1. ✅ 문제 파악 및 해결 방안 설계
2. ⏳ Prompt-based tool calling 구현
3. ⏳ 테스트 및 검증
4. ⏳ 별도 PR로 머지

---

## 관련 커밋

현재 `feature/uvicorn-stability-improvements` 브랜치에는 다음 개선사항만 포함:
- Connection leak 수정
- Timeout 최적화
- 에러 로깅 강화
- 기본 fallback (400/422 에러 시 retry)

Prompt-based tool calling은 별도 PR에서 구현 예정.
