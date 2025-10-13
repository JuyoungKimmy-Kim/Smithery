"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { MCPServer, ProtocolType, MCPServerTool, MCPServerProperty } from "../../types/mcp";
import { MCP_CATEGORIES } from "@/constants/categories";
import { useAuth } from "@/contexts/AuthContext";
import { PlusIcon, TrashIcon, PencilIcon, CheckCircleIcon } from "@heroicons/react/24/outline";
import TagSelector from "@/components/tag-selector";

export default function SubmitMCPPage() {
  const router = useRouter();
  const { token, isAuthenticated } = useAuth();
  const [formData, setFormData] = useState({
    name: "",
    category: "",
    github_link: "",
    description: "",
    tags: "",
    protocol: "",
    url: "",
    config: ""
  });
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [allTags, setAllTags] = useState<string[]>([]);
  const [tagCounts, setTagCounts] = useState<{[key: string]: number}>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [validationErrors, setValidationErrors] = useState<{[key: string]: string}>({});
  const [previewTools, setPreviewTools] = useState<any[]>([]);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  
  const [tools, setTools] = useState<MCPServerTool[]>([]);
  const [showAddTool, setShowAddTool] = useState(false);
  const [editingToolIndex, setEditingToolIndex] = useState<number | null>(null);
  const [toolForm, setToolForm] = useState({
    name: "",
    description: "",
    parameters: [] as MCPServerProperty[]
  });
  const [showAddParameter, setShowAddParameter] = useState(false);
  const [editingParameterIndex, setEditingParameterIndex] = useState<number | null>(null);
  const [parameterForm, setParameterForm] = useState({
    name: "",
    description: "",
    type: "",
    required: false
  });

  useEffect(() => {
    if (!isAuthenticated) {
      alert('Sign in required.');
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  // 모든 태그 가져오기
  useEffect(() => {
    const fetchAllTags = async () => {
      try {
        const response = await fetch('/api/posts');
        if (response.ok) {
          const data = await response.json();
          
          // 태그 추출 및 사용 빈도 계산
          const tagCountMap: {[key: string]: number} = {};
          data.forEach((post: any) => {
            if (post.tags) {
              let tagArray: string[] = [];
              try {
                const parsed = JSON.parse(post.tags);
                tagArray = Array.isArray(parsed) ? parsed : [parsed];
              } catch {
                if (typeof post.tags === 'string') {
                  if (post.tags.startsWith('[') && post.tags.endsWith(']')) {
                    const cleanTags = post.tags.slice(1, -1);
                    tagArray = cleanTags.split(',').map(tag => 
                      tag.trim().replace(/['"]/g, '')
                    ).filter(tag => tag.length > 0);
                  } else {
                    tagArray = post.tags.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0);
                  }
                }
              }
              tagArray.forEach(tag => {
                tagCountMap[tag] = (tagCountMap[tag] || 0) + 1;
              });
            }
          });
          
          const sortedTags = Object.keys(tagCountMap).sort((a, b) => tagCountMap[b] - tagCountMap[a]);
          setTagCounts(tagCountMap);
          setAllTags(sortedTags);
        }
      } catch (error) {
        console.error('Error fetching tags:', error);
      }
    };

    fetchAllTags();
  }, []);

  const handleNewTagAdded = (newTag: string) => {
    // 새 태그를 allTags에 추가하고 정렬
    if (!allTags.includes(newTag)) {
      const updatedTags = [...allTags, newTag].sort();
      setAllTags(updatedTags);
    }
    
    // 새 태그의 카운트를 0으로 설정
    setTagCounts(prev => ({
      ...prev,
      [newTag]: 0
    }));
  };

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


  const handleUrlChange = async (url: string, protocol: string) => {
    if (!url.trim() || !protocol) {
      setPreviewTools([]);
      return;
    }
    
    try {
      console.log('MCP Server URL detected:', url, 'Protocol:', protocol);
      await detectAndPreviewTools({ url: url.trim(), protocol });
    } catch (error) {
      console.error('URL 처리 실패:', error);
      setPreviewTools([]);
    }
  };


  const requestToolsList = async (config: any) => {
    try {
      console.log('Requesting tools via backend proxy:', config);
      
      // 백엔드 프록시 API를 통해 tools 가져오기
      const response = await fetch('/api/mcp-servers/preview-tools', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          url: config.url,
          protocol: config.protocol
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('Backend proxy response:', data);
        
        if (data.success && data.tools && data.tools.length > 0) {
          setPreviewTools(data.tools);
        } else {
          console.log('No tools found or request failed:', data.message);
          setPreviewTools([]);
        }
      } else {
        console.error('Backend proxy request failed:', response.status);
        setPreviewTools([]);
      }
    } catch (error) {
      console.error('tools/list 요청 실패:', error);
      setPreviewTools([]);
    }
  };


  const detectAndPreviewTools = async (config: any) => {
    setIsLoadingPreview(true);
    
    try {
      console.log('Fetching tools from MCP Server:', config.url, 'Protocol:', config.protocol);
      await requestToolsList(config);
    } catch (error) {
      console.error('MCP Server tools 가져오기 실패:', error);
      setPreviewTools([]);
    } finally {
      setIsLoadingPreview(false);
    }
  };

  const handleAddTool = () => {
    setToolForm({
      name: "",
      description: "",
      parameters: []
    });
    setShowAddTool(true);
    setEditingToolIndex(null);
  };

  const handleEditTool = (index: number) => {
    const tool = tools[index];
    setToolForm({
      name: tool.name,
      description: tool.description,
      parameters: [...tool.parameters]
    });
    setShowAddTool(true);
    setEditingToolIndex(index);
  };

  const handleSaveTool = () => {
    if (!toolForm.name.trim() || !toolForm.description.trim()) {
      alert('Tool name과 description은 필수입니다.');
      return;
    }

    const newTool: MCPServerTool = {
      name: toolForm.name.trim(),
      description: toolForm.description.trim(),
      parameters: toolForm.parameters
    };

    if (editingToolIndex !== null) {
      const updatedTools = [...tools];
      updatedTools[editingToolIndex] = newTool;
      setTools(updatedTools);
    } else {
      setTools([...tools, newTool]);
    }

    setShowAddTool(false);
    setEditingToolIndex(null);
    setToolForm({
      name: "",
      description: "",
      parameters: []
    });
  };

  const handleDeleteTool = (index: number) => {
    if (window.confirm('이 tool을 삭제하시겠습니까?')) {
      const updatedTools = tools.filter((_, i) => i !== index);
      setTools(updatedTools);
    }
  };

  const handleAddParameter = () => {
    if (!parameterForm.name.trim()) {
      alert('Parameter name은 필수입니다.');
      return;
    }

    const newParameter: MCPServerProperty = {
      name: parameterForm.name.trim(),
      description: parameterForm.description.trim(),
      type: parameterForm.type,
      required: parameterForm.required
    };

    setToolForm(prev => ({
      ...prev,
      parameters: [...prev.parameters, newParameter]
    }));

    setParameterForm({
      name: "",
      description: "",
      type: "",
      required: false
    });
    setShowAddParameter(false);
  };

  const handleDeleteParameter = (index: number) => {
    setToolForm(prev => ({
      ...prev,
      parameters: prev.parameters.filter((_, i) => i !== index)
    }));
  };

  const handleEditParameter = (index: number) => {
    const param = toolForm.parameters[index];
    setParameterForm({
      name: param.name,
      description: param.description || "",
      type: param.type || "",
      required: param.required
    });
    setEditingParameterIndex(index);
    setShowAddParameter(true);
  };

  const handleUpdateParameter = () => {
    if (!parameterForm.name.trim()) {
      alert('Parameter name은 필수입니다.');
      return;
    }

    if (editingParameterIndex !== null) {
      const updatedParameters = [...toolForm.parameters];
      updatedParameters[editingParameterIndex] = {
        name: parameterForm.name.trim(),
        description: parameterForm.description.trim(),
        type: parameterForm.type,
        required: parameterForm.required
      };
      
      setToolForm(prev => ({
        ...prev,
        parameters: updatedParameters
      }));
    }

    setParameterForm({
      name: "",
      description: "",
      type: "",
      required: false
    });
    setShowAddParameter(false);
    setEditingParameterIndex(null);
  };

  const convertMCPToolsToMCPServerTools = (mcpTools: any[]): MCPServerTool[] => {
    return mcpTools.map(tool => {
      const parameters: MCPServerProperty[] = [];
      
      if (tool.inputSchema?.properties) {
        Object.entries(tool.inputSchema.properties).forEach(([paramName, paramInfo]: [string, any]) => {
          parameters.push({
            name: paramName,
            description: paramInfo.description || '',
            type: paramInfo.type || 'string',
            required: tool.inputSchema?.required?.includes(paramName) || false
          });
        });
      }
      
      return {
        name: tool.name,
        description: tool.description || '',
        parameters: parameters
      };
    });
  };

  const handleUsePreviewTools = () => {
    if (previewTools.length > 0) {
      const convertedTools = convertMCPToolsToMCPServerTools(previewTools);
      setTools(convertedTools);
      alert(`${convertedTools.length}개의 tools가 추가되었습니다.`);
    }
  };

  const validateForm = () => {
    const errors: {[key: string]: string} = {};
    
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
    
    if (!formData.protocol.trim()) {
      errors.protocol = "Protocol은 필수입니다.";
    }
    
    if (formData.url.trim() && formData.protocol !== ProtocolType.STDIO) {
      if (!isValidUrl(formData.url)) {
        errors.url = "유효한 URL을 입력해주세요.";
      }
    }
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const isValidUrl = (url: string) => {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    
    if (!isAuthenticated) {
      setError("Sign in required.");
      return;
    }
    
    if (!validateForm()) {
      return;
    }
    
    setIsSubmitting(true);

    try {
      let config = {};
      if (formData.config.trim()) {
        try {
          config = JSON.parse(formData.config);
        } catch (error) {
          throw new Error('Server Config JSON 형식이 올바르지 않습니다.');
        }
      } else if (formData.url.trim()) {
        config = { url: formData.url.trim() };
      }

      const mcpServerData = {
        name: formData.name.trim(),
        category: formData.category.trim(),
        github_link: formData.github_link.trim(),
        description: formData.description.trim(),
        tags: selectedTags.join(', '),
        protocol: formData.protocol.trim(),
        config: config,
        tools: tools
      };


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
      setShowSuccessModal(true);
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

  const handleSuccessModalClose = () => {
    setShowSuccessModal(false);
    router.push('/');
  };

  const handleViewMCPList = () => {
    setShowSuccessModal(false);
    router.push('/');
  };

  const handleViewMyPage = () => {
    setShowSuccessModal(false);
    router.push('/mypage');
  };

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
    <div className="min-h-screen bg-gray-50 flex flex-col items-center">
      {/* Success Modal */}
      {showSuccessModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 transform transition-all">
            <div className="p-8 text-center">
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-6">
                <CheckCircleIcon className="h-8 w-8 text-green-600" />
              </div>
              
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                MCP 서버 등록이 완료되었습니다.
              </h3>
              
              <div className="text-gray-600 mb-8 space-y-2">
                <p>승인 후 MCP 목록에서 확인할 수 있으며,</p>
                <p>내 등록 서버는 My Page에서 확인하세요.</p>
              </div>
              
              <div className="flex gap-3">
                <button
                  onClick={handleViewMCPList}
                  className="flex-1 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  MCP 목록 보기
                </button>
                <button
                  onClick={handleViewMyPage}
                  className="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                >
                  My Page
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="w-full max-w-4xl p-8 bg-white shadow-lg rounded-lg my-8">
        <h1 className="text-2xl font-bold text-gray-800 mb-6 text-center">
          Deploy a New MCP Server
        </h1>
        
        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Server Name */}
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
          
          {/* Category */}
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

          {/* GitHub Link */}
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

          {/* Description */}
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
          <TagSelector
            selectedTags={selectedTags}
            onTagsChange={setSelectedTags}
            allTags={allTags}
            tagCounts={tagCounts}
            onNewTagAdded={handleNewTagAdded}
          />

          {/* Protocol */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Protocol *
            </label>
            <select
              required
              value={formData.protocol}
              onChange={(e) => {
                handleInputChange('protocol', e.target.value);
                // Protocol과 URL이 모두 있을 때 미리보기 시도
                if (formData.url.trim()) {
                  handleUrlChange(formData.url, e.target.value);
                }
              }}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                validationErrors.protocol ? 'border-red-500' : 'border-gray-300'
              }`}
            >
              <option value="">Select a protocol</option>
              <option value={ProtocolType.HTTP}>HTTP</option>
              <option value={ProtocolType.HTTP_STREAM}>HTTP-Stream</option>
              <option value={ProtocolType.WEBSOCKET}>WebSocket</option>
              <option value={ProtocolType.STDIO}>STDIO</option>
            </select>
            {validationErrors.protocol && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.protocol}</p>
            )}
          </div>

          {/* URL */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Server URL
            </label>
            <input
              type="url"
              value={formData.url}
              onChange={(e) => {
                handleInputChange('url', e.target.value);
                // Protocol과 URL이 모두 있을 때 미리보기 시도
                if (formData.protocol.trim()) {
                  handleUrlChange(e.target.value, formData.protocol);
                }
              }}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                validationErrors.url ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder={formData.protocol === ProtocolType.STDIO ? "python stdio_test_mcp_server.py" : "http://localhost:3000"}
            />
            {validationErrors.url && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.url}</p>
            )}
            <p className="mt-1 text-xs text-gray-500">
              {formData.protocol === ProtocolType.STDIO 
                ? "MCP 서버 실행 명령어를 입력하세요. Protocol과 함께 입력하면 자동으로 tools를 미리보기합니다."
                : "MCP Server의 URL을 입력하세요. Protocol과 함께 입력하면 자동으로 tools를 미리보기합니다."
              }
            </p>
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
              placeholder='{"type": "streamable-http", "url": "http://localhost:3000"}'
            />
            <p className="mt-1 text-xs text-gray-500">
              MCP Server 설정을 JSON 형식으로 입력하세요.
            </p>
          </div>

          {isLoadingPreview && (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-md">
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                <span className="text-blue-700">MCP Server에서 tools 정보를 가져오는 중...</span>
              </div>
            </div>
          )}

          {previewTools.length > 0 && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-md">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-green-800">
                  MCP Server Tools ({previewTools.length}개)
                </h3>
                <button
                  type="button"
                  onClick={handleUsePreviewTools}
                  className="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 transition-colors"
                >
                  모두 추가
                </button>
              </div>
              <div className="space-y-3">
                {previewTools.map((tool, index) => (
                  <div key={index} className="bg-white rounded-lg p-3 border border-green-200">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-green-900 text-sm">{tool.name}</h4>
                        <p className="text-xs text-green-700 mt-1">{tool.description || '설명 없음'}</p>
                        
                        {/* Parameters 정보 표시 */}
                        {tool.inputSchema?.properties && (
                          <div className="mt-2">
                            <p className="text-xs font-medium text-gray-700 mb-1">Parameters:</p>
                            <div className="space-y-1">
                              {Object.entries(tool.inputSchema.properties).map(([paramName, paramInfo]: [string, any]) => (
                                <div key={paramName} className="text-xs text-gray-600 flex items-center gap-2">
                                  <span className="font-medium">{paramName}</span>
                                  <span className="text-blue-600">({paramInfo.type || 'any'})</span>
                                  {tool.inputSchema?.required?.includes(paramName) && (
                                    <span className="text-red-600 text-xs">required</span>
                                  )}
                                  {paramInfo.description && (
                                    <span className="text-gray-500">- {paramInfo.description}</span>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {formData.url && formData.protocol && !isLoadingPreview && previewTools.length === 0 && formData.protocol !== ProtocolType.STDIO && (
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-md">
              <div className="flex items-center">
                <div className="text-yellow-600 mr-2">⚠️</div>
                <span className="text-yellow-700 text-sm">
                  MCP Server에 연결할 수 없습니다. Server URL과 프로토콜을 확인하고 서버가 실행 중인지 확인해주세요.
                </span>
              </div>
            </div>
          )}

          {formData.protocol === ProtocolType.STDIO && (
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-md">
              <div className="flex items-center">
                <div className="text-yellow-600 mr-2">⚠️</div>
                <div className="text-yellow-700 text-sm">
                  <p className="font-medium mb-1">STDIO 프로토콜 안내:</p>
                  <p>STDIO 프로토콜은 브라우저에서 직접 미리보기할 수 없습니다.</p>
                  <p>수동으로 tools를 추가해주세요.</p>
                </div>
              </div>
            </div>
          )}

          <div className="border-t pt-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-800">
                Tools ({tools.length})
              </h2>
              <button
                type="button"
                onClick={handleAddTool}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                <PlusIcon className="h-4 w-4" />
                Add Tool
              </button>
            </div>

            {tools.length > 0 && (
              <div className="space-y-3 mb-4">
                {tools.map((tool, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">{tool.name}</h3>
                        <p className="text-sm text-gray-600 mt-1">{tool.description}</p>
                        {tool.parameters && tool.parameters.length > 0 && (
                          <div className="mt-2">
                            <p className="text-xs font-medium text-gray-700 mb-1">Parameters:</p>
                            <div className="space-y-1">
                              {tool.parameters.map((param, paramIndex) => (
                                <div key={paramIndex} className="text-xs text-gray-600">
                                  • {param.name} 
                                  {param.type && <span className="text-blue-600"> ({param.type})</span>}
                                  {param.required && <span className="text-red-600"> (required)</span>}
                                  {param.description && ` - ${param.description}`}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        {tool.inputSchema?.properties && Object.keys(tool.inputSchema.properties).length > 0 && (
                          <div className="mt-2">
                            <p className="text-xs font-medium text-gray-700 mb-1">Parameters:</p>
                            <div className="space-y-1">
                              {Object.entries(tool.inputSchema.properties).map(([paramName, paramInfo]: [string, any]) => (
                                <div key={paramName} className="text-xs text-gray-600">
                                  • {paramName} 
                                  {paramInfo.type && <span className="text-blue-600"> ({paramInfo.type})</span>}
                                  {tool.inputSchema?.required?.includes(paramName) && <span className="text-red-600"> (required)</span>}
                                  {paramInfo.description && ` - ${paramInfo.description}`}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                      <div className="flex gap-2 ml-4">
                        <button
                          type="button"
                          onClick={() => handleEditTool(index)}
                          className="p-1 text-gray-400 hover:text-blue-600"
                        >
                          <PencilIcon className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteTool(index)}
                          className="p-1 text-gray-400 hover:text-red-600"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {showAddTool && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                  <h3 className="text-lg font-semibold mb-4">
                    {editingToolIndex !== null ? 'Edit Tool' : 'Add New Tool'}
                  </h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Tool Name *
                      </label>
                      <input
                        type="text"
                        value={toolForm.name}
                        onChange={(e) => setToolForm(prev => ({ ...prev, name: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="tool_name"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Description *
                      </label>
                      <textarea
                        value={toolForm.description}
                        onChange={(e) => setToolForm(prev => ({ ...prev, description: e.target.value }))}
                        rows={3}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Tool description..."
                      />
                    </div>

                    {/* Parameters */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <label className="block text-sm font-medium text-gray-700">
                          Parameters
                        </label>
                        <button
                          type="button"
                          onClick={() => setShowAddParameter(true)}
                          className="text-sm text-blue-600 hover:text-blue-800"
                        >
                          + Add Parameter
                        </button>
                      </div>
                      
                      {toolForm.parameters.length > 0 && (
                        <div className="space-y-2 mb-2">
                          {toolForm.parameters.map((param, index) => (
                            <div key={index} className="flex items-center gap-2 p-2 bg-gray-50 rounded">
                              <span className="text-sm font-medium">{param.name}</span>
                              {param.type && <span className="text-xs text-blue-600">({param.type})</span>}
                              {!param.type && <span className="text-xs text-gray-400">(no type)</span>}
                              {param.required && <span className="text-xs text-red-600">(required)</span>}
                              {param.description && <span className="text-xs text-gray-600">- {param.description}</span>}
                              <div className="flex gap-1 ml-auto">
                                <button
                                  type="button"
                                  onClick={() => handleEditParameter(index)}
                                  className="text-blue-600 hover:text-blue-800"
                                >
                                  <PencilIcon className="h-3 w-3" />
                                </button>
                                <button
                                  type="button"
                                  onClick={() => handleDeleteParameter(index)}
                                  className="text-red-600 hover:text-red-800"
                                >
                                  <TrashIcon className="h-3 w-3" />
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      {showAddParameter && (
                        <div className="border border-gray-200 rounded-lg p-3 bg-gray-50">
                          <h4 className="text-sm font-medium text-gray-700 mb-2">
                            {editingParameterIndex !== null ? 'Edit Parameter' : 'Add Parameter'}
                          </h4>
                          <div className="grid grid-cols-1 md:grid-cols-4 gap-2 mb-2">
                            <input
                              type="text"
                              placeholder="Parameter name"
                              value={parameterForm.name}
                              onChange={(e) => setParameterForm(prev => ({ ...prev, name: e.target.value }))}
                              className="px-2 py-1 text-sm border border-gray-300 rounded"
                            />
                            <input
                              type="text"
                              placeholder="Description (optional)"
                              value={parameterForm.description}
                              onChange={(e) => setParameterForm(prev => ({ ...prev, description: e.target.value }))}
                              className="px-2 py-1 text-sm border border-gray-300 rounded"
                            />
                            <select
                              value={parameterForm.type}
                              onChange={(e) => setParameterForm(prev => ({ ...prev, type: e.target.value }))}
                              className="px-2 py-1 text-sm border border-gray-300 rounded"
                            >
                              <option value="">Select type</option>
                              <option value="string">String</option>
                              <option value="integer">Integer</option>
                              <option value="number">Number</option>
                              <option value="boolean">Boolean</option>
                              <option value="object">Object</option>
                              <option value="array">Array</option>
                              <option value="null">Null</option>
                              <option value="uri">URI</option>
                              <option value="json">JSON</option>
                              <option value="enum">Enum</option>
                              <option value="any">Any</option>
                            </select>
                            <label className="flex items-center gap-1 text-sm">
                              <input
                                type="checkbox"
                                checked={parameterForm.required}
                                onChange={(e) => setParameterForm(prev => ({ ...prev, required: e.target.checked }))}
                              />
                              Required
                            </label>
                          </div>
                          <div className="flex gap-2">
                            <button
                              type="button"
                              onClick={editingParameterIndex !== null ? handleUpdateParameter : handleAddParameter}
                              className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                            >
                              {editingParameterIndex !== null ? 'Update' : 'Add'}
                            </button>
                            <button
                              type="button"
                              onClick={() => {
                                setShowAddParameter(false);
                                setEditingParameterIndex(null);
                                setParameterForm({
                                  name: "",
                                  description: "",
                                  type: "",
                                  required: false
                                });
                              }}
                              className="px-3 py-1 bg-gray-500 text-white text-sm rounded hover:bg-gray-600"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex gap-3 mt-6">
                    <button
                      type="button"
                      onClick={handleSaveTool}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    >
                      {editingToolIndex !== null ? 'Update' : 'Add'} Tool
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setShowAddTool(false);
                        setEditingToolIndex(null);
                        setToolForm({ name: "", description: "", parameters: [] });
                      }}
                      className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

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
