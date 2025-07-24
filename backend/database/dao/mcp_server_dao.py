from backend.database.database import Database
from backend.database.model.mcp_server import MCPServer
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
            transport TEXT NOT NULL,
            category TEXT,
            tags TEXT,
            status TEXT,
            tools TEXT,
            resources TEXT,
            created_at TEXT,
            updated_at TEXT
        );
        """
        self.conn.execute(query)
        self.conn.commit()

    def create_mcp(self, mcp: MCPServer):
        query = """
        INSERT INTO mcp_server (id, github_link, name, description, transport, category, tags, status, tools, resources, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    if hasattr(mcp.transport, "value")
                    else mcp.transport
                ),
                mcp.category,
                json.dumps(mcp.tags) if mcp.tags else None,
                mcp.status,
                json.dumps(mcp.tools) if hasattr(mcp, "tools") and mcp.tools else None,
                (
                    json.dumps(mcp.resources)
                    if hasattr(mcp, "resources") and mcp.resources
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
            data["tools"] = json.loads(data["tools"]) if data["tools"] else []
            data["resources"] = (
                json.loads(data["resources"]) if data["resources"] else []
            )
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
            data["tools"] = json.loads(data["tools"]) if data["tools"] else []
            data["resources"] = (
                json.loads(data["resources"]) if data["resources"] else []
            )
            result.append(MCPServer(**data))
        return result

    def update_mcp(self, mcp_id: str, **kwargs):
        if "tags" in kwargs:
            kwargs["tags"] = json.dumps(kwargs["tags"])
        if "tools" in kwargs:
            kwargs["tools"] = json.dumps(kwargs["tools"])
        if "resources" in kwargs:
            kwargs["resources"] = json.dumps(kwargs["resources"])
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
