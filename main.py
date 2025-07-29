from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from backend.database.dao.mcp_server_dao import MCPServerDAO
from backend.database.model.mcp_server import MCPServer, MCPServerTool, MCPServerResource, TransportType
from typing import List
import uvicorn

app = FastAPI(title="DS Smithery API", version="1.0.0")

# 데이터베이스 연결
def get_dao():
    dao = MCPServerDAO("mcp_market.db")
    dao.connect()
    dao.create_table()
    return dao

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

@app.get("/api/posts")
def get_posts():
    """블로그 포스트 목록 (UI용)"""
    try:
        dao = get_dao()
        mcps = dao.get_all_mcps()
        dao.close()
        
        # 기본 아바타 배열
        default_avatars = [
            '/image/avatar1.jpg',
            '/image/avatar2.jpg',
            '/image/avatar3.jpg',
        ]
        
        # 기본 작성자 배열
        default_authors = [
            'Ryan Samuel',
            'Nora Hazel',
            'Otto Gonzalez',
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
    uvicorn.run(app, host="0.0.0.0", port=8080) 