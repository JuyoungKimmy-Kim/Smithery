export const MCP_CATEGORIES = [
  "Code Tools",
  "Documentation", 
  "Data",
  "Automation",
  "DevOps",
  "Miscellaneous"
] as const;

export type MCPCategory = typeof MCP_CATEGORIES[number]; 