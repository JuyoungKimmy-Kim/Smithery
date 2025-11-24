"use client";

import { useState, useCallback } from 'react';
import { ChevronDownIcon, ChevronRightIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import { PlayIcon } from '@heroicons/react/24/solid';
import DynamicForm from './dynamic-form';

export interface ToolInputSchema {
  type: string;
  properties?: Record<string, unknown>;
  required?: string[];
}

export interface Tool {
  name: string;
  description: string;
  inputSchema: ToolInputSchema;
}

interface ToolCardProps {
  tool: Tool;
  serverId: number;
  onExecute: (toolName: string, arguments_: Record<string, any>) => Promise<ExecutionResult>;
}

interface ExecutionResult {
  success: boolean;
  result?: any;
  error?: string;
}

// Helper to check for "empty" values
function isEmptyValue(value: any): boolean {
  if (value == null) return true; // null or undefined
  if (typeof value === 'string') return value.trim() === '';
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'object') return Object.keys(value).length === 0;
  return false;
}

const ToolCard = ({ tool, serverId, onExecute }: ToolCardProps) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showRunForm, setShowRunForm] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<ExecutionResult | null>(null);

  // Generate a unique key for localStorage based on tool name and server
  const getStorageKey = useCallback(() => {
    return `smithery_tool_form_${serverId}_${tool.name}`;
  }, [tool.name, serverId]);

  // Clear form data from localStorage
  const clearStoredFormData = useCallback(() => {
    localStorage.removeItem(getStorageKey());
  }, [getStorageKey]);

  const handleRunTool = async (arguments_: Record<string, any>) => {
    setIsRunning(true);
    try {
      // filter empty values
      const filteredArgs = Object.fromEntries(
        Object.entries(arguments_).filter(([_, v]) => !isEmptyValue(v))
      );

      const executionResult = await onExecute(tool.name, filteredArgs);
      setResult(executionResult);
    } catch (error) {
      setResult({
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      });
    } finally {
      setIsRunning(false);
    }
  };

  const handleCancelRun = () => {
    setShowRunForm(false);
    clearStoredFormData();
    setResult(null);
  };

  const handleCloseResult = () => {
    setResult(null);
  };

  const renderResult = () => {
    if (!result) return null;

    return (
      <div className="mt-4 border border-gray-300 rounded-lg p-4">
        <div className="flex justify-between items-center mb-2">
          <h4 className="text-sm font-semibold text-gray-900">
            {result.success ? '✓ Result' : '✗ Error'}
          </h4>
          <button
            onClick={handleCloseResult}
            className="text-gray-400 hover:text-gray-600 text-sm"
          >
            Close
          </button>
        </div>

        <div className={`p-3 rounded-md ${result.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
          {result.success ? (
            <pre className="text-xs text-gray-800 overflow-auto whitespace-pre-wrap">
              {typeof result.result === 'string'
                ? result.result
                : JSON.stringify(result.result, null, 2)}
            </pre>
          ) : (
            <p className="text-sm text-red-800">{result.error}</p>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4 shadow-sm hover:shadow-md transition-shadow">
      <div
        className="flex justify-between items-center cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex-1">
          <h3 className="text-lg font-medium text-gray-900">
            {tool.name}
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            {tool.description || 'No description'}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(true); // Ensure card is expanded when showing run form
              setShowRunForm(true);
            }}
            className="flex items-center space-x-1 px-3 py-1.5 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={isRunning}
          >
            {isRunning ? (
              <>
                <ArrowPathIcon className="h-4 w-4 animate-spin" />
                <span>Running...</span>
              </>
            ) : (
              <>
                <PlayIcon className="h-4 w-4" />
                <span>Run</span>
              </>
            )}
          </button>
          <button className="text-gray-400 hover:text-gray-600">
            {isExpanded ? <ChevronDownIcon className="h-5 w-5" /> : <ChevronRightIcon className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="mt-4 space-y-4">
          {/* Schema Display */}
          {!showRunForm && (
            <div className="bg-gray-50 rounded-md p-3 border border-gray-300">
              <h4 className="text-sm font-medium text-gray-900 mb-2">Input Schema</h4>
              <pre className="text-xs text-gray-600 overflow-auto">
                {JSON.stringify(tool.inputSchema, null, 2)}
              </pre>
            </div>
          )}

          {/* Run Form */}
          {showRunForm && (
            <div className="border border-gray-300 rounded-lg p-4 bg-gray-50">
              <DynamicForm
                schema={tool.inputSchema || { type: 'object' }}
                onSubmit={handleRunTool}
                onCancel={handleCancelRun}
                loading={isRunning}
                storageKey={getStorageKey()}
                title={`Run ${tool.name}`}
              />

              {/* Tool Result */}
              {renderResult()}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ToolCard;
