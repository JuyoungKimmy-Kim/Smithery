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
  ClipboardDocumentIcon,
  CheckIcon,
  MegaphoneIcon,
  ArrowPathIcon,
} from "@heroicons/react/24/outline";
import { CheckCircleIcon, XCircleIcon, QuestionMarkCircleIcon } from "@heroicons/react/24/solid";
import { MCPServer } from "@/types/mcp";
import { useAuth } from "@/contexts/AuthContext";
import Comments from "@/components/comments";
import MCPCapabilitiesTabs from "@/components/mcp-capabilities-tabs";
import { apiFetch } from "@/lib/api-client";

export default function MCPServerDetail() {
  const params = useParams();
  const router = useRouter();
  const { user, isAuthenticated, isAdmin, token } = useAuth();
  const [mcp, setMcp] = useState<MCPServer | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isConfigCopied, setIsConfigCopied] = useState(false);
  const [showAnnouncementModal, setShowAnnouncementModal] = useState(false);
  const [announcementText, setAnnouncementText] = useState("");
  const [isUpdatingAnnouncement, setIsUpdatingAnnouncement] = useState(false);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);
  const [lastHealthCheckTime, setLastHealthCheckTime] = useState<number>(0);
  const [remainingCooldown, setRemainingCooldown] = useState<number>(0);

  const handleCopyConfig = async () => {
    if (!mcp?.config) return;
    
    try {
      const configString = JSON.stringify(mcp.config, null, 2);
      await navigator.clipboard.writeText(configString);
      setIsConfigCopied(true);
      setTimeout(() => setIsConfigCopied(false), 2000); // 2초 후 복사 상태 초기화
    } catch (error) {
      console.error('Failed to copy config:', error);
      // 클립보드 API가 지원되지 않는 경우 fallback
      const textArea = document.createElement('textarea');
      textArea.value = JSON.stringify(mcp.config, null, 2);
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setIsConfigCopied(true);
      setTimeout(() => setIsConfigCopied(false), 2000);
    }
  };

  const handleAddAnnouncement = () => {
    setAnnouncementText(mcp?.announcement || "");
    setShowAnnouncementModal(true);
  };

  const handleSaveAnnouncement = async () => {
    if (!mcp) return;
    
    setIsUpdatingAnnouncement(true);
    
    try {
      const response = await apiFetch(`/api/mcps/${mcp.id}/announcement`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          announcement: announcementText.trim() || null
        }),
        requiresAuth: true,
      });
      
      if (response.ok) {
        const updatedMCP = await response.json();
        setMcp(updatedMCP);
        setShowAnnouncementModal(false);
        setAnnouncementText("");
      } else {
        const errorData = await response.json();
        console.error('API Error:', errorData);
        throw new Error(errorData.detail || `HTTP ${response.status}: Failed to update announcement`);
      }
    } catch (error) {
      console.error('Announcement update error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      alert(`Failed to update announcement: ${errorMessage}`);
    } finally {
      setIsUpdatingAnnouncement(false);
    }
  };

  const handleDeleteAnnouncement = async () => {
    if (!mcp) return;
    
    const confirmed = window.confirm("Are you sure you want to delete the announcement?");
    if (!confirmed) return;
    
    setIsUpdatingAnnouncement(true);
    
    try {
      const response = await apiFetch(`/api/mcps/${mcp.id}/announcement`, {
        method: 'DELETE',
        requiresAuth: true,
      });
      
      if (response.ok) {
        const updatedMCP = await response.json();
        setMcp(updatedMCP);
      } else {
        const errorData = await response.json();
        console.error('API Error:', errorData);
        throw new Error(errorData.detail || `HTTP ${response.status}: Failed to delete announcement`);
      }
    } catch (error) {
      console.error('Announcement delete error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      alert(`Failed to delete announcement: ${errorMessage}`);
    } finally {
      setIsUpdatingAnnouncement(false);
    }
  };

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

  const handleHealthCheck = async () => {
    if (!mcp || isCheckingHealth || remainingCooldown > 0) return;

    setIsCheckingHealth(true);

    try {
      // Start health check (returns immediately)
      const response = await fetch(`/api/mcp-servers/${mcp.id}/health-check`, {
        method: 'POST',
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Health check started:', result);

        // Poll for results (check every 2 seconds, max 10 times = 20 seconds)
        let pollCount = 0;
        const maxPolls = 10;
        const initialLastCheck = mcp.last_health_check;

        console.log('Starting polling with initial last_health_check:', initialLastCheck);

        const pollInterval = setInterval(async () => {
          pollCount++;
          console.log(`Poll attempt ${pollCount}/${maxPolls}`);

          try {
            // Fetch updated server data
            const serverResponse = await fetch(`/api/mcps/${mcp.id}`, {
              cache: 'no-store',
              headers: {
                'Cache-Control': 'no-cache',
              }
            });

            if (serverResponse.ok) {
              const serverData = await serverResponse.json();
              console.log('Polled server data:', {
                health_status: serverData.health_status,
                last_health_check: serverData.last_health_check,
                initial_last_check: initialLastCheck,
                changed: serverData.last_health_check !== initialLastCheck
              });

              // Check if health status was updated (compare with initial value)
              if (serverData.last_health_check && serverData.last_health_check !== initialLastCheck) {
                console.log('Health check completed! Status:', serverData.health_status);

                // Update MCP state with new health info
                setMcp({
                  ...mcp,
                  health_status: serverData.health_status,
                  last_health_check: serverData.last_health_check,
                });

                // Stop polling
                clearInterval(pollInterval);
                setIsCheckingHealth(false);

                // Set cooldown (20 seconds)
                const now = Date.now();
                setLastHealthCheckTime(now);
                setRemainingCooldown(20000);
              } else if (pollCount >= maxPolls) {
                // Timeout after max polls
                console.log('Health check timeout - no update after', maxPolls, 'attempts');
                console.log('Last backend response:', serverData);
                clearInterval(pollInterval);
                setIsCheckingHealth(false);
                alert('Health check is taking longer than expected. Please refresh the page later.');
              }
            } else {
              console.error('Polling failed with status:', serverResponse.status);
            }
          } catch (pollError) {
            console.error('Polling error:', pollError);
          }
        }, 2000);

      } else {
        const errorData = await response.json();
        alert(`Health check failed: ${errorData.detail || errorData.error || 'Unknown error'}`);
        setIsCheckingHealth(false);
      }
    } catch (error) {
      console.error('Health check error:', error);
      alert('Failed to perform health check');
      setIsCheckingHealth(false);
    }
  };

  // Cooldown timer effect
  useEffect(() => {
    if (remainingCooldown <= 0) return;

    const interval = setInterval(() => {
      const now = Date.now();
      const elapsed = now - lastHealthCheckTime;
      const remaining = Math.max(0, 20000 - elapsed);

      setRemainingCooldown(remaining);

      if (remaining === 0) {
        clearInterval(interval);
      }
    }, 100);

    return () => clearInterval(interval);
  }, [remainingCooldown, lastHealthCheckTime]);

  const handleDelete = async () => {
    if (!mcp) return;
    
    const confirmed = window.confirm(
      `Are you sure you want to delete "${mcp.name}"? This action cannot be undone.`
    );
    
    if (!confirmed) return;
    
    setIsDeleting(true);
    
    try {
      const response = await apiFetch(`/api/mcps/${mcp.id}`, {
        method: 'DELETE',
        requiresAuth: true,
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
    <div className="min-h-screen bg-gray-50">
      {/* Announcement Banner - Top of Page */}
      {mcp.announcement && (
        <div className="bg-yellow-100 border-b-2 border-yellow-300">
          <div className="container mx-auto px-4 max-w-6xl py-4">
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3 flex-1">
                <MegaphoneIcon className="h-6 w-6 text-black mt-1 flex-shrink-0" />
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-black mb-2">공지사항</h3>
                  <p className="text-black whitespace-pre-wrap">{mcp.announcement}</p>
                </div>
              </div>
              {isOwner && (
                <div className="flex gap-2 ml-4 flex-shrink-0">
                  <button
                    onClick={handleAddAnnouncement}
                    className="px-3 py-1 bg-yellow-600 text-white text-sm rounded-md hover:bg-yellow-700 transition-colors flex items-center gap-1"
                    disabled={isUpdatingAnnouncement}
                  >
                    Edit
                  </button>
                  <button
                    onClick={handleDeleteAnnouncement}
                    className="px-3 py-1 bg-red-600 text-white text-sm rounded-md hover:bg-red-700 transition-colors flex items-center gap-1"
                    disabled={isUpdatingAnnouncement}
                  >
                    Delete
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      
      <div className="container mx-auto px-4 max-w-6xl py-8">
        {/* Header Section */}
        <div className="bg-white rounded-lg shadow-sm p-8 mb-8">
          <div className="flex items-start justify-between mb-6">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-4">
                <h1 className="text-3xl font-bold text-gray-900">
                  {mcp.name}
                </h1>
                {/* Health Status - 모든 상태 표시 */}
                {mcp.health_status && (
                  <div className="flex items-center gap-2">
                    {mcp.health_status === 'healthy' ? (
                      <>
                        <CheckCircleIcon className="h-5 w-5 text-green-500" />
                        <span className="text-sm font-medium text-green-700">Active</span>
                      </>
                    ) : mcp.health_status === 'unhealthy' ? (
                      <>
                        <XCircleIcon className="h-5 w-5 text-red-500" />
                        <span className="text-sm font-medium text-red-700">Inactive</span>
                      </>
                    ) : (
                      <>
                        <QuestionMarkCircleIcon className="h-5 w-5 text-gray-400" />
                        <span className="text-sm font-medium text-gray-600">Unknown</span>
                      </>
                    )}
                    <button
                      onClick={handleHealthCheck}
                      disabled={isCheckingHealth || remainingCooldown > 0}
                      className={`p-1 rounded-full transition-colors ${
                        isCheckingHealth || remainingCooldown > 0
                          ? 'text-gray-300 cursor-not-allowed'
                          : 'text-gray-500 hover:text-blue-600 hover:bg-blue-50'
                      }`}
                      title="Refresh health status"
                    >
                      <ArrowPathIcon className={`h-4 w-4 ${isCheckingHealth ? 'animate-spin' : ''}`} />
                    </button>
                    {remainingCooldown > 0 && (
                      <span className="text-xs text-gray-500">
                        ({Math.ceil(remainingCooldown / 1000)}s)
                      </span>
                    )}
                  </div>
                )}
              </div>
              {/* Last health check time */}
              {mcp.last_health_check && (
                <p className="text-xs text-gray-500 mb-4">
                  Last checked: {new Date(mcp.last_health_check).toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' })}
                </p>
              )}
              <p className="text-lg text-gray-600 mb-6">
                {mcp.description}
              </p>

              {/* 공지사항 추가 버튼 - 공지사항이 없을 때만 표시 */}
              {isOwner && !mcp.announcement && (
                <div className="mb-4">
                  <button 
                    className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 transition-colors flex items-center gap-2"
                    onClick={handleAddAnnouncement}
                    disabled={isUpdatingAnnouncement}
                  >
                    <ClipboardDocumentIcon className="h-4 w-4" />
                    공지사항 추가
                  </button>
                </div>
              )}

              <div className="flex items-center gap-6 text-sm text-gray-600 flex-wrap">
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


        {/* Tools, Prompts & Resources Tabs Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          {/* Capabilities Tabs (Left - 2 columns) */}
          <div className="md:col-span-2">
            <MCPCapabilitiesTabs
              tools={mcp.tools || []}
              prompts={mcp.prompts || []}
              resources={mcp.resources || []}
            />
          </div>

          {/* Config (Right - 1 column) */}
          <div>
            <div className="bg-white rounded-lg shadow-sm p-8">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                  <WrenchScrewdriverIcon className="h-6 w-6 text-blue-500" />
                  <h2 className="text-2xl font-bold text-gray-900">
                    Server Config
                  </h2>
                </div>
                <button
                  onClick={handleCopyConfig}
                  className={`px-3 py-2 text-sm font-medium rounded-md transition-colors flex items-center gap-2 ${
                    isConfigCopied
                      ? 'bg-green-100 text-green-800 border border-green-300'
                      : 'bg-gray-100 text-gray-700 border border-gray-300 hover:bg-gray-200'
                  }`}
                  title="Copy server config to clipboard"
                >
                  {isConfigCopied ? (
                    <>
                      <CheckIcon className="h-4 w-4" />
                      Copied
                    </>
                  ) : (
                    <>
                      <ClipboardDocumentIcon className="h-4 w-4" />
                      Copy
                    </>
                  )}
                </button>
              </div>
              <pre className="bg-gray-100 rounded p-4 text-xs overflow-x-auto">
                {JSON.stringify(mcp.config, null, 2)}
              </pre>
            </div>
          </div>
        </div>

        {/* Metadata Section */}
        <div className="bg-white rounded-lg shadow-sm p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            등록 정보
          </h2>
          
          <div className="grid gap-4 md:grid-cols-2">       
            <div>
              <p className="text-sm font-medium text-gray-600">
                Owner
              </p>
              {mcp.owner ? (
                <button 
                  className="text-blue-600 hover:text-blue-800 hover:underline"
                  onClick={() => router.push(`/user/${mcp.owner?.username}`)}
                >
                  {mcp.owner.username}
                </button>
              ) : (
                <p className="text-gray-900">Unknown</p>
              )}
            </div>
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

        {/* 댓글 섹션 */}
        <div className="mt-8">
          <Comments mcpServerId={parseInt(mcp.id)} />
        </div>
      </div>

      {/* Announcement Modal */}
      {showAnnouncementModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              {mcp.announcement ? "Edit Announcement" : "Add Announcement"}
            </h3>
            
            <textarea
              value={announcementText}
              onChange={(e) => setAnnouncementText(e.target.value)}
              placeholder="Enter your announcement here..."
              className="w-full h-32 p-3 border border-gray-300 rounded-md resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              maxLength={1000}
            />
            
            <div className="text-sm text-gray-500 mt-2">
              {announcementText.length}/1000 characters
            </div>
            
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => {
                  setShowAnnouncementModal(false);
                  setAnnouncementText("");
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                disabled={isUpdatingAnnouncement}
              >
                Cancel
              </button>
              <button
                onClick={handleSaveAnnouncement}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
                disabled={isUpdatingAnnouncement}
              >
                {isUpdatingAnnouncement ? "Saving..." : "Save"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 