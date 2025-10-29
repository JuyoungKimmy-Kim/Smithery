"use client";

import React, { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { MCPServer, TransportType, MCPServerTool, MCPServerProperty } from "../../../../types/mcp";
import { useAuth } from "@/contexts/AuthContext";
import { useLanguage } from "@/contexts/LanguageContext";
import { PlusIcon, TrashIcon, PencilIcon, CheckCircleIcon } from "@heroicons/react/24/outline";
import TagSelector from "@/components/tag-selector";
import { apiFetch } from "@/lib/api-client";

export default function EditMCPServerPage() {
  const params = useParams();
  const router = useRouter();
  const { token, isAuthenticated } = useAuth();
  const { t } = useLanguage();
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
    config: "",
    // stdio 전용 필드
    command: "",
    args: "",
    cwd: ""
  });

  // STDIO 선택적 필드 표시 상태
  const [showStdioArgs, setShowStdioArgs] = useState(false);
  const [showStdioCwd, setShowStdioCwd] = useState(false);
  const [showStdioEnv, setShowStdioEnv] = useState(false);

  // 환경 변수 관리
  const [envVars, setEnvVars] = useState<{key: string, value: string}[]>([]);
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

  // Tool 미리보기 관련 상태
  const [previewTools, setPreviewTools] = useState<any[]>([]);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);
  const [showDuplicateModal, setShowDuplicateModal] = useState(false);
  const [duplicateTools, setDuplicateTools] = useState<{existing: MCPServerTool[], new: MCPServerTool[]}>({existing: [], new: []});
  const [pendingNewTools, setPendingNewTools] = useState<MCPServerTool[]>([]);
  const [selectedChoices, setSelectedChoices] = useState<('existing' | 'new')[]>([]);

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
      router.push('/ad-login');
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
        
        if (confirm(t('edit.restorePrompt'))) {
          setFormData(parsed.formData || formData);
          setSelectedTags(parsed.selectedTags || []);
          setTools(parsed.tools || []);
          sessionStorage.setItem(`hasAskedRestore_${params.id}`, 'true');
          console.log('자동 저장된 수정 내용을 복원했습니다.');
        } else {
          localStorage.removeItem(AUTOSAVE_KEY);
          sessionStorage.setItem(`hasAskedRestore_${params.id}`, 'true');
        }
      } else if (savedData && hasAskedRestore) {
        // 이미 복원 여부를 물어봤으면 조용히 복원
        const parsed = JSON.parse(savedData);
        setFormData(parsed.formData || formData);
        setSelectedTags(parsed.selectedTags || []);
        setTools(parsed.tools || []);
        console.log('자동 저장된 수정 내용을 조용히 복원했습니다.');
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
        console.log('Auto-saved edit.');
      } catch (error) {
        console.error('자동 저장 실패:', error);
      }
    }, 15000);

    return () => clearTimeout(timeoutId);
  }, [formData, selectedTags, tools, isDataLoaded, mcp]);

  // 다른 탭에서 localStorage 변경 감지 및 동기화
  useEffect(() => {
    if (!isDataLoaded || !mcp) return;

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
  }, [isDataLoaded, mcp]);

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
          t('edit.leaveConfirm')
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
          t('edit.leaveConfirm')
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

          // config에서 url 추출
          let urlValue = "";
          let configObj = null;
          try {
            if (typeof data.config === 'string') {
              configObj = JSON.parse(data.config);
            } else if (data.config && typeof data.config === 'object') {
              configObj = data.config;
            }
            urlValue = configObj?.url || "";
          } catch (e) {
            console.error('Failed to parse config:', e);
          }

          setFormData({
            name: data.name || "",
            github_link: data.github_link || "",
            description: data.description || "",
            tags: formatTagsToString(data.tags),
            protocol: data.protocol || "",
            url: urlValue,
            config: data.config ? (typeof data.config === 'string' ? data.config : JSON.stringify(data.config, null, 2)) : ""
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

  // 미리보기 버튼 클릭 핸들러
  const handlePreviewClick = async () => {
    if (!formData.protocol) {
      return;
    }

    try {
      if (formData.protocol === TransportType.STDIO) {
        // STDIO: Command 필수, Args/CWD 선택
        if (!formData.command.trim()) {
          return;
        }
        console.log('Previewing STDIO tools - Command:', formData.command, 'Args:', formData.args, 'CWD:', formData.cwd);
        await detectAndPreviewTools({
          url: '',
          protocol: TransportType.STDIO
        });
      } else {
        // SSE/HTTP: URL 필수
        if (!formData.url.trim()) {
          return;
        }
        console.log('Previewing tools - URL:', formData.url, 'Transport Type:', formData.protocol);
        await detectAndPreviewTools({
          url: formData.url.trim(),
          protocol: formData.protocol
        });
      }
    } catch (error) {
      console.error('미리보기 실패:', error);
      setPreviewTools([]);
    }
  };

  // 미리보기 버튼 활성화 조건
  const canPreview = (): boolean => {
    if (!formData.protocol) return false;

    if (formData.protocol === TransportType.STDIO) {
      // STDIO: Command 필수
      return formData.command.trim().length > 0;
    } else {
      // SSE/HTTP: URL 필수
      return formData.url.trim().length > 0;
    }
  };

  const requestToolsList = async (config: any) => {
    try {
      console.log('Requesting tools via backend proxy:', config);

      // stdio일 때는 command, args, cwd도 함께 전달
      const requestBody: any = {
        url: config.url,
        protocol: config.protocol
      };

      if (config.protocol === TransportType.STDIO) {
        requestBody.command = formData.command;
        requestBody.args = formData.args;
        requestBody.cwd = formData.cwd;

        // 환경 변수가 있으면 객체로 변환하여 전달
        if (envVars.length > 0) {
          const envObj: {[key: string]: string} = {};
          envVars.forEach(env => {
            if (env.key.trim()) {
              envObj[env.key.trim()] = env.value;
            }
          });
          if (Object.keys(envObj).length > 0) {
            requestBody.env = envObj;
          }
        }
      }

      const response = await fetch('/api/mcp-servers/preview-tools', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
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
      console.log('Fetching tools from MCP Server:', config.url, 'Transport Type:', config.protocol);
      await requestToolsList(config);
    } catch (error) {
      console.error('MCP Server tools 가져오기 실패:', error);
      setPreviewTools([]);
    } finally {
      setIsLoadingPreview(false);
    }
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

      // 중복된 tool 찾기
      const duplicates: {existing: MCPServerTool[], new: MCPServerTool[]} = {existing: [], new: []};
      const newToolsOnly: MCPServerTool[] = [];

      convertedTools.forEach(newTool => {
        const existingTool = tools.find(t => t.name === newTool.name);
        if (existingTool) {
          duplicates.existing.push(existingTool);
          duplicates.new.push(newTool);
        } else {
          newToolsOnly.push(newTool);
        }
      });

      // 중복이 있으면 모달 표시
      if (duplicates.existing.length > 0) {
        setDuplicateTools(duplicates);
        setPendingNewTools(newToolsOnly);
        // 기본값은 모두 'existing' (기존 것 유지)
        setSelectedChoices(new Array(duplicates.existing.length).fill('existing'));
        setShowDuplicateModal(true);
      } else {
        // 중복 없으면 바로 추가
        setTools([...tools, ...newToolsOnly]);
        alert(t('edit.toolsAdded', { count: String(newToolsOnly.length) }));
      }
    }
  };

  const handleToggleChoice = (index: number) => {
    setSelectedChoices(prev => {
      const newChoices = [...prev];
      newChoices[index] = newChoices[index] === 'existing' ? 'new' : 'existing';
      return newChoices;
    });
  };

  const handleApplyChoices = () => {
    // 선택된 tool들을 적용
    const duplicateNamesToReplace = new Set<string>();
    const toolsToAdd: MCPServerTool[] = [];

    selectedChoices.forEach((choice, index) => {
      if (choice === 'new') {
        duplicateNamesToReplace.add(duplicateTools.existing[index].name);
        toolsToAdd.push(duplicateTools.new[index]);
      }
    });

    // 교체할 tool 제거 후 새로운 것 추가
    const filteredTools = tools.filter(t => !duplicateNamesToReplace.has(t.name));
    setTools([...filteredTools, ...toolsToAdd, ...pendingNewTools]);

    setShowDuplicateModal(false);
    const totalAdded = toolsToAdd.length + pendingNewTools.length;
    alert(t('edit.toolsAdded', { count: String(totalAdded) }));
  };

  const handleCancelDuplicate = () => {
    setShowDuplicateModal(false);
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
      alert(t('edit.toolNameRequired'));
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
    if (window.confirm(t('edit.deleteToolConfirm'))) {
      const updatedTools = tools.filter((_, i) => i !== index);
      setTools(updatedTools);
    }
  };

  const handleAddParameter = () => {
    if (!parameterForm.name.trim()) {
      alert(t('edit.parameterNameRequired'));
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
      alert(t('edit.parameterNameRequired'));
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
      errors.description = t('edit.descriptionRequired');
    }
    
    if (!formData.protocol.trim()) {
      errors.protocol = t('edit.protocolRequired');
    }
    
    if (formData.url.trim() && formData.protocol !== TransportType.STDIO) {
      try {
        new URL(formData.url);
      } catch {
        errors.url = t('edit.serverUrlInvalid');
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
          throw new Error(t('edit.serverConfigInvalid'));
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
        setError(t('edit.serverConfigInvalid'));
      } else {
        setError(err instanceof Error ? err.message : t('signup.unknownError'));
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
          {t('edit.loading')}
        </h2>
      </div>
    );
  }

  if (error || !mcp) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <h2 className="text-xl text-red-600">
          {error || t('edit.notFound')}
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
                {t('edit.sessionExpired')}
              </h3>

              <div className="text-gray-600 mb-6 space-y-2">
                <p>{t('edit.draftSaved')}</p>
                <p>{t('edit.loginAgain')}</p>
              </div>

              <button
                onClick={() => router.push('/ad-login')}
                className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors font-medium"
              >
                {t('edit.ok')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Duplicate Tools Modal */}
      {showDuplicateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full mx-4 transform transition-all max-h-[85vh] overflow-y-auto">
            <div className="p-8">
              <div className="flex items-center mb-6">
                <div className="flex items-center justify-center h-12 w-12 rounded-full bg-yellow-100 mr-4">
                  <svg className="h-6 w-6 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900">
                    {t('edit.duplicateToolsTitle')}
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {t('edit.duplicateToolsDesc')}
                  </p>
                </div>
              </div>

              <div className="space-y-4 mb-6">
                {duplicateTools.existing.map((existingTool, index) => {
                  const isExistingSelected = selectedChoices[index] === 'existing';
                  const isNewSelected = selectedChoices[index] === 'new';

                  return (
                    <div key={index} className="border-2 border-gray-300 rounded-lg p-4">
                      <div className="grid grid-cols-2 gap-4">
                        {/* 기존 Tool */}
                        <div
                          className={`border-r pr-4 cursor-pointer transition-all ${
                            isExistingSelected ? 'opacity-100' : 'opacity-50'
                          }`}
                          onClick={() => handleToggleChoice(index)}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="text-sm font-semibold text-blue-700">{t('edit.existingTool')}</h4>
                            <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                              isExistingSelected
                                ? 'border-blue-600 bg-blue-600'
                                : 'border-gray-300 bg-white'
                            }`}>
                              {isExistingSelected && (
                                <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                </svg>
                              )}
                            </div>
                          </div>
                          <div className={`p-3 rounded ${
                            isExistingSelected ? 'bg-blue-100 border-2 border-blue-500' : 'bg-blue-50'
                          }`}>
                            <p className="font-medium text-gray-900">{existingTool.name}</p>
                            <p className="text-sm text-gray-600 mt-1">{existingTool.description}</p>
                            {existingTool.parameters.length > 0 && (
                              <div className="mt-2">
                                <p className="text-xs font-medium text-gray-700">Parameters: {existingTool.parameters.length}</p>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* 새로운 Tool */}
                        <div
                          className={`pl-4 cursor-pointer transition-all ${
                            isNewSelected ? 'opacity-100' : 'opacity-50'
                          }`}
                          onClick={() => handleToggleChoice(index)}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="text-sm font-semibold text-green-700">{t('edit.newTool')}</h4>
                            <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                              isNewSelected
                                ? 'border-green-600 bg-green-600'
                                : 'border-gray-300 bg-white'
                            }`}>
                              {isNewSelected && (
                                <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                </svg>
                              )}
                            </div>
                          </div>
                          <div className={`p-3 rounded ${
                            isNewSelected ? 'bg-green-100 border-2 border-green-500' : 'bg-green-50'
                          }`}>
                            <p className="font-medium text-gray-900">{duplicateTools.new[index].name}</p>
                            <p className="text-sm text-gray-600 mt-1">{duplicateTools.new[index].description}</p>
                            {duplicateTools.new[index].parameters.length > 0 && (
                              <div className="mt-2">
                                <p className="text-xs font-medium text-gray-700">Parameters: {duplicateTools.new[index].parameters.length}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="flex gap-3">
                <button
                  onClick={handleApplyChoices}
                  className="flex-1 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  {t('edit.applyChoices')}
                </button>
                <button
                  onClick={handleCancelDuplicate}
                  className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                >
                  {t('edit.cancel')}
                </button>
              </div>
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
                {t('edit.successTitle')}
              </h3>
              
              <div className="text-gray-600 mb-8 space-y-2">
                <p>{t('edit.successDesc1')}</p>
                <p>{t('edit.successDesc2')}</p>
              </div>
              
              <div className="flex gap-3">
                <button
                  onClick={handleSuccessModalClose}
                  className="flex-1 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  {t('edit.viewDetail')}
                </button>
                <button
                  onClick={handleViewMCPList}
                  className="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                >
                  {t('edit.viewMcpList')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="w-full max-w-4xl p-8 bg-white shadow-lg rounded-lg my-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-800 text-center">
            {t('edit.title')}
          </h1>
          {lastSavedTime && (
            <p className="text-xs text-gray-500 text-center mt-2">
              💾 {t('edit.autoSaved', { time: lastSavedTime.toLocaleTimeString('ko-KR') })}
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
              {t('edit.serverName')}
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
              {t('edit.githubLink')}
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
              {t('edit.description')} *
            </label>
            <textarea
              required
              rows={4}
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                validationErrors.description ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder={t('edit.descriptionPlaceholder')}
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
          
          {/* Transport Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('edit.protocol')} *
            </label>
            <select
              required
              value={formData.protocol}
              onChange={(e) => handleInputChange('protocol', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                validationErrors.protocol ? 'border-red-500' : 'border-gray-300'
              }`}
            >
              <option value="">{t('edit.protocolSelect')}</option>
              <option value={TransportType.STREAMABLE_HTTP}>Streamable HTTP</option>
              <option value={TransportType.SSE}>SSE</option>
              <option value={TransportType.STDIO}>STDIO</option>
            </select>
            {validationErrors.protocol && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.protocol}</p>
            )}
          </div>

          {/* URL - STDIO일 때는 숨김 */}
          {formData.protocol !== TransportType.STDIO && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('edit.serverUrl')}
              </label>
              <input
                type="url"
                value={formData.url}
                onChange={(e) => handleInputChange('url', e.target.value)}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  validationErrors.url ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder={t('edit.serverUrlPlaceholderHttp')}
              />
              {validationErrors.url && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.url}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                {t('edit.serverUrlHelpHttp')}
              </p>
            </div>
          )}

          {isLoadingPreview && (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-md">
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                <span className="text-blue-700">{t('edit.loadingTools')}</span>
              </div>
            </div>
          )}

          {previewTools.length > 0 && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-md">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-green-800">
                  {t('edit.toolsPreview', { count: String(previewTools.length) })}
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
                {previewTools.map((tool: any, index: number) => (
                  <div key={index} className="bg-white rounded-lg p-3 border border-green-200">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-green-900 text-sm">{tool.name}</h4>
                        <p className="text-xs text-green-700 mt-1">{tool.description || t('edit.noDescription')}</p>

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
                                    <span className="text-red-600 text-xs">{t('edit.required')}</span>
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

          {formData.url && formData.protocol && !isLoadingPreview && previewTools.length === 0 && formData.protocol !== TransportType.STDIO && (
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-md">
              <div className="flex items-center">
                <div className="text-yellow-600 mr-2">⚠️</div>
                <span className="text-yellow-700 text-sm">
                  {t('edit.connectionError')}
                </span>
              </div>
            </div>
          )}

          {/* STDIO 전용 필드들 */}
          {formData.protocol === TransportType.STDIO && (
            <>
              {/* Command - 필수 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('edit.command')} *
                </label>
                <input
                  type="text"
                  value={formData.command}
                  onChange={(e) => handleInputChange('command', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                  placeholder={t('edit.commandPlaceholder')}
                />
                <p className="mt-1 text-xs text-gray-500">
                  {t('edit.commandHelp')}
                </p>
              </div>

              {/* 선택적 필드 추가 버튼들 */}
              <div className="flex flex-wrap gap-2">
                {!showStdioArgs && (
                  <button
                    type="button"
                    onClick={() => setShowStdioArgs(true)}
                    className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
                  >
                    + {t('edit.addArguments')}
                  </button>
                )}
                {!showStdioCwd && (
                  <button
                    type="button"
                    onClick={() => setShowStdioCwd(true)}
                    className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
                  >
                    + {t('edit.addCwd')}
                  </button>
                )}
                {!showStdioEnv && (
                  <button
                    type="button"
                    onClick={() => setShowStdioEnv(true)}
                    className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
                  >
                    + {t('edit.addEnv')}
                  </button>
                )}
              </div>

              {/* Arguments - 선택적 */}
              {showStdioArgs && (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-gray-700">
                      {t('edit.arguments')}
                    </label>
                    <button
                      type="button"
                      onClick={() => {
                        setShowStdioArgs(false);
                        handleInputChange('args', '');
                      }}
                      className="text-xs text-red-600 hover:text-red-800"
                    >
                      {t('edit.remove')}
                    </button>
                  </div>
                  <input
                    type="text"
                    value={formData.args}
                    onChange={(e) => handleInputChange('args', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                    placeholder={t('edit.argumentsPlaceholder')}
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    {t('edit.argumentsHelp')}
                  </p>
                </div>
              )}

              {/* CWD - 선택적 */}
              {showStdioCwd && (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-gray-700">
                      {t('edit.cwd')}
                    </label>
                    <button
                      type="button"
                      onClick={() => {
                        setShowStdioCwd(false);
                        handleInputChange('cwd', '');
                      }}
                      className="text-xs text-red-600 hover:text-red-800"
                    >
                      {t('edit.remove')}
                    </button>
                  </div>
                  <input
                    type="text"
                    value={formData.cwd}
                    onChange={(e) => handleInputChange('cwd', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                    placeholder={t('edit.cwdPlaceholder')}
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    {t('edit.cwdHelp')}
                  </p>
                </div>
              )}

              {/* Environment Variables - 선택적 */}
              {showStdioEnv && (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-gray-700">
                      {t('edit.envVars')}
                    </label>
                    <button
                      type="button"
                      onClick={() => {
                        setShowStdioEnv(false);
                        setEnvVars([]);
                      }}
                      className="text-xs text-red-600 hover:text-red-800"
                    >
                      {t('edit.remove')}
                    </button>
                  </div>
                  <div className="space-y-2">
                    {envVars.map((env, index) => (
                      <div key={index} className="flex gap-2">
                        <input
                          type="text"
                          value={env.key}
                          onChange={(e) => {
                            const newEnvVars = [...envVars];
                            newEnvVars[index].key = e.target.value;
                            setEnvVars(newEnvVars);
                          }}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                          placeholder={t('edit.envKey')}
                        />
                        <input
                          type="text"
                          value={env.value}
                          onChange={(e) => {
                            const newEnvVars = [...envVars];
                            newEnvVars[index].value = e.target.value;
                            setEnvVars(newEnvVars);
                          }}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                          placeholder={t('edit.envValue')}
                        />
                        <button
                          type="button"
                          onClick={() => setEnvVars(envVars.filter((_, i) => i !== index))}
                          className="px-3 py-2 text-red-600 hover:text-red-800"
                        >
                          ✕
                        </button>
                      </div>
                    ))}
                    <button
                      type="button"
                      onClick={() => setEnvVars([...envVars, {key: '', value: ''}])}
                      className="w-full px-3 py-2 text-sm border-2 border-dashed border-gray-300 text-gray-600 rounded-md hover:border-gray-400 hover:text-gray-800 transition-colors"
                    >
                      + {t('edit.addEnvVar')}
                    </button>
                  </div>
                  <p className="mt-1 text-xs text-gray-500">
                    {t('edit.envHelp')}
                  </p>
                </div>
              )}
            </>
          )}

          {/* 미리보기 버튼 */}
          <div className="flex justify-center">
            <button
              type="button"
              onClick={handlePreviewClick}
              disabled={!canPreview() || isLoadingPreview}
              className={`px-6 py-2.5 rounded-lg font-medium transition-colors ${
                canPreview() && !isLoadingPreview
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              {isLoadingPreview ? (
                <span className="flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  {t('edit.loadingTools')}
                </span>
              ) : (
                t('edit.previewTools')
              )}
            </button>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('edit.serverConfig')}
            </label>
            <textarea
              rows={6}
              value={formData.config}
              onChange={(e) => handleInputChange('config', e.target.value)}
              placeholder={t('edit.serverConfigPlaceholder')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="mt-1 text-sm text-gray-500">
              {t('edit.serverConfigHelp')}
            </p>
          </div>

          <div className="border-t pt-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-800">
                {t('edit.tools', { count: String(tools.length) })}
              </h2>
              <button
                type="button"
                onClick={handleAddTool}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                <PlusIcon className="h-4 w-4" />
                {t('edit.addTool')}
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
                            <p className="text-xs font-medium text-gray-700 mb-1">{t('edit.parameters')}</p>
                            <div className="space-y-1">
                              {tool.parameters.map((param: MCPServerProperty, paramIndex: number) => (
                                <div key={paramIndex} className="text-xs text-gray-600">
                                  • {param.name} 
                                  {param.type && <span className="text-blue-600"> ({param.type})</span>}
                                  {!param.type && <span className="text-gray-400"> ({t('edit.noType')})</span>}
                                  {param.required && <span className="text-red-600"> ({t('edit.required')})</span>}
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
                    {editingToolIndex !== null ? t('edit.editTool') : t('edit.addNewTool')}
                  </h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {t('edit.toolName')} *
                      </label>
                      <input
                        type="text"
                        value={toolForm.name}
                        onChange={(e) => setToolForm(prev => ({ ...prev, name: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder={t('edit.toolNamePlaceholder')}
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {t('edit.toolDescription')} *
                      </label>
                      <textarea
                        value={toolForm.description}
                        onChange={(e) => setToolForm(prev => ({ ...prev, description: e.target.value }))}
                        rows={3}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder={t('edit.toolDescriptionPlaceholder')}
                      />
                    </div>

                    {/* Parameters */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <label className="block text-sm font-medium text-gray-700">
                          {t('edit.parameters')}
                        </label>
                        <button
                          type="button"
                          onClick={() => setShowAddParameter(true)}
                          className="text-sm text-blue-600 hover:text-blue-800"
                        >
                          + {t('edit.addParameter')}
                        </button>
                      </div>
                      
                      {toolForm.parameters.length > 0 && (
                        <div className="space-y-2 mb-2">
                          {toolForm.parameters.map((param: MCPServerProperty, index: number) => (
                            <div key={index} className="flex items-center gap-2 p-2 bg-gray-50 rounded">
                              <span className="text-sm font-medium">{param.name}</span>
                              {param.type && <span className="text-xs text-blue-600">({param.type})</span>}
                              {!param.type && <span className="text-xs text-gray-400">({t('edit.noType')})</span>}
                              {param.required && <span className="text-xs text-red-600">({t('edit.required')})</span>}
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
                            {editingParameterIndex !== null ? t('edit.editParameter') : t('edit.addParameter')}
                          </h4>
                          <div className="grid grid-cols-1 md:grid-cols-4 gap-2 mb-2">
                            <input
                              type="text"
                              placeholder={t('edit.parameterName')}
                              value={parameterForm.name}
                              onChange={(e) => setParameterForm(prev => ({ ...prev, name: e.target.value }))}
                              className="px-2 py-1 text-sm border border-gray-300 rounded"
                            />
                            <input
                              type="text"
                              placeholder={t('edit.parameterDescription')}
                              value={parameterForm.description}
                              onChange={(e) => setParameterForm(prev => ({ ...prev, description: e.target.value }))}
                              className="px-2 py-1 text-sm border border-gray-300 rounded"
                            />
                            <select
                              value={parameterForm.type}
                              onChange={(e) => setParameterForm(prev => ({ ...prev, type: e.target.value }))}
                              className="px-2 py-1 text-sm border border-gray-300 rounded"
                            >
                              <option value="">{t('edit.selectType')}</option>
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
                              {editingParameterIndex !== null ? t('edit.update') : t('edit.add')}
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
                              {t('edit.cancel')}
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
                      {editingToolIndex !== null ? t('edit.updateTool') : t('edit.addToolButton')}
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
                      {t('edit.cancel')}
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
              {t('edit.cancelButton')}
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? t('edit.updating') : t('edit.updateButton')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
