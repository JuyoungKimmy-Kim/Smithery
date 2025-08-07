"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { MCPServer, TransportType } from "../../types/mcp";
import { MCP_CATEGORIES } from "@/constants/categories";
import { useAuth } from "@/contexts/AuthContext";

export default function SubmitMCPPage() {
  const router = useRouter();
  const { token, isAuthenticated } = useAuth();
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
  const [previewTools, setPreviewTools] = useState<any[]>([]);
  const [previewResources, setPreviewResources] = useState<any[]>([]);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);

  // 인증 상태 확인
  useEffect(() => {
    if (!isAuthenticated) {
      alert('Sign in required.');
      router.push('/login');
    }
  }, [isAuthenticated, router]);

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

    // GitHub 링크가 변경되면 tools 미리보기 업데이트
    if (field === 'github_link' && value.trim()) {
      handleGitHubLinkChange(value);
    }
  };

  const handleGitHubLinkChange = async (githubLink: string) => {
    if (!githubLink.startsWith('https://github.com/')) {
      setPreviewTools([]);
      setPreviewResources([]);
      return;
    }

    setIsLoadingPreview(true);
    try {
      // 백엔드 API를 통해 tools 정보 미리보기 요청
      const response = await fetch('/api/mcps', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ github_link: githubLink }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Preview API Response:', data); // 디버깅용 로그
        setPreviewTools(data.tools || []);
        setPreviewResources(data.resources || []);
        console.log('Set Preview Tools:', data.tools || []); // 설정된 tools 확인
      } else {
        console.log('Preview API failed:', response.status); // 실패 로그
        setPreviewTools([]);
        setPreviewResources([]);
      }
    } catch (error) {
      console.error('Tools 미리보기 로드 실패:', error);
      setPreviewTools([]);
      setPreviewResources([]);
    } finally {
      setIsLoadingPreview(false);
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
    
    // 인증 확인
    if (!isAuthenticated) {
      setError("Sign in required.");
      return;
    }
    
    // 폼 검증
    if (!validateForm()) {
      return;
    }
    
    setIsSubmitting(true);

    try {
      // 백엔드 스키마에 맞는 데이터 형식으로 변환
      const mcpServerData = {
        name: formData.name.trim(),
        category: formData.category.trim(),
        github_link: formData.github_link.trim(),
        description: formData.description.trim(),
        tags: formData.tags.trim(), // 콤마로 구분된 문자열
        config: formData.config ? JSON.parse(formData.config) : {}
      };

      console.log('Submitting MCP Server:', mcpServerData); // 디버깅용 로그

      const response = await fetch('/api/mcps', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(mcpServerData),
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

  // 로그인하지 않은 경우 로딩 표시
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Checking authentication...</p>
        </div>
      </div>
    );
  }

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
          
          {/* Category - 필수 */}
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
              <option value="">Select a category</option>
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
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              rows={4}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                validationErrors.description ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Describe your MCP server..."
            />
            {validationErrors.description && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.description}</p>
            )}
          </div>

          {/* Tags */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tags (comma-separated)
            </label>
            <input
              type="text"
              value={formData.tags}
              onChange={(e) => handleInputChange('tags', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="python, mcp, automation"
            />
          </div>

          {/* Server Config */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Server Config (JSON)
            </label>
            <textarea
              value={formData.config}
              onChange={(e) => handleInputChange('config', e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder='{"key": "value"}'
            />
          </div>

          {/* Tools Preview */}
          {isLoadingPreview && (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-md">
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                <span className="text-blue-700">GitHub에서 tools 정보를 분석 중...</span>
              </div>
            </div>
          )}

          {previewTools.length > 0 && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-md">
              <h3 className="text-sm font-medium text-green-800 mb-2">
                발견된 Tools ({previewTools.length}개)
              </h3>
              <div className="space-y-2">
                {previewTools.map((tool, index) => (
                  <div key={index} className="text-sm text-green-700">
                    • {tool.name}: {tool.description || '설명 없음'}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? '등록 중...' : 'MCP Server 등록'}
          </button>
        </form>
      </div>
    </div>
  );
} 