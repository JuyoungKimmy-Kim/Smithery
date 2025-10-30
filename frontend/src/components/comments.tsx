"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useLanguage } from "@/contexts/LanguageContext";
import { apiFetch } from "@/lib/api-client";
import {
  ChatBubbleLeftIcon,
  PencilIcon,
  TrashIcon,
  PaperAirplaneIcon,
  CheckIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";
import { StarIcon as StarSolid } from "@heroicons/react/24/solid";

interface Comment {
  id: number;
  content: string;
  is_deleted: boolean;
  user_id: number;
  created_at: string;
  updated_at: string;
  user_nickname: string;
  user_avatar_url: string;
  rating: number;
}

interface CommentsProps {
  mcpServerId: number;
}

export default function Comments({ mcpServerId }: CommentsProps) {
  const { user, isAuthenticated, token } = useAuth();
  const { t, language } = useLanguage();
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState("");
  const [newRating, setNewRating] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [editingCommentId, setEditingCommentId] = useState<number | null>(null);
  const [editingContent, setEditingContent] = useState("");
  const [editingRating, setEditingRating] = useState<number>(0);
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
    // 0~5, 0.5 단위 검증
    const isHalfStep = Math.abs(newRating * 2 - Math.round(newRating * 2)) < 1e-9;
    if (newRating < 0 || newRating > 5 || !isHalfStep) {
      alert(t('comments.writeErrorUnknown'));
      return;
    }

    setSubmitting(true);
    try {
      const response = await apiFetch(`/api/comments/mcp-servers/${mcpServerId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        requiresAuth: true,
        body: JSON.stringify({ content: newComment.trim(), rating: newRating }),
      });

      if (response.ok) {
        setNewComment("");
        setNewRating(0);
        fetchComments();
        fetchCommentCount();
      } else {
        const errorData = await response.json();
        alert(t('comments.writeError', { error: errorData.detail || t('comments.writeErrorUnknown') }));
      }
    } catch (error) {
      console.error("댓글 작성 오류:", error);
      alert(t('comments.writeErrorUnknown'));
    } finally {
      setSubmitting(false);
    }
  };

  // 댓글 수정
  const handleEditComment = async (commentId: number) => {
    if (!editingContent.trim()) return;
    const isHalfStep = Math.abs(editingRating * 2 - Math.round(editingRating * 2)) < 1e-9;
    if (editingRating < 0 || editingRating > 5 || !isHalfStep) {
      alert(t('comments.editErrorUnknown'));
      return;
    }

    try {
      const response = await apiFetch(`/api/comments/${commentId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        requiresAuth: true,
        body: JSON.stringify({ content: editingContent.trim(), rating: editingRating }),
      });

      if (response.ok) {
        setEditingCommentId(null);
        setEditingContent("");
        setEditingRating(0);
        fetchComments();
      } else {
        const errorData = await response.json();
        alert(t('comments.editError', { error: errorData.detail || t('comments.editErrorUnknown') }));
      }
    } catch (error) {
      console.error("댓글 수정 오류:", error);
      alert(t('comments.editErrorUnknown'));
    }
  };

  // 댓글 삭제
  const handleDeleteComment = async (commentId: number) => {
    if (!confirm(t('comments.deleteConfirm'))) return;

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
        alert(t('comments.deleteError', { error: errorData.detail || t('comments.deleteErrorUnknown') }));
      }
    } catch (error) {
      console.error("댓글 삭제 오류:", error);
      alert(t('comments.deleteErrorUnknown'));
    }
  };

  // 수정 모드 시작
  const startEditing = (comment: Comment) => {
    setEditingCommentId(comment.id);
    setEditingContent(comment.content);
    setEditingRating(comment.rating ?? 0);
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
      return t('comments.justNow');
    } else if (diffInHours < 24) {
      return t('comments.hoursAgo', { hours: diffInHours.toString() });
    } else {
      return date.toLocaleDateString(language === 'ko' ? 'ko-KR' : 'en-US');
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-8">
      <div className="flex items-center gap-2 mb-6">
        <ChatBubbleLeftIcon className="h-6 w-6 text-blue-500" />
        <h2 className="text-2xl font-bold text-gray-900">{t('comments.title')}</h2>
        <span className="text-sm text-gray-500">({commentCount})</span>
      </div>

      {/* 댓글 작성 폼 */}
      {isAuthenticated ? (
        <form onSubmit={handleSubmitComment} className="mb-6">
          <div className="flex gap-3">
            <div className="flex-1">
              <div className="mb-2">
                <StarRatingInput value={newRating} onChange={setNewRating} />
              </div>
              <textarea
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder={t('comments.writeComment')}
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
                t('comments.submitting')
              ) : (
                <>
                  <PaperAirplaneIcon className="h-4 w-4" />
                  {t('comments.submit')}
                </>
              )}
            </button>
          </div>
        </form>
      ) : (
        <div className="mb-6 p-4 bg-gray-50 rounded-md text-center text-gray-600">
          {t('comments.loginRequired')}
        </div>
      )}

      {/* 댓글 목록 */}
      {loading ? (
        <div className="text-center py-8 text-gray-500">{t('comments.loading')}</div>
      ) : comments.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          {t('comments.noComments')}
        </div>
      ) : (
        <div className="space-y-4">
          {comments.map((comment) => (
            <div key={comment.id} className="border-b border-gray-100 pb-4 last:border-b-0">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <img
                      src={comment.user_avatar_url || '/image/avatar1.jpg'}
                      alt={comment.user_nickname}
                      className="w-8 h-8 rounded-full object-cover"
                    />
                    <span className="font-medium text-gray-900">
                      {comment.user_nickname}
                    </span>
                    <span className="flex items-center ml-1">
                      <StarRatingDisplay value={comment.rating} />
                    </span>
                    <span className="text-sm text-gray-500">
                      {formatDate(comment.created_at)}
                    </span>
                    {comment.updated_at !== comment.created_at && (
                      <span className="text-xs text-gray-400">{t('comments.edited')}</span>
                    )}
                  </div>
                  
                  {editingCommentId === comment.id ? (
                    <div className="space-y-2">
                    <StarRatingInput value={editingRating} onChange={setEditingRating} />
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
                          {t('comments.save')}
                        </button>
                        <button
                          onClick={cancelEditing}
                          className="px-3 py-1 bg-gray-500 text-white text-sm rounded-md hover:bg-gray-600 flex items-center gap-1"
                        >
                          <XMarkIcon className="h-3 w-3" />
                          {t('comments.cancel')}
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
                      title={t('comments.edit')}
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDeleteComment(comment.id)}
                      className="p-1 text-gray-400 hover:text-red-600"
                      title={t('comments.delete')}
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

function StarRatingDisplay({ value }: { value: number }) {
  const percentage = Math.max(0, Math.min(100, (value / 5) * 100));
  return (
    <div className="relative inline-block align-middle leading-none" aria-label={`rating ${value.toFixed(1)} / 5`}>
      <div className="flex text-gray-300 leading-none">
        {Array.from({ length: 5 }).map((_, idx) => (
          <StarSolid key={idx} className="h-4 w-4 shrink-0" />
        ))}
      </div>
      <div className="absolute inset-0 overflow-hidden" style={{ width: `${percentage}%` }}>
        <div className="flex text-yellow-400 leading-none pointer-events-none">
          {Array.from({ length: 5 }).map((_, idx) => (
            <StarSolid key={idx} className="h-4 w-4 shrink-0" />
          ))}
        </div>
      </div>
    </div>
  );
}

function StarRatingInput({ value, onChange }: { value: number; onChange: (v: number) => void }) {
  const percentage = Math.max(0, Math.min(100, (value / 5) * 100));
  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = (e.currentTarget as HTMLDivElement).getBoundingClientRect();
    const x = e.clientX - rect.left;
    const ratio = x / rect.width; // 0..1
    const steps = Math.round(ratio * 10); // 0..10
    const newVal = Math.min(10, Math.max(0, steps)) / 2; // 0..5 step 0.5
    onChange(newVal);
  };
  return (
    <div className="inline-block select-none align-middle leading-none">
      <div className="relative inline-block cursor-pointer align-middle leading-none" onClick={handleClick} title={`${value.toFixed(1)}/5`}>
        <div className="flex text-gray-300 leading-none">
          {Array.from({ length: 5 }).map((_, idx) => (
            <StarSolid key={idx} className="h-6 w-6 shrink-0" />
          ))}
        </div>
        <div className="absolute inset-0 overflow-hidden pointer-events-none" style={{ width: `${percentage}%` }}>
          <div className="flex text-yellow-400 leading-none">
            {Array.from({ length: 5 }).map((_, idx) => (
              <StarSolid key={idx} className="h-6 w-6 shrink-0" />
            ))}
          </div>
        </div>
      </div>
      <span className="ml-2 align-middle text-sm text-gray-600">{value.toFixed(1)}</span>
    </div>
  );
}
