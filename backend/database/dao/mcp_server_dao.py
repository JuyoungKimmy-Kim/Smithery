from backend.database.database import Database
from backend.database.model.mcp_server import (
    MCPServer,
    MCPServerTool,
    MCPServerResource,
    MCPServerProperty,
    TransportType,
)
from typing import List, Optional
import json


class MCPServerDAO(Database):
    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS mcp_server (
            id TEXT PRIMARY KEY,
            github_link TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            transport,
            category TEXT NOT NULL,
            tags TEXT,
            status TEXT,
            tools TEXT,
            resources TEXT,
            config TEXT,
            created_at TEXT,
            updated_at TEXT
        );
        """
        self.conn.execute(query)
        self.conn.commit()

    def _serialize_tools(self, tools: List[MCPServerTool]) -> str:
        """MCPServerTool 리스트를 JSON 문자열로 직렬화"""
        if not tools:
            return None
        tools_data = []
        for tool in tools:
            tool_data = {
                "name": tool.name,
                "description": tool.description,
                "input_properties": [
                    {
                        "name": prop.name,
                        "description": prop.description,
                        "required": prop.required,
                    }
                    for prop in tool.input_properties
                ],
            }
            tools_data.append(tool_data)
        return json.dumps(tools_data)

    def _deserialize_tools(self, tools_json: str) -> List[MCPServerTool]:
        """JSON 문자열을 MCPServerTool 리스트로 역직렬화"""
        if not tools_json:
            return []
        tools_data = json.loads(tools_json)
        tools = []
        for tool_data in tools_data:
            input_properties = [
                MCPServerProperty(
                    name=prop["name"],
                    description=prop.get("description"),
                    required=prop["required"],
                )
                for prop in tool_data["input_properties"]
            ]
            tool = MCPServerTool(
                name=tool_data["name"],
                description=tool_data["description"],
                input_properties=input_properties,
            )
            tools.append(tool)
        return tools

    def _serialize_resources(self, resources: List[MCPServerResource]) -> str:
        """MCPServerResource 리스트를 JSON 문자열로 직렬화"""
        if not resources:
            return None
        resources_data = [
            {
                "name": resource.name,
                "description": resource.description,
                "url": resource.url,
            }
            for resource in resources
        ]
        return json.dumps(resources_data)

    def _deserialize_resources(self, resources_json: str) -> List[MCPServerResource]:
        """JSON 문자열을 MCPServerResource 리스트로 역직렬화"""
        if not resources_json:
            return []
        resources_data = json.loads(resources_json)
        resources = []
        for resource_data in resources_data:
            resource = MCPServerResource(
                name=resource_data["name"],
                description=resource_data["description"],
                url=resource_data["url"],
            )
            resources.append(resource)
        return resources

    def create_mcp(self, mcp: MCPServer):
        query = """
        INSERT INTO mcp_server (id, github_link, name, description, transport, category, tags, status, tools, resources, config, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(
            query,
            (
                mcp.id,
                mcp.github_link,
                mcp.name,
                mcp.description,
                (
                    mcp.transport.value
                    if isinstance(mcp.transport, TransportType)
                    else mcp.transport
                ),
                mcp.category,
                json.dumps(mcp.tags) if mcp.tags else None,
                mcp.status,
                self._serialize_tools(mcp.tools),
                self._serialize_resources(mcp.resources),
                (
                    json.dumps(mcp.config)
                    if hasattr(mcp, "config") and mcp.config is not None
                    else None
                ),
                mcp.created_at,
                mcp.updated_at,
            ),
        )
        self.conn.commit()

    def get_mcp(self, mcp_id: str) -> Optional[MCPServer]:
        query = "SELECT * FROM mcp_server WHERE id = ?"
        cur = self.conn.execute(query, (mcp_id,))
        row = cur.fetchone()
        if row:
            data = dict(row)
            data["tags"] = json.loads(data["tags"]) if data["tags"] else []
            data["tools"] = self._deserialize_tools(data["tools"])
            data["resources"] = self._deserialize_resources(data["resources"])
            data["config"] = json.loads(data["config"]) if data.get("config") else None
            # transport를 enum으로 변환
            if data["transport"]:
                data["transport"] = TransportType(data["transport"])
            return MCPServer(**data)
        return None

    def get_all_mcps(self) -> List[MCPServer]:
        query = "SELECT * FROM mcp_server"
        cur = self.conn.execute(query)
        rows = cur.fetchall()
        result = []
        for row in rows:
            data = dict(row)
            data["tags"] = json.loads(data["tags"]) if data["tags"] else []
            data["tools"] = self._deserialize_tools(data["tools"])
            data["resources"] = self._deserialize_resources(data["resources"])
            data["config"] = json.loads(data["config"]) if data.get("config") else None
            # transport를 enum으로 변환
            if data["transport"]:
                data["transport"] = TransportType(data["transport"])
            result.append(MCPServer(**data))
        return result

    def update_mcp(self, mcp_id: str, **kwargs):
        if "tags" in kwargs:
            kwargs["tags"] = json.dumps(kwargs["tags"])
        if "tools" in kwargs:
            kwargs["tools"] = self._serialize_tools(kwargs["tools"])
        if "resources" in kwargs:
            kwargs["resources"] = self._serialize_resources(kwargs["resources"])
        if "config" in kwargs:
            kwargs["config"] = json.dumps(kwargs["config"])
        if "transport" in kwargs:
            transport = kwargs["transport"]
            kwargs["transport"] = (
                transport.value if isinstance(transport, TransportType) else transport
            )
        fields = ", ".join([f"{k} = ?" for k in kwargs])
        values = list(kwargs.values())
        values.append(mcp_id)
        query = f"UPDATE mcp_server SET {fields} WHERE id = ?"
        self.conn.execute(query, values)
        self.conn.commit()

    def delete_mcp(self, mcp_id: str):
        query = "DELETE FROM mcp_server WHERE id = ?"
        self.conn.execute(query, (mcp_id,))
        self.conn.commit()
