"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { MCPServer, ProtocolType, MCPServerTool, MCPServerProperty } from "../../types/mcp";
import { useAuth } from "@/contexts/AuthContext";
import { useLanguage } from "@/contexts/LanguageContext";
import { PlusIcon, TrashIcon, PencilIcon, CheckCircleIcon } from "@heroicons/react/24/outline";
import TagSelector from "@/components/tag-selector";
import { apiFetch } from "@/lib/api-client";

export default function SubmitMCPPage() {
  const router = useRouter();
  const { token, isAuthenticated } = useAuth();
  const { t } = useLanguage();
  const AUTOSAVE_KEY = 'mcp_submit_autosave';
  const hasRedirectedRef = useRef(false);
  
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
  const [isDataLoaded, setIsDataLoaded] = useState(false);
  const [lastSavedTime, setLastSavedTime] = useState<Date | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [showSessionExpiredModal, setShowSessionExpiredModal] = useState(false);

  // 폼에 내용이 있는지 확인하는 함수
  const hasFormContent = (): boolean => {
    return !!(formData.name || 
              formData.github_link || 
              formData.description || 
              selectedTags.length > 0 || 
              tools.length > 0);
  };

  // 페이지 로드 시 자동 저장된 데이터 복원
  useEffect(() => {
    try {
      // 이미 이번 세션에서 복원 여부를 물어봤는지 확인
      const hasAskedRestore = sessionStorage.getItem('hasAskedRestore');
      
      const savedData = localStorage.getItem(AUTOSAVE_KEY);
      if (savedData && !hasAskedRestore) {
        const parsed = JSON.parse(savedData);
        
        // 사용자에게 먼저 물어보고 복원
        if (confirm(t('submit.restorePrompt'))) {
          // 복원
          setFormData(parsed.formData || formData);
          setSelectedTags(parsed.selectedTags || []);
          setTools(parsed.tools || []);
          console.log('자동 저장된 데이터를 복원했습니다.');
          // 이번 세션에서 복원했다는 플래그 설정
          sessionStorage.setItem('hasAskedRestore', 'true');
        } else {
          // 사용자가 거부하면 localStorage에서 삭제
          localStorage.removeItem(AUTOSAVE_KEY);
          // 이번 세션에서 물어봤다는 플래그 설정
          sessionStorage.setItem('hasAskedRestore', 'true');
        }
      } else if (savedData && hasAskedRestore) {
        // 이미 복원 여부를 물어봤으면 조용히 복원 (confirm 없이)
        const parsed = JSON.parse(savedData);
        setFormData(parsed.formData || formData);
        setSelectedTags(parsed.selectedTags || []);
        setTools(parsed.tools || []);
      }
    } catch (error) {
      console.error('자동 저장 데이터 복원 실패:', error);
      localStorage.removeItem(AUTOSAVE_KEY);
    }
    setIsDataLoaded(true);
  }, []);

  // 폼 데이터 변경 시 자동 저장 및 미저장 변경사항 플래그 설정
  useEffect(() => {
    if (!isDataLoaded) return; // 초기 로드 시에는 저장하지 않음
    
    // 내용이 있으면 미저장 변경사항 플래그 설정
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
        console.log('Auto-saved draft.');
      } catch (error) {
        console.error('자동 저장 실패:', error);
      }
    }, 2000); // 2초 디바운스

    return () => clearTimeout(timeoutId);
  }, [formData, selectedTags, tools, isDataLoaded]);

  // 다른 탭에서 localStorage 변경 감지 및 동기화
  useEffect(() => {
    if (!isDataLoaded) return;

    const handleStorageChange = (e: StorageEvent) => {
      // 다른 탭에서 AUTOSAVE_KEY가 변경된 경우에만 처리
      if (e.key === AUTOSAVE_KEY && e.newValue) {
        try {
          const parsed = JSON.parse(e.newValue);
          const savedTime = new Date(parsed.savedAt);
          
          // 다른 탭의 변경사항으로 현재 탭 업데이트
          if (parsed.formData) {
            setFormData(parsed.formData);
          }
          if (parsed.selectedTags) {
            setSelectedTags(parsed.selectedTags);
          }
          if (parsed.tools) {
            setTools(parsed.tools);
          }
          setLastSavedTime(savedTime);
        } catch (error) {
          console.error('다른 탭의 데이터 동기화 실패:', error);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [isDataLoaded]);

  // 초기 인증 체크 (한 번만 실행)
  useEffect(() => {
    // 데이터 로드 완료 후, 인증되지 않았고, 아직 리다이렉트하지 않았고, 모달이 표시 중이 아니면
    if (isDataLoaded && !isAuthenticated && !hasRedirectedRef.current && !showSessionExpiredModal) {
      hasRedirectedRef.current = true;
      router.push('/login');
    }
  }, [isDataLoaded, isAuthenticated, showSessionExpiredModal, router]);

  // 페이지 이탈 방지 (브라우저 닫기/새로고침)
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges && !isSubmitting) {
        e.preventDefault();
        e.returnValue = ''; // Chrome에서 필요
        return t('submit.leaveConfirm');
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasUnsavedChanges, isSubmitting]);

  // 페이지 이탈 방지 (뒤로가기 버튼)
  useEffect(() => {
    // 페이지 진입 시 히스토리에 현재 상태 추가
    if (hasUnsavedChanges) {
      window.history.pushState({ page: 'submit' }, '');
    }

    const handlePopState = (e: PopStateEvent) => {
      if (hasUnsavedChanges && !isSubmitting) {
        const confirmLeave = window.confirm(
          '작성 중인 내용이 자동 저장되었습니다.\n페이지를 벗어나시겠습니까?'
        );
        
        if (!confirmLeave) {
          // 사용자가 취소하면 다시 현재 페이지로 이동
          window.history.pushState({ page: 'submit' }, '');
        } else {
          // 사용자가 확인하면 뒤로가기 진행 (변경사항 플래그 해제)
          setHasUnsavedChanges(false);
        }
      }
    };

    window.addEventListener('popstate', handlePopState);
    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
  }, [hasUnsavedChanges, isSubmitting]);

  // 페이지 이탈 방지 (내부 링크 클릭 - 홈 버튼 등)
  useEffect(() => {
    const handleLinkClick = (e: MouseEvent) => {
      if (!hasUnsavedChanges || isSubmitting) return;
      
      const target = e.target as HTMLElement;
      
      // navbar 또는 외부 링크만 감지 (submit 페이지 내부 요소 제외)
      const isNavbarLink = target.closest('nav a, nav button');
      const linkElement = target.closest('a');
      
      if (isNavbarLink || (linkElement && !linkElement.closest('.submit-page-content'))) {
        e.preventDefault();
        e.stopPropagation();
        
        const confirmLeave = window.confirm(
          t('submit.leaveConfirm')
        );
        
        if (confirmLeave) {
          setHasUnsavedChanges(false);
          // 확인 후 링크 이동
          if (linkElement instanceof HTMLAnchorElement) {
            const href = linkElement.getAttribute('href');
            if (href) {
              // setTimeout으로 상태 업데이트 후 이동
              setTimeout(() => {
                router.push(href);
              }, 0);
            }
          } else if (isNavbarLink instanceof HTMLButtonElement) {
            // Register 버튼 등의 onClick 다시 실행
            setTimeout(() => {
              (isNavbarLink as HTMLButtonElement).click();
            }, 0);
          }
        }
      }
    };

    // capture phase에서 이벤트를 먼저 잡음
    document.addEventListener('click', handleLinkClick, true);
    return () => {
      document.removeEventListener('click', handleLinkClick, true);
    };
  }, [hasUnsavedChanges, isSubmitting, router]);

  // 세션 만료 이벤트 리스너
  useEffect(() => {
    const handleSessionExpired = () => {
      console.log('Session expired event received, showing modal...');
      setShowSessionExpiredModal(true);
    };

    window.addEventListener('session-expired', handleSessionExpired);
    return () => {
      window.removeEventListener('session-expired', handleSessionExpired);
    };
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
      alert(t('submit.toolNameRequired'));
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
    if (window.confirm(t('submit.deleteToolConfirm'))) {
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
      alert(t('submit.toolsAdded', { count: String(convertedTools.length) }));
    }
  };

  const validateForm = () => {
    const errors: {[key: string]: string} = {};
    
    if (!formData.name.trim()) {
              errors.name = t('submit.serverNameRequired');
    }
    
    
    if (!formData.github_link.trim()) {
      errors.github_link = t('submit.githubLinkRequired');
    } else if (!formData.github_link.startsWith('https://github.com/')) {
      errors.github_link = t('submit.githubLinkInvalid');
    }
    
    if (!formData.description.trim()) {
      errors.description = t('submit.descriptionRequired');
    }
    
    if (!formData.protocol.trim()) {
      errors.protocol = t('submit.protocolRequired');
    }
    
    if (formData.url.trim() && formData.protocol !== ProtocolType.STDIO) {
      if (!isValidUrl(formData.url)) {
        errors.url = t('submit.serverUrlInvalid');
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
      setError(t('submit.signInRequired'));
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
          throw new Error(t('submit.serverConfigInvalid'));
        }
      } else if (formData.url.trim()) {
        config = { url: formData.url.trim() };
      }

      const mcpServerData = {
        name: formData.name.trim(),
        github_link: formData.github_link.trim(),
        description: formData.description.trim(),
        tags: selectedTags.join(', '),
        protocol: formData.protocol.trim(),
        config: config,
        tools: tools
      };


      const response = await apiFetch('/api/mcps', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        requiresAuth: true,
        body: JSON.stringify(mcpServerData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create MCP server');
      }

      const result = await response.json();
      
      // 제출 성공 시 자동 저장 데이터 삭제 및 플래그 해제
      localStorage.removeItem(AUTOSAVE_KEY);
      sessionStorage.removeItem('hasAskedRestore'); // 세션 플래그도 삭제
      setHasUnsavedChanges(false);
      console.log('제출 완료. 자동 저장 데이터를 삭제했습니다.');
      
      setShowSuccessModal(true);
    } catch (err) {
      if (err instanceof Error && err.message.includes('JSON')) {
        setError(t('submit.serverConfigInvalid'));
      } else {
        setError(err instanceof Error ? err.message : t('signup.unknownError'));
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

  // 세션 만료 모달이 표시 중이 아니면서 인증되지 않은 경우에만 로딩 표시
  if (!isAuthenticated && !showSessionExpiredModal) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">{t('submit.checkingAuth')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center submit-page-content">
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
                {t('submit.sessionExpired')}
              </h3>
              
              <div className="text-gray-600 mb-6 space-y-2">
                <p>{t('submit.draftSaved')}</p>
                <p>{t('submit.loginAgain')}</p>
              </div>
              
              <button
                onClick={() => router.push('/login')}
                className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors font-medium"
              >
                {t('submit.ok')}
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
                {t('submit.successTitle')}
              </h3>
              
              <div className="text-gray-600 mb-8 space-y-2">
                <p>{t('submit.successDesc1')}</p>
                <p>{t('submit.successDesc2')}</p>
              </div>
              
              <div className="flex gap-3">
                <button
                  onClick={handleViewMCPList}
                  className="flex-1 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  {t('submit.viewMcpList')}
                </button>
                <button
                  onClick={handleViewMyPage}
                  className="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                >
                  {t('submit.viewMyPage')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="w-full max-w-4xl p-8 bg-white shadow-lg rounded-lg my-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-800 text-center">
            {t('submit.title')}
          </h1>
          {lastSavedTime && (
            <p className="text-xs text-gray-500 text-center mt-2">
              💾 {t('submit.autoSaved', { time: lastSavedTime.toLocaleTimeString('ko-KR') })}
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
              {t('submit.serverName')} *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                validationErrors.name ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder={t('submit.serverNamePlaceholder')}
            />
            {validationErrors.name && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.name}</p>
            )}
          </div>
          

          {/* GitHub Link */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('submit.githubLink')} *
            </label>
            <input
              type="url"
              required
              value={formData.github_link}
              onChange={(e) => handleInputChange('github_link', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                validationErrors.github_link ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder={t('submit.githubLinkPlaceholder')}
            />
            {validationErrors.github_link && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.github_link}</p>
            )}
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('submit.description')} *
            </label>
            <textarea
              required
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              rows={4}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                validationErrors.description ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder={t('submit.descriptionPlaceholder')}
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
              {t('submit.protocol')} *
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
              <option value="">{t('submit.protocolSelect')}</option>
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
              {t('submit.serverUrl')}
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
              placeholder={formData.protocol === ProtocolType.STDIO ? t('submit.serverUrlPlaceholderStdio') : t('submit.serverUrlPlaceholderHttp')}
            />
            {validationErrors.url && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.url}</p>
            )}
            <p className="mt-1 text-xs text-gray-500">
              {formData.protocol === ProtocolType.STDIO 
                ? t('submit.serverUrlHelpStdio')
                : t('submit.serverUrlHelpHttp')
              }
            </p>
          </div>

          {/* Server Config */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('submit.serverConfig')}
            </label>
            <textarea
              value={formData.config}
              onChange={(e) => handleInputChange('config', e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={t('submit.serverConfigPlaceholder')}
            />
            <p className="mt-1 text-xs text-gray-500">
              {t('submit.serverConfigHelp')}
            </p>
          </div>

          {isLoadingPreview && (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-md">
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                <span className="text-blue-700">{t('submit.loadingTools')}</span>
              </div>
            </div>
          )}

          {previewTools.length > 0 && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-md">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-green-800">
                  {t('submit.toolsPreview', { count: String(previewTools.length) })}
                </h3>
                <button
                  type="button"
                  onClick={handleUsePreviewTools}
                  className="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 transition-colors"
                >
                  {t('submit.addAllTools')}
                </button>
              </div>
              <div className="space-y-3">
                {previewTools.map((tool: any, index: number) => (
                  <div key={index} className="bg-white rounded-lg p-3 border border-green-200">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-green-900 text-sm">{tool.name}</h4>
                        <p className="text-xs text-green-700 mt-1">{tool.description || t('submit.noDescription')}</p>
                        
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
                                    <span className="text-red-600 text-xs">{t('submit.required')}</span>
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
                  {t('submit.connectionError')}
                </span>
              </div>
            </div>
          )}

          {formData.protocol === ProtocolType.STDIO && (
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-md">
              <div className="flex items-center">
                <div className="text-yellow-600 mr-2">⚠️</div>
                <div className="text-yellow-700 text-sm">
                  <p className="font-medium mb-1">{t('submit.stdioWarning')}</p>
                  <p>{t('submit.stdioWarningDesc1')}</p>
                  <p>{t('submit.stdioWarningDesc2')}</p>
                </div>
              </div>
            </div>
          )}

          <div className="border-t pt-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-800">
                {t('submit.tools', { count: String(tools.length) })}
              </h2>
              <button
                type="button"
                onClick={handleAddTool}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                <PlusIcon className="h-4 w-4" />
                {t('submit.addTool')}
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
                        {tool.parameters && tool.parameters.length > 0 && (
                          <div className="mt-2">
                            <p className="text-xs font-medium text-gray-700 mb-1">{t('submit.parameters')}</p>
                            <div className="space-y-1">
                              {tool.parameters.map((param: MCPServerProperty, paramIndex: number) => (
                                <div key={paramIndex} className="text-xs text-gray-600">
                                  • {param.name} 
                                  {param.type && <span className="text-blue-600"> ({param.type})</span>}
                                  {param.required && <span className="text-red-600"> ({t('submit.required')})</span>}
                                  {param.description && ` - ${param.description}`}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        {tool.inputSchema?.properties && Object.keys(tool.inputSchema.properties).length > 0 && (
                          <div className="mt-2">
                            <p className="text-xs font-medium text-gray-700 mb-1">{t('submit.parameters')}</p>
                            <div className="space-y-1">
                              {Object.entries(tool.inputSchema.properties).map(([paramName, paramInfo]: [string, any]) => (
                                <div key={paramName} className="text-xs text-gray-600">
                                  • {paramName} 
                                  {paramInfo.type && <span className="text-blue-600"> ({paramInfo.type})</span>}
                                  {tool.inputSchema?.required?.includes(paramName) && <span className="text-red-600"> ({t('submit.required')})</span>}
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
                    {editingToolIndex !== null ? t('submit.editTool') : t('submit.addNewTool')}
                  </h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {t('submit.toolName')} *
                      </label>
                      <input
                        type="text"
                        value={toolForm.name}
                        onChange={(e) => setToolForm(prev => ({ ...prev, name: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder={t('submit.toolNamePlaceholder')}
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {t('submit.toolDescription')} *
                      </label>
                      <textarea
                        value={toolForm.description}
                        onChange={(e) => setToolForm(prev => ({ ...prev, description: e.target.value }))}
                        rows={3}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder={t('submit.toolDescriptionPlaceholder')}
                      />
                    </div>

                    {/* Parameters */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <label className="block text-sm font-medium text-gray-700">
                          {t('submit.parameters')}
                        </label>
                        <button
                          type="button"
                          onClick={() => setShowAddParameter(true)}
                          className="text-sm text-blue-600 hover:text-blue-800"
                        >
                          + {t('submit.addParameter')}
                        </button>
                      </div>
                      
                      {toolForm.parameters.length > 0 && (
                        <div className="space-y-2 mb-2">
                          {toolForm.parameters.map((param: MCPServerProperty, index: number) => (
                            <div key={index} className="flex items-center gap-2 p-2 bg-gray-50 rounded">
                              <span className="text-sm font-medium">{param.name}</span>
                              {param.type && <span className="text-xs text-blue-600">({param.type})</span>}
                              {!param.type && <span className="text-xs text-gray-400">({t('submit.noType')})</span>}
                              {param.required && <span className="text-xs text-red-600">({t('submit.required')})</span>}
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
                            {editingParameterIndex !== null ? t('submit.editParameter') : t('submit.addParameter')}
                          </h4>
                          <div className="grid grid-cols-1 md:grid-cols-4 gap-2 mb-2">
                            <input
                              type="text"
                              placeholder={t('submit.parameterName')}
                              value={parameterForm.name}
                              onChange={(e) => setParameterForm(prev => ({ ...prev, name: e.target.value }))}
                              className="px-2 py-1 text-sm border border-gray-300 rounded"
                            />
                            <input
                              type="text"
                              placeholder={t('submit.parameterDescription')}
                              value={parameterForm.description}
                              onChange={(e) => setParameterForm(prev => ({ ...prev, description: e.target.value }))}
                              className="px-2 py-1 text-sm border border-gray-300 rounded"
                            />
                            <select
                              value={parameterForm.type}
                              onChange={(e) => setParameterForm(prev => ({ ...prev, type: e.target.value }))}
                              className="px-2 py-1 text-sm border border-gray-300 rounded"
                            >
                              <option value="">{t('submit.selectType')}</option>
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
                              {editingParameterIndex !== null ? t('submit.update') : t('submit.add')}
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
                              {t('submit.cancel')}
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
                      {editingToolIndex !== null ? t('submit.updateTool') : t('submit.addToolButton')}
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
                      {t('submit.cancel')}
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
            {isSubmitting ? t('submit.submitting') : t('submit.submitButton')}
          </button>
        </form>
      </div>
    </div>
  );
}
