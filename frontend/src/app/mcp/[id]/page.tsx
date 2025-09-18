"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  CodeBracketIcon,
  GlobeAltIcon,
  TagIcon,
  CalendarIcon,
  WrenchScrewdriverIcon,
  BookOpenIcon,
  PencilIcon,
  TrashIcon,
} from "@heroicons/react/24/outline";
import { MCPServer } from "@/types/mcp";
import { useAuth } from "@/contexts/AuthContext";

export default function MCPServerDetail() {
  const params = useParams();
  const router = useRouter();
  const { user, isAuthenticated, isAdmin, token } = useAuth();
  const [mcp, setMcp] = useState<MCPServer | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const fetchMCP = async () => {
      try {
        // 캐시를 무시하고 새로운 데이터를 가져오기 위해 timestamp 추가
        const timestamp = new Date().getTime();
        const response = await fetch(`/api/mcps/${params.id}?t=${timestamp}`);
        if (response.ok) {
          const data = await response.json();
          console.log('MCP Server Data:', data); // 디버깅용 로그
          console.log('Tools:', data.tools); // tools 데이터 확인
          setMcp(data);
        } else {
          setError("MCP server not found");
        }
      } catch (error) {
        setError("Failed to fetch MCP server");
      } finally {
        setLoading(false);
      }
    };

    if (params.id) {
      fetchMCP();
    }
  }, [params.id]);

  // 현재 사용자가 이 MCP 서버의 소유자인지 확인
  const isOwner = mcp && user && (mcp as any).owner_id === user.id;
  
  // Edit 권한: 소유자 또는 관리자
  const canEdit = isOwner || isAdmin;
  
  // Delete 권한: 관리자만
  const canDelete = isAdmin;

  const handleModify = () => {
    // 수정 페이지로 이동
    if (mcp) {
      router.push(`/mcp/${mcp.id}/edit`);
    }
  };

  const handleDelete = async () => {
    if (!mcp) return;
    
    const confirmed = window.confirm(
      `Are you sure you want to delete "${mcp.name}"? This action cannot be undone.`
    );
    
    if (!confirmed) return;
    
    setIsDeleting(true);
    
    try {
      const response = await fetch(`/api/mcps/${mcp.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        alert("MCP server deleted successfully!");
        router.push('/'); // 홈페이지로 이동
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to delete MCP server');
      }
    } catch (error) {
      console.error('Delete error:', error);
      alert('Failed to delete MCP server. Please try again.');
    } finally {
      setIsDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <h2 className="text-xl text-gray-600">
          Loading MCP server...
        </h2>
      </div>
    );
  }

  if (error || !mcp) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <h2 className="text-xl text-red-600">
          {error || "MCP server not found"}
        </h2>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4 max-w-6xl">
        {/* Header Section */}
        <div className="bg-white rounded-lg shadow-sm p-8 mb-8">
          <div className="flex items-start justify-between mb-6">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-4">
                <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                  {mcp.category || "Uncategorized"}
                </span>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  mcp.status === "active" 
                    ? "bg-green-100 text-green-800" 
                    : "bg-gray-100 text-gray-800"
                }`}>
                  {mcp.status || "Unknown"}
                </span>
              </div>
              
              <h1 className="text-3xl font-bold text-gray-900 mb-4">
                {mcp.name}
              </h1>
              
              <p className="text-lg text-gray-600 mb-6">
                {mcp.description}
              </p>

              <div className="flex items-center gap-6 text-sm text-gray-600">
                {mcp.created_at && (
                  <div className="flex items-center gap-2">
                    <CalendarIcon className="h-4 w-4" />
                    <span>Created: {new Date(mcp.created_at).toLocaleDateString()}</span>
                  </div>
                )}
                {/* 권한 정보 표시 */}
                {isAuthenticated && (
                  <div className="flex items-center gap-2">
                    <span className="text-xs px-2 py-1 rounded-full bg-gray-100">
                      {isOwner ? "Owner" : isAdmin ? "Admin" : "Viewer"}
                    </span>
                  </div>
                )}
              </div>
            </div>

            <div className="flex gap-3">
              <button 
                className="px-4 py-2 border border-blue-600 text-blue-600 rounded-md hover:bg-blue-50 transition-colors flex items-center gap-2"
                onClick={() => window.open(mcp.github_link, '_blank')}
              >
                <CodeBracketIcon className="h-4 w-4" />
                View on GitHub
              </button>
              
              {canEdit && (
                <button 
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center gap-2"
                  onClick={handleModify}
                >
                  <PencilIcon className="h-4 w-4" />
                  Edit
                </button>
              )}
              
              {canDelete && (
                <button 
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors flex items-center gap-2 disabled:opacity-50"
                  onClick={handleDelete}
                  disabled={isDeleting}
                >
                  <TrashIcon className="h-4 w-4" />
                  {isDeleting ? "Deleting..." : "Delete"}
                </button>
              )}
            </div>
          </div>

          {/* Tags */}
          {mcp.tags && mcp.tags.length > 0 && (
            <div className="flex items-center gap-2 mb-4">
              <TagIcon className="h-4 w-4 text-gray-600" />
              <div className="flex flex-wrap gap-2">
                {mcp.tags.map((tag: any, index) => {
                  let tagName = '';
                  if (typeof tag === 'string') {
                    tagName = tag;
                  } else if (tag && typeof tag === 'object' && tag.name) {
                    tagName = tag.name;
                  } else {
                    tagName = 'Unknown Tag';
                  }
                  
                  return (
                    <span
                      key={index}
                      className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full"
                    >
                      {tagName}
                    </span>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Tools & Config Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          {/* Tools (Left) */}
          <div>
            {mcp.tools && mcp.tools.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm p-8">
                <div className="flex items-center gap-2 mb-6">
                  <WrenchScrewdriverIcon className="h-6 w-6 text-blue-500" />
                  <h2 className="text-2xl font-bold text-gray-900">
                    Tools ({mcp.tools.length})
                  </h2>
                </div>
                <div className="grid gap-4">
                  {mcp.tools.map((tool, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        {tool.name}
                      </h3>
                      <p className="text-sm text-gray-600 mb-3">
                        {tool.description}
                      </p>
                      {tool.input_properties && tool.input_properties.length > 0 && (
                        <div>
                          <p className="text-sm font-medium text-gray-900 mb-2">
                            Input Properties:
                          </p>
                          <div className="space-y-1">
                            {tool.input_properties.map((prop, propIndex) => (
                              <div key={propIndex} className="flex items-center gap-2 text-xs">
                                <span className="font-medium">{prop.name}</span>
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
                  ))}
                </div>
              </div>
            )}
          </div>
          {/* Config (Right) */}
          <div>
            <div className="bg-white rounded-lg shadow-sm p-8">
              <div className="flex items-center gap-2 mb-6">
                <WrenchScrewdriverIcon className="h-6 w-6 text-blue-500" />
                <h2 className="text-2xl font-bold text-gray-900">
                  Server Config
                </h2>
              </div>
              <pre className="bg-gray-100 rounded p-4 text-xs overflow-x-auto">
                {JSON.stringify(mcp.config, null, 2)}
              </pre>
            </div>
          </div>
        </div>

        {/* Resources Section */}
        {mcp.resources && mcp.resources.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm p-8 mb-8">
            <div className="flex items-center gap-2 mb-6">
              <BookOpenIcon className="h-6 w-6 text-blue-500" />
              <h2 className="text-2xl font-bold text-gray-900">
                Resources ({mcp.resources.length})
              </h2>
            </div>
            
            <div className="grid gap-4">
              {mcp.resources.map((resource, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {resource.name}
                  </h3>
                  <p className="text-sm text-gray-600 mb-3">
                    {resource.description}
                  </p>
                  <button
                    className="text-blue-600 hover:text-blue-800 text-sm hover:underline"
                    onClick={() => window.open(resource.url, '_blank')}
                  >
                    {resource.url}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Metadata Section */}
        <div className="bg-white rounded-lg shadow-sm p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            Metadata
          </h2>
          
          <div className="grid gap-4 md:grid-cols-2">       
            <div>
              <p className="text-sm font-medium text-gray-600">
                GitHub Link
              </p>
              <button 
                className="text-blue-600 hover:text-blue-800 hover:underline"
                onClick={() => window.open(mcp.github_link, '_blank')}
              >
                {mcp.github_link}
              </button>
            </div>         
            <div>
              <p className="text-sm font-medium text-gray-600">
                Status
              </p>
              <span className={`px-2 py-1 text-xs rounded-full ${
                mcp.status === "active" 
                  ? "bg-green-100 text-green-800" 
                  : "bg-gray-100 text-gray-800"
              }`}>
                {mcp.status || "Unknown"}
              </span>
            </div>
            
            {mcp.created_at && (
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Created At
                </p>
                <p className="text-gray-900">
                  {new Date(mcp.created_at).toLocaleString()}
                </p>
              </div>
            )}
            
            {mcp.updated_at && (
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Updated At
                </p>
                <p className="text-gray-900">
                  {new Date(mcp.updated_at).toLocaleString()}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 