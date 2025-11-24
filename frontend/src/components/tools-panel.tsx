"use client";

import React from 'react';
import ToolCard, { Tool } from './ui/tool-card';
import { apiFetch } from '@/lib/api-client';

interface ToolsPanelProps {
  tools: any[]; // Accept raw tool data from backend
  serverId: number;
}

// Convert backend tool format to frontend format
function convertToolFormat(tool: any): Tool {
  // If inputSchema already exists, use it
  if (tool.inputSchema) {
    return {
      name: tool.name,
      description: tool.description || '',
      inputSchema: tool.inputSchema,
    };
  }

  // Otherwise, convert from parameters array
  const properties: Record<string, any> = {};
  const required: string[] = [];

  if (tool.parameters && Array.isArray(tool.parameters)) {
    tool.parameters.forEach((param: any) => {
      properties[param.name] = {
        type: param.type || 'string',
        description: param.description,
      };
      if (param.required) {
        required.push(param.name);
      }
    });
  }

  return {
    name: tool.name,
    description: tool.description || '',
    inputSchema: {
      type: 'object',
      properties,
      required: required.length > 0 ? required : undefined,
    },
  };
}

const ToolsPanel = ({ tools, serverId }: ToolsPanelProps) => {
  // Convert tools to proper format
  const convertedTools = tools.map(convertToolFormat);
  const handleExecuteTool = async (toolName: string, arguments_: Record<string, any>) => {
    try {
      const response = await apiFetch(`/api/mcp-servers/${serverId}/tools/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tool_name: toolName,
          arguments: arguments_,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        return data;
      } else {
        const errorData = await response.json();
        return {
          success: false,
          error: errorData.detail || errorData.error || 'Failed to execute tool',
        };
      }
    } catch (error) {
      console.error('Tool execution error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      };
    }
  };

  if (!convertedTools || convertedTools.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-8 text-center">
        <p className="text-gray-600">No tools available for this server.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          🔧 Direct Tool Testing
        </h2>
        <p className="text-gray-600">
          Test each tool directly by providing parameters and viewing results. No LLM involved - pure tool execution.
        </p>
      </div>

      <div className="space-y-3">
        {convertedTools.map((tool) => (
          <ToolCard
            key={tool.name}
            tool={tool}
            serverId={serverId}
            onExecute={handleExecuteTool}
          />
        ))}
      </div>
    </div>
  );
};

export default ToolsPanel;
