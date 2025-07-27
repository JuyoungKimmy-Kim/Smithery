from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
from backend.database.dao.mcp_server_dao import MCPServerDAO

app = FastAPI()
# 정적 파일(css, js, assets) 서빙
app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
app.mount("/js", StaticFiles(directory="frontend/js"), name="js")
app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets")
# index.html은 frontend/에서, detail.html 등은 frontend/templates/에서 렌더링
index_templates = Jinja2Templates(directory="frontend")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    dao = MCPServerDAO("mcp_market.db")
    dao.connect()
    dao.create_table()
    mcps = dao.get_all_mcps()
    dao.close()
    return index_templates.TemplateResponse("index.html", {"request": request, "mcps": mcps})

@app.get("/mcp/{mcp_id}", response_class=HTMLResponse)
def mcp_detail(request: Request, mcp_id: str):
    dao = MCPServerDAO("mcp_market.db")
    dao.connect()
    dao.create_table()
    mcp = dao.get_mcp(mcp_id)
    dao.close()
    return detail_templates.TemplateResponse("detail.html", {"request": request, "mcp": mcp})

@app.get("/api/mcps")
def api_mcps():
    dao = MCPServerDAO("mcp_market.db")
    dao.connect()
    dao.create_table()
    mcps = dao.get_all_mcps()
    dao.close()
    return JSONResponse(content=jsonable_encoder(mcps))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

