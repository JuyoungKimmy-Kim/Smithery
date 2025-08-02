from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from backend.database.dao.mcp_server_dao import MCPServerDAO
from backend.database.model.mcp_server import (
    MCPServer,
    MCPServerTool,
    MCPServerResource,
    TransportType,
)
from backend.service.mcp_server_service import MCPServerService
from typing import List
import uvicorn

app = FastAPI(title="DS Smithery API", version="1.0.0")


# 데이터베이스 연결
def get_dao():
    dao = MCPServerDAO("mcp_market.db")
    dao.connect()
    dao.create_table()
    return dao


# MCP 서버 서비스 인스턴스 생성
def get_mcp_service():
    import os
    from dotenv import load_dotenv

    load_dotenv()

    github_token = os.getenv("GITHUB_TOKEN")
    return MCPServerService(github_token)


@app.get("/api/mcps", response_model=List[dict])
def get_all_mcps():
    """모든 MCP 서버 목록 조회"""
    try:
        dao = get_dao()
        mcps = dao.get_all_mcps()
        dao.close()
        return jsonable_encoder(mcps)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/mcps/{mcp_id}", response_model=dict)
def get_mcp(mcp_id: str):
    """특정 MCP 서버 조회"""
    try:
        dao = get_dao()
        mcp = dao.get_mcp(mcp_id)
        dao.close()
        if not mcp:
            raise HTTPException(status_code=404, detail="MCP server not found")
        return jsonable_encoder(mcp)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/mcps", response_model=dict)
def create_mcp(mcp: MCPServer):
    """새로운 MCP 서버 생성"""
    try:
        dao = get_dao()
        mcp_service = get_mcp_service()

        # GitHub 링크에서 tools 정보 자동 추출 (항상 추출)
        if mcp.github_link:
            print(f"GitHub 링크에서 tools 정보 추출 중: {mcp.github_link}")
            extracted_tools = mcp_service.read_mcp_server_tool_list(mcp.github_link)
            print(f"추출된 tools 데이터: {extracted_tools[:3]}...")  # 처음 3개만 로그

            if extracted_tools:
                # 추출된 tools를 MCPServerTool 형식으로 변환
                mcp.tools = []
                for tool_data in extracted_tools:
                    tool = MCPServerTool(
                        name=tool_data.get("name", ""),
                        description=tool_data.get("description", ""),
                        input_properties=[],
                    )
                    mcp.tools.append(tool)
                print(f"변환된 tools 개수: {len(mcp.tools)}")
                print(f"첫 번째 tool: {mcp.tools[0].name if mcp.tools else 'None'}")
            else:
                print("tools 정보를 추출할 수 없습니다.")
        else:
            print(
                f"Tools 추출 조건 확인: github_link={bool(mcp.github_link)}, tools_empty={not mcp.tools}"
            )

        # GitHub 링크에서 resources 정보 자동 추출 (항상 추출)
        if mcp.github_link:
            print(f"GitHub 링크에서 resources 정보 추출 중: {mcp.github_link}")
            extracted_resources = mcp_service.read_mcp_server_resource_list(
                mcp.github_link
            )

            if extracted_resources:
                # 추출된 resources를 MCPServerResource 형식으로 변환
                mcp.resources = []
                for resource_data in extracted_resources:
                    resource = MCPServerResource(
                        name=resource_data.get("name", ""),
                        description=resource_data.get("description", ""),
                        url=resource_data.get("url", ""),
                    )
                    mcp.resources.append(resource)
                print(f"추출된 resources 개수: {len(mcp.resources)}")
            else:
                print("resources 정보를 추출할 수 없습니다.")

        dao.create_mcp(mcp)
        dao.close()
        return {"message": "MCP server created successfully", "id": mcp.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/mcps/{mcp_id}", response_model=dict)
def update_mcp(mcp_id: str, mcp_update: dict):
    """MCP 서버 정보 수정"""
    try:
        dao = get_dao()
        dao.update_mcp(mcp_id, **mcp_update)
        dao.close()
        return {"message": "MCP server updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/mcps/{mcp_id}", response_model=dict)
def delete_mcp(mcp_id: str):
    """MCP 서버 삭제"""
    try:
        dao = get_dao()
        dao.delete_mcp(mcp_id)
        dao.close()
        return {"message": "MCP server deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/mcps/preview", response_model=dict)
def preview_mcp_server(github_link: dict):
    """GitHub 링크에서 tools와 resources 정보 미리보기"""
    try:
        mcp_service = get_mcp_service()
        github_url = github_link.get("github_link", "")

        if not github_url:
            raise HTTPException(status_code=400, detail="GitHub link is required")

        # tools 정보 추출
        tools = mcp_service.read_mcp_server_tool_list(github_url)

        # resources 정보 추출
        resources = mcp_service.read_mcp_server_resource_list(github_url)

        return {"tools": tools, "resources": resources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/posts")
def get_posts():
    """블로그 포스트 목록 (UI용)"""
    try:
        dao = get_dao()
        mcps = dao.get_all_mcps()
        dao.close()

        # 기본 아바타 배열
        default_avatars = [
            "/image/avatar1.jpg",
            "/image/avatar2.jpg",
            "/image/avatar3.jpg",
        ]

        # 기본 작성자 배열
        default_authors = [
            "Ryan Samuel",
            "Nora Hazel",
            "Otto Gonzalez",
        ]

        posts = []
        for i, mcp in enumerate(mcps):
            post = {
                "id": mcp.id,  # MCP 서버 ID 추가
                "category": mcp.category or "Unknown",
                "tags": str(mcp.tags) if mcp.tags else "[]",
                "title": mcp.name,
                "desc": mcp.description or "No description available.",
                "date": mcp.created_at or "Unknown date",
                "author": {
                    "img": default_avatars[i % len(default_avatars)],
                    "name": default_authors[i % len(default_authors)],
                },
            }
            posts.append(post)

        return posts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
