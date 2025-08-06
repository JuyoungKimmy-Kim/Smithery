"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { MCPServer, TransportType } from "../../../../types/mcp";
import { MCP_CATEGORIES } from "@/constants/categories";
import { useAuth } from "@/contexts/AuthContext";

export default function EditMCPServerPage() {
  const params = useParams();
  const router = useRouter();
  const { token, isAuthenticated } = useAuth();
  const [mcp, setMcp] = useState<MCPServer | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    category: "",
    github_link: "",
    description: "",
    tags: "",
    config: ""
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [validationErrors, setValidationErrors] = useState<{[key: string]: string}>({});

  // tags를 문자열로 변환하는 함수
  const formatTagsToString = (tags: any): string => {
    if (!tags) return "";
    if (typeof tags === 'string') return tags;
    if (Array.isArray(tags)) {
      return tags.map((tag: any) => {
        if (typeof tag === 'string') return tag;
        if (tag && typeof tag === 'object' && tag.name) return tag.name;
        return 'Unknown Tag';
      }).join(', ');
    }
    return "";
  };

  // 인증 상태 확인
  useEffect(() => {
    if (!isAuthenticated) {
      alert('Sign in required.');
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  // 기존 MCP 서버 데이터 로드
  useEffect(() => {
    const fetchMCP = async () => {
      try {
        const response = await fetch(`/api/mcps/${params.id}`);
        if (response.ok) {
          const data = await response.json();
          setMcp(data);
          
          // 폼 데이터 초기화
          setFormData({
            name: data.name || "",
            category: data.category || "",
            github_link: data.github_link || "",
            description: data.description || "",
            tags: formatTagsToString(data.tags),
            config: data.config ? JSON.stringify(data.config, null, 2) : ""
          });
        } else {
          setError("MCP server not found");
        }
      } catch (error) {
        setError("Failed to fetch MCP server");
      } finally {
        setIsLoading(false);
      }
    };

    if (params.id) {
      fetchMCP();
    }
  }, [params.id]);

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // 입력 시 해당 필드의 validation error 제거
    if (validationErrors[field]) {
      setValidationErrors(prev => ({
        ...prev,
        [field]: ""
      }));
    }
  };

  const validateForm = () => {
    const errors: {[key: string]: string} = {};
    
    // 필수 필드 검증 (name과 github_link는 읽기 전용이므로 검증하지 않음)
    if (!formData.category.trim()) {
      errors.category = "Category는 필수입니다.";
    }
    
    if (!formData.description.trim()) {
      errors.description = "Description은 필수입니다.";
    }
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    
    // 폼 검증
    if (!validateForm()) {
      return;
    }
    
    setIsSubmitting(true);

    try {
      // 폼 데이터를 MCPServer 형식으로 변환
      const updateData = {
        description: formData.description.trim(),
        category: formData.category.trim(),
        tags: formData.tags.trim(), // 콤마로 구분된 문자열로 전송
        config: formData.config ? JSON.parse(formData.config) : {}
      };

      const response = await fetch(`/api/mcps/${params.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(updateData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update MCP server');
      }

      const result = await response.json();
      alert('MCP Server가 성공적으로 수정되었습니다!');
      
      // 상세 페이지로 이동하기 전에 잠시 대기
      setTimeout(() => {
        router.push(`/mcp/${params.id}`);
      }, 100);

    } catch (err) {
      if (err instanceof Error && err.message.includes('JSON')) {
        setError('Server Config JSON 형식이 올바르지 않습니다.');
      } else {
        setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
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
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-12">
      <div className="w-full max-w-2xl p-8 bg-white shadow-lg rounded-lg">
        <h1 className="text-2xl font-bold text-gray-800 mb-6 text-center">
          Edit MCP Server
        </h1>
        
        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Server Name - 읽기 전용 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Server Name
            </label>
            <input
              type="text"
              value={formData.name}
              disabled
              className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100 text-gray-500 cursor-not-allowed"
            />
          </div>
          
          {/* GitHub Link - 읽기 전용 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              GitHub Link
            </label>
            <input
              type="url"
              value={formData.github_link}
              disabled
              className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100 text-gray-500 cursor-not-allowed"
            />
          </div>
          
          {/* Description - 필수 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description *
            </label>
            <textarea
              required
              rows={4}
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                validationErrors.description ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="MCP 서버에 대한 상세한 설명을 입력하세요"
            />
            {validationErrors.description && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.description}</p>
            )}
          </div>
          
           {/* Category - 필수 (드롭다운) */}
           <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Category *
            </label>
            <select
              required
              value={formData.category}
              onChange={(e) => handleInputChange('category', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                validationErrors.category ? 'border-red-500' : 'border-gray-300'
              }`}
            >
              <option value="">카테고리를 선택하세요</option>
              {MCP_CATEGORIES.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
            {validationErrors.category && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.category}</p>
            )}
          </div>

          {/* Tags - 선택적 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tags (comma separated)
            </label>
            <input
              type="text"
              value={formData.tags}
              onChange={(e) => handleInputChange('tags', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="github, code, api, test"
            />
          </div>
          
          {/* Server Config - 선택적 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Server Config (JSON)
            </label>
            <textarea
              rows={6}
              value={formData.config}
              onChange={(e) => handleInputChange('config', e.target.value)}
              placeholder='{"mcpServers": {"example": {"command": "python", "args": ["server.py"]}}}'
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="mt-1 text-sm text-gray-500">
              JSON 형식으로 서버 설정을 입력하세요. 비워두면 기본 설정이 사용됩니다.
            </p>
          </div>
          
          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={() => router.push(`/mcp/${params.id}`)}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? "Updating..." : "Update Server"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
} 