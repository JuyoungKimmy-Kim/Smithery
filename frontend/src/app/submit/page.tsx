"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { MCPServer, TransportType } from "../../types/mcp";
import { MCP_CATEGORIES } from "@/constants/categories";

export default function SubmitMCPPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    name: "",
    category: "",
    github_link: "",
    description: "",
    tags: "",
    config: ""
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [validationErrors, setValidationErrors] = useState<{[key: string]: string}>({});

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
    
    // 필수 필드 검증
    if (!formData.name.trim()) {
      errors.name = "Server Name은 필수입니다.";
    }
    
    if (!formData.category.trim()) {
      errors.category = "Category는 필수입니다.";
    }
    
    if (!formData.github_link.trim()) {
      errors.github_link = "GitHub Link는 필수입니다.";
    } else if (!formData.github_link.startsWith('https://github.com/')) {
      errors.github_link = "유효한 GitHub URL을 입력해주세요.";
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
      const mcpServer: Partial<MCPServer> = {
        id: Date.now().toString(), // 임시 ID 생성
        name: formData.name.trim(),
        category: formData.category.trim(),
        github_link: formData.github_link.trim(),
        description: formData.description.trim(),
        transport: TransportType.SSE, // 기본값으로 SSE 사용
        tags: formData.tags.split(',').map(tag => tag.trim()).filter(tag => tag),
        status: "active",
        tools: [], // 기본 빈 배열
        resources: [], // 기본 빈 배열
        config: formData.config ? JSON.parse(formData.config) : {}
      };

      const response = await fetch('/api/mcps', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(mcpServer),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create MCP server');
      }

      const result = await response.json();
      alert('MCP Server가 성공적으로 등록되었습니다!');
      router.push('/'); // 메인 페이지로 이동
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

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-12">
      <div className="w-full max-w-2xl p-8 bg-white shadow-lg rounded-lg">
        <h1 className="text-2xl font-bold text-gray-800 mb-6 text-center">
          Deploy a New MCP Server
        </h1>
        
        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Server Name - 필수 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Server Name *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                validationErrors.name ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="My MCP Server"
            />
            {validationErrors.name && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.name}</p>
            )}
          </div>
          
          {/* GitHub Link - 필수 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              GitHub Link *
            </label>
            <input
              type="url"
              required
              value={formData.github_link}
              onChange={(e) => handleInputChange('github_link', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                validationErrors.github_link ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="https://github.com/username/repository"
            />
            {validationErrors.github_link && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.github_link}</p>
            )}
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
          
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? "Deploying..." : "Deploy Server"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
} 