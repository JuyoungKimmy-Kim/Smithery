export const MCP_CATEGORIES = [
  "Code Tools",
  "Documentation", 
  "Data & Search",
  "Automation",
  "DevOps",
  "Miscellaneous"
] as const;

export type MCPCategory = typeof MCP_CATEGORIES[number]; 