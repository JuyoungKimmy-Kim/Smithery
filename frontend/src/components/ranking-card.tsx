"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { HeartIcon as HeartIconOutline } from "@heroicons/react/24/outline";
import { HeartIcon as HeartIconSolid } from "@heroicons/react/24/solid";
import { TagList } from "./tag-list";
import { useAuth } from "@/contexts/AuthContext";
import { apiFetch } from "@/lib/api-client";

interface RankingCardProps {
  rank: number;
  title: string;
  desc: string;
  tags: string;
  id?: string;
  onFavoriteChange?: () => void;
  onTagClick?: (tag: string) => void;
}

export function RankingCard({
  rank,
  title,
  desc,
  tags,
  id,
  onFavoriteChange,
  onTagClick,
}: RankingCardProps) {
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const [isFavorite, setIsFavorite] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [favoritesCount, setFavoritesCount] = useState(0);

  useEffect(() => {
    if (id) {
      fetchFavoritesCount();
      if (isAuthenticated) {
        checkFavoriteStatus();
      }
    }
  }, [isAuthenticated, id]);

  const fetchFavoritesCount = async () => {
    try {
      const response = await fetch(`/api/mcp-servers/${id}/favorites/count`);
      if (response.ok) {
        const data = await response.json();
        setFavoritesCount(data.favorites_count);
      }
    } catch (error) {
      console.error('Error fetching favorites count:', error);
    }
  };

  const checkFavoriteStatus = async () => {
    try {
      const response = await apiFetch(`/api/mcp-servers/user/favorites`, {
        requiresAuth: true
      });
      
      if (response.ok) {
        const favorites = await response.json();
        const isFav = favorites.some((fav: any) => fav.id === id);
        setIsFavorite(isFav);
      }
    } catch (error) {
      console.error('Error checking favorite status:', error);
    }
  };

  const handleFavoriteClick = async (e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    setIsLoading(true);
    try {
      const method = isFavorite ? 'DELETE' : 'POST';
      const response = await apiFetch(`/api/mcp-servers/${id}/favorites`, {
        method,
        requiresAuth: true
      });

      if (response.ok) {
        setIsFavorite(!isFavorite);
        await fetchFavoritesCount();
        if (onFavoriteChange) {
          onFavoriteChange();
        }
      }
    } catch (error) {
      console.error('Error toggling favorite:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCardClick = () => {
    if (id) {
      router.push(`/detail/${id}`);
    }
  };

  // 순위별 색상 및 스타일
  const getRankStyle = () => {
    switch (rank) {
      case 1:
        return {
          bg: 'bg-gradient-to-r from-yellow-50 to-amber-50',
          border: 'border-yellow-400',
          rankBg: 'bg-gradient-to-br from-yellow-400 to-yellow-600',
          shadow: 'shadow-yellow-200',
        };
      case 2:
        return {
          bg: 'bg-gradient-to-r from-gray-50 to-slate-50',
          border: 'border-gray-400',
          rankBg: 'bg-gradient-to-br from-gray-300 to-gray-500',
          shadow: 'shadow-gray-200',
        };
      case 3:
        return {
          bg: 'bg-gradient-to-r from-orange-50 to-amber-50',
          border: 'border-amber-600',
          rankBg: 'bg-gradient-to-br from-amber-600 to-amber-800',
          shadow: 'shadow-amber-200',
        };
      default:
        return {
          bg: 'bg-white',
          border: 'border-gray-200',
          rankBg: 'bg-gray-400',
          shadow: 'shadow-gray-100',
        };
    }
  };

  const rankStyle = getRankStyle();

  return (
    <div
      onClick={handleCardClick}
      className={`group relative flex items-center gap-2 px-3 py-2 rounded-md border ${rankStyle.border} ${rankStyle.bg} ${rankStyle.shadow} shadow-sm hover:shadow-md transition-all duration-300 cursor-pointer hover:-translate-y-0.5`}
    >
      {/* 순위 배지 */}
      <div className={`flex-shrink-0 w-6 h-6 rounded-full ${rankStyle.rankBg} flex items-center justify-center text-white font-bold text-sm shadow-sm`}>
        {rank}
      </div>

      {/* 컨텐츠 영역 */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <div className="flex-1 min-w-0 flex items-center gap-3">
            {/* 제목 */}
            <h3 className="text-sm font-semibold text-gray-900 group-hover:text-blue-600 transition-colors truncate">
              {title}
            </h3>
            
            {/* 설명 */}
            <p className="text-xs text-gray-500 truncate flex-shrink">
              {desc}
            </p>
            
            {/* 태그 */}
            <div className="flex items-center gap-1 flex-shrink-0">
              <TagList tags={tags} maxTags={3} onTagClick={onTagClick} />
            </div>
          </div>

          {/* 좋아요 버튼 */}
          <div className="flex-shrink-0 flex items-center gap-1">
            <button
              onClick={handleFavoriteClick}
              disabled={isLoading}
              className="p-0.5 rounded-full hover:bg-white/50 transition-colors disabled:opacity-50"
            >
              {isFavorite ? (
                <HeartIconSolid className="h-4 w-4 text-red-500" />
              ) : (
                <HeartIconOutline className="h-4 w-4 text-gray-400 group-hover:text-red-400" />
              )}
            </button>
            <span className="text-xs font-medium text-gray-700 min-w-[1.5rem] text-center">
              {favoritesCount}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default RankingCard;

