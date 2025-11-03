"use client";

import React, { useState } from "react";
import {
  WrenchScrewdriverIcon,
  BookOpenIcon,
  ChatBubbleLeftRightIcon,
} from "@heroicons/react/24/outline";
import { MCPServerTool, MCPServerPrompt, MCPServerResource } from "@/types/mcp";

interface MCPCapabilitiesTabsProps {
  tools: MCPServerTool[];
  prompts?: MCPServerPrompt[];
  resources: MCPServerResource[];
}

type TabType = "tools" | "prompts" | "resources";

export default function MCPCapabilitiesTabs({
  tools,
  prompts = [],
  resources
}: MCPCapabilitiesTabsProps) {
  const [activeTab, setActiveTab] = useState<TabType>("tools");
  const [expandedTools, setExpandedTools] = useState<Set<number>>(new Set());
  const [expandedPrompts, setExpandedPrompts] = useState<Set<number>>(new Set());
  const [currentToolPage, setCurrentToolPage] = useState(1);
  const [currentPromptPage, setCurrentPromptPage] = useState(1);
  const [currentResourcePage, setCurrentResourcePage] = useState(1);
  const itemsPerPage = 5;

  const toggleToolExpansion = (index: number) => {
    const newExpanded = new Set(expandedTools);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedTools(newExpanded);
  };

  const togglePromptExpansion = (index: number) => {
    const newExpanded = new Set(expandedPrompts);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedPrompts(newExpanded);
  };

  // Pagination helpers
  const getPaginatedItems = <T,>(items: T[], currentPage: number) => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return {
      items: items.slice(startIndex, endIndex),
      totalPages: Math.ceil(items.length / itemsPerPage),
      startIndex,
    };
  };

  const renderPagination = (totalPages: number, currentPage: number, onPageChange: (page: number) => void) => {
    if (totalPages <= 1) return null;

    return (
      <div className="flex justify-center items-center gap-2 mt-6">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Previous
        </button>

        {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
          <button
            key={page}
            onClick={() => onPageChange(page)}
            className={`px-3 py-2 text-sm font-medium rounded-md ${
              currentPage === page
                ? 'bg-blue-600 text-white'
                : 'text-gray-500 bg-white border border-gray-300 hover:bg-gray-50'
            }`}
          >
            {page}
          </button>
        ))}

        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Next
        </button>
      </div>
    );
  };

  const tabs = [
    { id: "tools" as TabType, label: "Tools", count: tools.length, icon: WrenchScrewdriverIcon },
    { id: "prompts" as TabType, label: "Prompts", count: prompts.length, icon: ChatBubbleLeftRightIcon },
    { id: "resources" as TabType, label: "Resources", count: resources.length, icon: BookOpenIcon },
  ];

  // Get paginated data
  const { items: currentTools, totalPages: totalToolPages, startIndex: startToolIndex } =
    getPaginatedItems(tools, currentToolPage);
  const { items: currentPrompts, totalPages: totalPromptPages, startIndex: startPromptIndex } =
    getPaginatedItems(prompts, currentPromptPage);
  const { items: currentResources, totalPages: totalResourcePages } =
    getPaginatedItems(resources, currentResourcePage);

  return (
    <div className="bg-white rounded-lg shadow-sm p-8">
      {/* Tabs Header */}
      <div className="flex border-b border-gray-200 mb-6">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-6 py-3 font-medium transition-colors relative ${
                activeTab === tab.id
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Icon className="h-5 w-5" />
              <span>{tab.label}</span>
              <span className={`px-2 py-0.5 rounded-full text-xs ${
                activeTab === tab.id
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-700'
              }`}>
                {tab.count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div>
        {/* Tools Tab */}
        {activeTab === "tools" && (
          <div>
            {tools.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No tools available</p>
            ) : (
              <>
                <div className="grid gap-4">
                  {currentTools.map((tool, index) => {
                    const actualIndex = startToolIndex + index;
                    return (
                      <div
                        key={actualIndex}
                        className="border border-gray-200 rounded-lg p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                        onClick={() => toggleToolExpansion(actualIndex)}
                      >
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">
                          {tool.name}
                        </h3>
                        <div className="text-sm text-gray-600 mb-3">
                          <p
                            className={`${tool.description.length > 100 ? (expandedTools.has(actualIndex) ? '' : 'overflow-hidden') : ''}`}
                            style={{
                              display: tool.description.length > 100 && !expandedTools.has(actualIndex) ? '-webkit-box' : 'block',
                              WebkitLineClamp: tool.description.length > 100 && !expandedTools.has(actualIndex) ? 2 : 'unset',
                              WebkitBoxOrient: 'vertical'
                            }}
                          >
                            {tool.description}
                          </p>
                        </div>
                        {tool.parameters && tool.parameters.length > 0 && (
                          <div
                            className={`transition-all duration-300 ease-in-out ${
                              !expandedTools.has(actualIndex)
                                ? 'max-h-0 overflow-hidden opacity-0'
                                : 'max-h-96 opacity-100'
                            }`}
                          >
                            <p className="text-sm font-medium text-gray-900 mb-2">
                              Input Properties:
                            </p>
                            <div className="space-y-1">
                              {tool.parameters.map((prop, propIndex) => (
                                <div key={propIndex} className="flex items-center gap-2 text-xs">
                                  <span className="font-medium">{prop.name}</span>
                                  {prop.type && (
                                    <span className="px-1 py-0.5 bg-blue-100 text-blue-800 text-xs rounded">
                                      {prop.type}
                                    </span>
                                  )}
                                  {prop.required && (
                                    <span className="px-1 py-0.5 bg-red-100 text-red-800 text-xs rounded">Required</span>
                                  )}
                                  {prop.description && (
                                    <span className="text-gray-600">- {prop.description}</span>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
                {renderPagination(totalToolPages, currentToolPage, setCurrentToolPage)}
              </>
            )}
          </div>
        )}

        {/* Prompts Tab */}
        {activeTab === "prompts" && (
          <div>
            {prompts.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No prompts available</p>
            ) : (
              <>
                <div className="grid gap-4">
                  {currentPrompts.map((prompt, index) => {
                    const actualIndex = startPromptIndex + index;
                    return (
                      <div
                        key={actualIndex}
                        className="border border-gray-200 rounded-lg p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                        onClick={() => togglePromptExpansion(actualIndex)}
                      >
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">
                          {prompt.name}
                        </h3>
                        {prompt.description && (
                          <p className="text-sm text-gray-600 mb-3">
                            {prompt.description}
                          </p>
                        )}
                        {prompt.arguments && prompt.arguments.length > 0 && (
                          <div
                            className={`transition-all duration-300 ease-in-out ${
                              !expandedPrompts.has(actualIndex)
                                ? 'max-h-0 overflow-hidden opacity-0'
                                : 'max-h-96 opacity-100'
                            }`}
                          >
                            <p className="text-sm font-medium text-gray-900 mb-2">
                              Arguments:
                            </p>
                            <div className="space-y-1">
                              {prompt.arguments.map((arg, argIndex) => (
                                <div key={argIndex} className="flex items-center gap-2 text-xs">
                                  <span className="font-medium">{arg.name}</span>
                                  {arg.type && (
                                    <span className="px-1 py-0.5 bg-purple-100 text-purple-800 text-xs rounded">
                                      {arg.type}
                                    </span>
                                  )}
                                  {arg.required && (
                                    <span className="px-1 py-0.5 bg-red-100 text-red-800 text-xs rounded">Required</span>
                                  )}
                                  {arg.description && (
                                    <span className="text-gray-600">- {arg.description}</span>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
                {renderPagination(totalPromptPages, currentPromptPage, setCurrentPromptPage)}
              </>
            )}
          </div>
        )}

        {/* Resources Tab */}
        {activeTab === "resources" && (
          <div>
            {resources.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No resources available</p>
            ) : (
              <>
                <div className="grid gap-4">
                  {currentResources.map((resource, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        {resource.name}
                      </h3>
                      {resource.description && (
                        <p className="text-sm text-gray-600 mb-3">
                          {resource.description}
                        </p>
                      )}
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-500">URI:</span>
                        <code className="text-xs bg-gray-100 px-2 py-1 rounded font-mono">
                          {resource.uri}
                        </code>
                      </div>
                      {resource.mimeType && (
                        <div className="flex items-center gap-2 mt-2">
                          <span className="text-xs text-gray-500">MIME Type:</span>
                          <span className="px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded">
                            {resource.mimeType}
                          </span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                {renderPagination(totalResourcePages, currentResourcePage, setCurrentResourcePage)}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
