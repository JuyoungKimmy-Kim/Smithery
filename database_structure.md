PostreSQL, sqlalchemy 방식으로 구현

class MCPServer
    id = integer, primary key, auto increment 
    name = string (사용자 입력)
    github link = string (사용자 입력)
    description = string (사용자 입력)
    tool = 아래 MCP Server Tool 과 연결 (git clone을 통해 tools list를 찾아냄)
    category = string (사용자 입력력)
    tags = list (콤마로 사용자에게 여러개 입력 받고, list로 저장) (Optional)
    status = string ()
    config = json (Optional) (사용자 입력)
    created at = DateTime (처음 생성시 자동 생성)
    update at = DateTimea (업데이트시 자동 생성)
    
class MCPServerTool
    name = string
    description = string (Optional)
    parameter = 아래 MCPServerProperty 와 연결결

class MCPServerProperty
    name = string
    description = string (Optional)

MCPServer : MCPServerTool = 1:N
MCPServerTool : MCPServerProperty = 1:N 

