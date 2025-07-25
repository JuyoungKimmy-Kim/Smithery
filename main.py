from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder
from backend.database.dao.mcp_server_dao import MCPServerDAO

app = FastAPI()
templates = Jinja2Templates(directory="frontend/templates")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    dao = MCPServerDAO("mcp_market.db")
    dao.connect()
    dao.create_table()
    mcps = dao.get_all_mcps()
    dao.close()
    return templates.TemplateResponse("index.html", {"request": request, "mcps": mcps})

@app.get("/mcp/{mcp_id}", response_class=HTMLResponse)
def mcp_detail(request: Request, mcp_id: str):
    dao = MCPServerDAO("mcp_market.db")
    dao.connect()
    dao.create_table()
    mcp = dao.get_mcp(mcp_id)
    dao.close()
    return templates.TemplateResponse("detail.html", {"request": request, "mcp": mcp})

@app.get("/api/mcps")
def api_mcps():
    dao = MCPServerDAO("mcp_market.db")
    dao.connect()
    dao.create_table()
    mcps = dao.get_all_mcps()
    dao.close()
    return JSONResponse(content=jsonable_encoder(mcps))

