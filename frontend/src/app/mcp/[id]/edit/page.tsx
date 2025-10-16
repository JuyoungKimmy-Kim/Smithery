"use client";

import React, { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { MCPServer, ProtocolType, MCPServerTool, MCPServerProperty } from "../../../../types/mcp";
import { useAuth } from "@/contexts/AuthContext";
import { PlusIcon, TrashIcon, PencilIcon, CheckCircleIcon } from "@heroicons/react/24/outline";
import TagSelector from "@/components/tag-selector";
import { apiFetch } from "@/lib/api-client";

export default function EditMCPServerPage() {
  const params = useParams();
  const router = useRouter();
  const { token, isAuthenticated } = useAuth();
  const AUTOSAVE_KEY = `mcp_edit_autosave_${params.id}`;
  const hasRedirectedRef = useRef(false);
  
  const [mcp, setMcp] = useState<MCPServer | null>(null);
  const [formData, setFormData] = useState({
    name: "",
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
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [validationErrors, setValidationErrors] = useState<{[key: string]: string}>({});
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [showSessionExpiredModal, setShowSessionExpiredModal] = useState(false);
  const [lastSavedTime, setLastSavedTime] = useState<Date | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [isDataLoaded, setIsDataLoaded] = useState(false);

  const [tools, setTools] = useState<MCPServerTool[]>([]);
  const [showAddTool, setShowAddTool] = useState(false);
  const [editingToolIndex, setEditingToolIndex] = useState<number | null>(null);
  const [toolForm, setToolForm] = useState({
    name: "",
    description: "",
    parameters: [] as MCPServerProperty[]
  });
  const [showAddParameter, setShowAddParameter] = useState(false);
  const [parameterForm, setParameterForm] = useState({
    name: "",
    description: "",
    type: "",
    required: false
  });
  const [editingParameterIndex, setEditingParameterIndex] = useState<number | null>(null);

  // 폼에 내용이 있는지 확인하는 함수
  const hasFormContent = (): boolean => {
    return !!(formData.name || 
              formData.github_link || 
              formData.description || 
              selectedTags.length > 0 || 
              tools.length > 0);
  };

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

  // 초기 인증 체크 (한 번만 실행)
  useEffect(() => {
    if (isDataLoaded && !isAuthenticated && !hasRedirectedRef.current && !showSessionExpiredModal) {
      hasRedirectedRef.current = true;
      router.push('/login');
    }
  }, [isDataLoaded, isAuthenticated, showSessionExpiredModal, router]);

  // 자동 저장된 데이터 복원 (MCP 데이터 로드 후)
  useEffect(() => {
    // MCP 데이터가 로드되지 않았으면 복원하지 않음
    if (!mcp || !isDataLoaded) return;
    
    try {
      const hasAskedRestore = sessionStorage.getItem(`hasAskedRestore_${params.id}`);
      const savedData = localStorage.getItem(AUTOSAVE_KEY);
      
      if (savedData && !hasAskedRestore) {
        const parsed = JSON.parse(savedData);
        const savedTime = new Date(parsed.savedAt).getTime();
        const now = new Date().getTime();
        const hoursSinceAutosave = (now - savedTime) / (1000 * 60 * 60);
        
        if (hoursSinceAutosave < 24) {
          if (confirm('이전에 수정하던 내용이 있습니다. 복원하시겠습니까?')) {
            setFormData(parsed.formData || formData);
            setSelectedTags(parsed.selectedTags || []);
            setTools(parsed.tools || []);
            sessionStorage.setItem(`hasAskedRestore_${params.id}`, 'true');
            console.log('자동 저장된 수정 내용을 복원했습니다.');
          } else {
            localStorage.removeItem(AUTOSAVE_KEY);
            sessionStorage.setItem(`hasAskedRestore_${params.id}`, 'true');
          }
        } else {
          localStorage.removeItem(AUTOSAVE_KEY);
        }
      } else if (savedData && hasAskedRestore) {
        // 이미 복원 여부를 물어봤으면 조용히 복원
        const parsed = JSON.parse(savedData);
        const savedTime = new Date(parsed.savedAt).getTime();
        const now = new Date().getTime();
        const hoursSinceAutosave = (now - savedTime) / (1000 * 60 * 60);
        
        if (hoursSinceAutosave < 24) {
          setFormData(parsed.formData || formData);
          setSelectedTags(parsed.selectedTags || []);
          setTools(parsed.tools || []);
          console.log('자동 저장된 수정 내용을 조용히 복원했습니다.');
        }
      }
    } catch (error) {
      console.error('자동 저장 데이터 복원 실패:', error);
      localStorage.removeItem(AUTOSAVE_KEY);
    }
  }, [mcp, isDataLoaded, params.id]); // MCP 데이터 로드 후 실행

  // 폼 데이터 변경 시 자동 저장
  useEffect(() => {
    if (!isDataLoaded || !mcp) return; // 데이터 로드 완료 후에만 저장
    
    setHasUnsavedChanges(hasFormContent());
    
    const timeoutId = setTimeout(() => {
      try {
        const now = new Date();
        const dataToSave = {
          formData,
          selectedTags,
          tools,
          savedAt: now.toISOString()
        };
        localStorage.setItem(AUTOSAVE_KEY, JSON.stringify(dataToSave));
        setLastSavedTime(now);
        console.log('수정 중인 내용이 자동 저장되었습니다.');
      } catch (error) {
        console.error('자동 저장 실패:', error);
      }
    }, 5000);

    return () => clearTimeout(timeoutId);
  }, [formData, selectedTags, tools, isDataLoaded, mcp]);

  // 페이지 이탈 방지 (브라우저 닫기/새로고침)
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges && !isSubmitting) {
        e.preventDefault();
        e.returnValue = '';
        return '작성 중인 내용이 있습니다. 정말 페이지를 벗어나시겠습니까?';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasUnsavedChanges, isSubmitting]);

  // 페이지 이탈 방지 (뒤로가기 버튼)
  useEffect(() => {
    if (hasUnsavedChanges) {
      window.history.pushState({ page: 'edit' }, '');
    }

    const handlePopState = (e: PopStateEvent) => {
      if (hasUnsavedChanges && !isSubmitting) {
        const confirmLeave = window.confirm(
          '수정 중인 내용이 자동 저장되었습니다.\n페이지를 벗어나시겠습니까?'
        );
        
        if (!confirmLeave) {
          window.history.pushState({ page: 'edit' }, '');
        } else {
          setHasUnsavedChanges(false);
        }
      }
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [hasUnsavedChanges, isSubmitting]);

  // 페이지 이탈 방지 (내부 링크 클릭)
  useEffect(() => {
    const handleLinkClick = (e: MouseEvent) => {
      if (!hasUnsavedChanges || isSubmitting) return;
      
      const target = e.target as HTMLElement;
      const isNavbarLink = target.closest('nav a, nav button');
      const linkElement = target.closest('a');
      
      if (isNavbarLink || (linkElement && !linkElement.closest('.edit-page-content'))) {
        e.preventDefault();
        e.stopPropagation();
        
        const confirmLeave = window.confirm(
          '수정 중인 내용이 자동 저장되었습니다.\n페이지를 벗어나시겠습니까?'
        );
        
        if (confirmLeave) {
          setHasUnsavedChanges(false);
          if (linkElement instanceof HTMLAnchorElement) {
            const href = linkElement.getAttribute('href');
            if (href) {
              setTimeout(() => router.push(href), 0);
            }
          } else if (isNavbarLink instanceof HTMLButtonElement) {
            setTimeout(() => (isNavbarLink as HTMLButtonElement).click(), 0);
          }
        }
      }
    };

    document.addEventListener('click', handleLinkClick, true);
    return () => document.removeEventListener('click', handleLinkClick, true);
  }, [hasUnsavedChanges, isSubmitting, router]);

  // 세션 만료 이벤트 리스너
  useEffect(() => {
    const handleSessionExpired = () => {
      console.log('Session expired event received, showing modal...');
      setShowSessionExpiredModal(true);
    };

    window.addEventListener('session-expired', handleSessionExpired);
    return () => window.removeEventListener('session-expired', handleSessionExpired);
  }, []);

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
                    tagArray = cleanTags.split(',').map((tag: string) => 
                      tag.trim().replace(/['"]/g, '')
                    ).filter((tag: string) => tag.length > 0);
                  } else {
                    tagArray = post.tags.split(',').map((tag: string) => tag.trim()).filter((tag: string) => tag.length > 0);
                  }
                }
              }
              tagArray.forEach((tag: string) => {
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

  useEffect(() => {
    const fetchMCP = async () => {
      try {
        const response = await fetch(`/api/mcps/${params.id}`);
        if (response.ok) {
          const data = await response.json();
          setMcp(data);
          
          setFormData({
            name: data.name || "",
            github_link: data.github_link || "",
            description: data.description || "",
            tags: formatTagsToString(data.tags),
            protocol: data.protocol || "http",
            url: data.config?.url || "",
            config: data.config ? JSON.stringify(data.config, null, 2) : ""
          });

          // 기존 태그를 선택된 태그로 설정
          const existingTags = formatTagsToString(data.tags);
          if (existingTags) {
            const tagArray = existingTags.split(',').map((tag: string) => tag.trim()).filter((tag: string) => tag.length > 0);
            setSelectedTags(tagArray);
          }
          
          setTools(data.tools || []);
        } else {
          setError("MCP server not found");
        }
      } catch (error) {
        setError("Failed to fetch MCP server");
      } finally {
        setIsLoading(false);
        setIsDataLoaded(true); // 데이터 로드 완료 플래그
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
    
    if (validationErrors[field]) {
      setValidationErrors(prev => ({
        ...prev,
        [field]: ""
      }));
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

  const validateForm = () => {
    const errors: {[key: string]: string} = {};
    
    
    if (!formData.description.trim()) {
      errors.description = "Description은 필수입니다.";
    }
    
    if (!formData.protocol.trim()) {
      errors.protocol = "Protocol은 필수입니다.";
    }
    
    if (formData.url.trim() && formData.protocol !== ProtocolType.STDIO) {
      try {
        new URL(formData.url);
      } catch {
        errors.url = "유효한 URL을 입력해주세요.";
      }
    }
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    
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

      const updateData = {
        description: formData.description.trim(),
        protocol: formData.protocol.trim(),
        tags: selectedTags.join(', '),
        config: config,
        tools: tools
      };

      const response = await apiFetch(`/api/mcps/${params.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        requiresAuth: true,
        body: JSON.stringify(updateData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update MCP server');
      }

      const result = await response.json();
      
      // 수정 성공 시 자동 저장 데이터 삭제 및 플래그 해제
      localStorage.removeItem(AUTOSAVE_KEY);
      sessionStorage.removeItem(`hasAskedRestore_${params.id}`);
      setHasUnsavedChanges(false);
      console.log('수정 완료. 자동 저장 데이터를 삭제했습니다.');
      
      setShowSuccessModal(true);
    } catch (err) {
      // 세션 만료 에러인 경우 모달 표시
      if (err instanceof Error && err.message === 'SESSION_EXPIRED') {
        console.log('Session expired, showing modal...');
        setShowSessionExpiredModal(true);
        return;
      }
      
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
    router.push(`/mcp/${params.id}`);
  };

  const handleViewMCPList = () => {
    setShowSuccessModal(false);
    router.push('/');
  };

  const handleViewMyPage = () => {
    setShowSuccessModal(false);
    router.push('/mypage');
  };

  if (isLoading || (!isDataLoaded && !showSessionExpiredModal)) {
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
    <div className="min-h-screen bg-gray-50 flex flex-col items-center edit-page-content">
      {/* Session Expired Modal */}
      {showSessionExpiredModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 transform transition-all">
            <div className="p-8 text-center">
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-yellow-100 mb-6">
                <svg className="h-8 w-8 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                Session Expired
              </h3>
              
              <div className="text-gray-600 mb-6 space-y-2">
                <p>Draft saved automatically.</p>
                <p>Log in again to continue.</p>
              </div>
              
              <button
                onClick={() => router.push('/login')}
                className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors font-medium"
              >
                OK
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Success Modal */}
      {showSuccessModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 transform transition-all">
            <div className="p-8 text-center">
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-6">
                <CheckCircleIcon className="h-8 w-8 text-green-600" />
              </div>
              
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                MCP 서버 수정이 완료되었습니다.
              </h3>
              
              <div className="text-gray-600 mb-8 space-y-2">
                <p>수정된 내용이 반영되었으며,</p>
                <p>MCP 목록에서 확인할 수 있습니다.</p>
              </div>
              
              <div className="flex gap-3">
                <button
                  onClick={handleSuccessModalClose}
                  className="flex-1 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  상세 페이지 보기
                </button>
                <button
                  onClick={handleViewMCPList}
                  className="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                >
                  MCP 목록 보기
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="w-full max-w-4xl p-8 bg-white shadow-lg rounded-lg my-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-800 text-center">
            Edit MCP Server
          </h1>
          {lastSavedTime && (
            <p className="text-xs text-gray-500 text-center mt-2">
              💾 자동 저장됨: {lastSavedTime.toLocaleTimeString('ko-KR')}
            </p>
          )}
        </div>
        
        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Server Name */}
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
          
          {/* GitHub Link */}
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
          
          {/* Description */}
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
              onChange={(e) => handleInputChange('protocol', e.target.value)}
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
              onChange={(e) => handleInputChange('url', e.target.value)}
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
                ? "MCP 서버 실행 명령어를 입력하세요."
                : "MCP Server의 URL을 입력하세요."
              }
            </p>
          </div>

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
                {tools.map((tool: MCPServerTool, index: number) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">{tool.name}</h3>
                        <p className="text-sm text-gray-600 mt-1">{tool.description}</p>
                        {tool.parameters.length > 0 && (
                          <div className="mt-2">
                            <p className="text-xs font-medium text-gray-700 mb-1">Parameters:</p>
                            <div className="space-y-1">
                              {tool.parameters.map((param: MCPServerProperty, paramIndex: number) => (
                                <div key={paramIndex} className="text-xs text-gray-600">
                                  • {param.name} 
                                  {param.type && <span className="text-blue-600"> ({param.type})</span>}
                                  {!param.type && <span className="text-gray-400"> (no type)</span>}
                                  {param.required && <span className="text-red-600"> (required)</span>}
                                  {param.description && ` - ${param.description}`}
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
                          {toolForm.parameters.map((param: MCPServerProperty, index: number) => (
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
