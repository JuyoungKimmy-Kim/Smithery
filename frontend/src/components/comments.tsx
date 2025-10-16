"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { apiFetch } from "@/lib/api-client";
import {
  ChatBubbleLeftIcon,
  PencilIcon,
  TrashIcon,
  PaperAirplaneIcon,
  CheckIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";

interface Comment {
  id: number;
  content: string;
  is_deleted: boolean;
  user_id: number;
  created_at: string;
  updated_at: string;
  user_nickname: string;
}

interface CommentsProps {
  mcpServerId: number;
}

export default function Comments({ mcpServerId }: CommentsProps) {
  const { user, isAuthenticated, token } = useAuth();
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [editingCommentId, setEditingCommentId] = useState<number | null>(null);
  const [editingContent, setEditingContent] = useState("");
  const [commentCount, setCommentCount] = useState(0);

  // 댓글 목록 조회
  const fetchComments = async () => {
    try {
      const response = await fetch(`/api/comments/mcp-servers/${mcpServerId}`);
      if (response.ok) {
        const data = await response.json();
        setComments(data);
      }
    } catch (error) {
      console.error("댓글 조회 오류:", error);
    } finally {
      setLoading(false);
    }
  };

  // 댓글 수 조회
  const fetchCommentCount = async () => {
    try {
      const response = await fetch(`/api/comments/mcp-servers/${mcpServerId}/count`);
      if (response.ok) {
        const data = await response.json();
        setCommentCount(data.count);
      }
    } catch (error) {
      console.error("댓글 수 조회 오류:", error);
    }
  };

  useEffect(() => {
    fetchComments();
    fetchCommentCount();
  }, [mcpServerId]);

  // 댓글 작성
  const handleSubmitComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim() || !isAuthenticated) return;

    setSubmitting(true);
    try {
      const response = await apiFetch(`/api/comments/mcp-servers/${mcpServerId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        requiresAuth: true,
        body: JSON.stringify({ content: newComment.trim() }),
      });

      if (response.ok) {
        setNewComment("");
        fetchComments();
        fetchCommentCount();
      } else {
        const errorData = await response.json();
        alert(`댓글 작성 실패: ${errorData.detail || "알 수 없는 오류"}`);
      }
    } catch (error) {
      console.error("댓글 작성 오류:", error);
      alert("댓글 작성 중 오류가 발생했습니다.");
    } finally {
      setSubmitting(false);
    }
  };

  // 댓글 수정
  const handleEditComment = async (commentId: number) => {
    if (!editingContent.trim()) return;

    try {
      const response = await apiFetch(`/api/comments/${commentId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        requiresAuth: true,
        body: JSON.stringify({ content: editingContent.trim() }),
      });

      if (response.ok) {
        setEditingCommentId(null);
        setEditingContent("");
        fetchComments();
      } else {
        const errorData = await response.json();
        alert(`댓글 수정 실패: ${errorData.detail || "알 수 없는 오류"}`);
      }
    } catch (error) {
      console.error("댓글 수정 오류:", error);
      alert("댓글 수정 중 오류가 발생했습니다.");
    }
  };

  // 댓글 삭제
  const handleDeleteComment = async (commentId: number) => {
    if (!confirm("댓글을 삭제하시겠습니까?")) return;

    try {
      const response = await apiFetch(`/api/comments/${commentId}`, {
        method: "DELETE",
        requiresAuth: true,
      });

      if (response.ok) {
        fetchComments();
        fetchCommentCount();
      } else {
        const errorData = await response.json();
        alert(`댓글 삭제 실패: ${errorData.detail || "알 수 없는 오류"}`);
      }
    } catch (error) {
      console.error("댓글 삭제 오류:", error);
      alert("댓글 삭제 중 오류가 발생했습니다.");
    }
  };

  // 수정 모드 시작
  const startEditing = (comment: Comment) => {
    setEditingCommentId(comment.id);
    setEditingContent(comment.content);
  };

  // 수정 취소
  const cancelEditing = () => {
    setEditingCommentId(null);
    setEditingContent("");
  };

  // 날짜 포맷팅
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) {
      return "방금 전";
    } else if (diffInHours < 24) {
      return `${diffInHours}시간 전`;
    } else {
      return date.toLocaleDateString("ko-KR");
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-8">
      <div className="flex items-center gap-2 mb-6">
        <ChatBubbleLeftIcon className="h-6 w-6 text-blue-500" />
        <h2 className="text-2xl font-bold text-gray-900">댓글</h2>
        <span className="text-sm text-gray-500">({commentCount})</span>
      </div>

      {/* 댓글 작성 폼 */}
      {isAuthenticated ? (
        <form onSubmit={handleSubmitComment} className="mb-6">
          <div className="flex gap-3">
            <div className="flex-1">
              <textarea
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="댓글을 작성해주세요..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows={3}
                maxLength={500}
              />
              <div className="text-right text-xs text-gray-500 mt-1">
                {newComment.length}/500
              </div>
            </div>
            <button
              type="submit"
              disabled={!newComment.trim() || submitting}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {submitting ? (
                "작성 중..."
              ) : (
                <>
                  <PaperAirplaneIcon className="h-4 w-4" />
                  작성
                </>
              )}
            </button>
          </div>
        </form>
      ) : (
        <div className="mb-6 p-4 bg-gray-50 rounded-md text-center text-gray-600">
          댓글을 작성하려면 로그인해주세요.
        </div>
      )}

      {/* 댓글 목록 */}
      {loading ? (
        <div className="text-center py-8 text-gray-500">댓글을 불러오는 중...</div>
      ) : comments.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          아직 댓글이 없습니다. 첫 번째 댓글을 작성해보세요!
        </div>
      ) : (
        <div className="space-y-4">
          {comments.map((comment) => (
            <div key={comment.id} className="border-b border-gray-100 pb-4 last:border-b-0">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-medium text-gray-900">
                      {comment.user_nickname}
                    </span>
                    <span className="text-sm text-gray-500">
                      {formatDate(comment.created_at)}
                    </span>
                    {comment.updated_at !== comment.created_at && (
                      <span className="text-xs text-gray-400">(수정됨)</span>
                    )}
                  </div>
                  
                  {editingCommentId === comment.id ? (
                    <div className="space-y-2">
                      <textarea
                        value={editingContent}
                        onChange={(e) => setEditingContent(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                        rows={2}
                        maxLength={500}
                      />
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEditComment(comment.id)}
                          className="px-3 py-1 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 flex items-center gap-1"
                        >
                          <CheckIcon className="h-3 w-3" />
                          저장
                        </button>
                        <button
                          onClick={cancelEditing}
                          className="px-3 py-1 bg-gray-500 text-white text-sm rounded-md hover:bg-gray-600 flex items-center gap-1"
                        >
                          <XMarkIcon className="h-3 w-3" />
                          취소
                        </button>
                      </div>
                    </div>
                  ) : (
                    <p className={`whitespace-pre-wrap ${
                      comment.is_deleted 
                        ? 'text-gray-500 italic' 
                        : 'text-gray-700'
                    }`}>
                      {comment.content}
                    </p>
                  )}
                </div>
                
                {/* 댓글 작성자만 수정/삭제 가능 (삭제된 댓글은 제외) */}
                {isAuthenticated && user && comment.user_id === user.id && !comment.is_deleted && (
                  <div className="flex gap-1 ml-2">
                    <button
                      onClick={() => startEditing(comment)}
                      className="p-1 text-gray-400 hover:text-blue-600"
                      title="수정"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDeleteComment(comment.id)}
                      className="p-1 text-gray-400 hover:text-red-600"
                      title="삭제"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
