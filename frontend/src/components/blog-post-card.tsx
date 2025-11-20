import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { StarIcon } from "@heroicons/react/24/outline";
import { StarIcon as StarIconSolid, CheckCircleIcon } from "@heroicons/react/24/solid";
import TagList from "./tag-list";
import { useAuth } from "@/contexts/AuthContext";
import { useLanguage } from "@/contexts/LanguageContext";
import { apiFetch } from "@/lib/api-client";
import { stripMarkdown } from "@/lib/markdown-utils";

interface BlogPostCardProps {
  category: string;
  tags: string;
  title: string;
  desc: string;
  author: { name: string; img: string };
  date: string;
  status?: string; // 서버 상태 (pending, approved 등)
  healthStatus?: string; // Health status (healthy, unhealthy, unknown)
  id?: string; // MCP 서버 ID 추가
  favoritesCount?: number; // 즐겨찾기 수 (초기값)
  onFavoriteChange?: () => void; // 즐겨찾기 상태 변경 콜백
  onTagClick?: (tag: string) => void; // 태그 클릭 콜백
}

export function BlogPostCard({
  category,
  tags,
  title,
  desc,
  author,
  date,
  status,
  healthStatus,
  id,
  favoritesCount: initialFavoritesCount = 0,
  onFavoriteChange,
  onTagClick,
}: BlogPostCardProps) {
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const { t } = useLanguage();
  const [isFavorite, setIsFavorite] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [favoritesCount, setFavoritesCount] = useState(initialFavoritesCount);

  // 즐겨찾기 상태 및 수 확인
  useEffect(() => {
    // 초기값 설정
    setFavoritesCount(initialFavoritesCount);

    const loadFavoriteData = () => {
      if (id) {
        fetchFavoritesCount();
        if (isAuthenticated) {
          checkFavoriteStatus();
        }
      }
    };

    loadFavoriteData();

    // 페이지가 다시 보일 때 자동 새로고침 (뒤로 가기 등)
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        loadFavoriteData();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [isAuthenticated, id, initialFavoritesCount]);

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
        console.log('Checking favorite status for id:', id, 'type:', typeof id);
        console.log('User favorites:', favorites.map((f: any) => ({ id: f.id, type: typeof f.id })));
        // ID를 문자열로 변환하여 비교 (타입 불일치 방지)
        const isFav = favorites.some((fav: any) => String(fav.id) === String(id));
        console.log('Is favorite:', isFav);
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

    if (!id) return;

    setIsLoading(true);
    try {
      const url = `/api/mcp-servers/${id}/favorite`;
      const method = isFavorite ? 'DELETE' : 'POST';
      
      const response = await apiFetch(url, {
        method,
        requiresAuth: true
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Favorite toggle response:', data);
        setIsFavorite(!isFavorite);
        // 즐겨찾기 수 새로고침
        await fetchFavoritesCount();
        // 부모 컴포넌트에 즐겨찾기 상태 변경 알림
        if (onFavoriteChange) {
          onFavoriteChange();
        }
      } else {
        const errorText = await response.text();
        console.error('Failed to toggle favorite:', response.status, errorText);
      }
    } catch (error) {
      console.error('Error toggling favorite:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClick = () => {
    console.log("Card clicked! ID:", id); // 디버깅 로그 추가
    console.log("Card title:", title); // 제목도 로깅
    if (id) {
      console.log("Navigating to:", `/mcp/${id}`); // 디버깅 로그 추가
      router.push(`/mcp/${id}`);
    } else {
      console.log("No ID provided, navigating to test page"); // 디버깅 로그 추가
      // ID가 없어도 테스트용으로 첫 번째 MCP로 이동
      // router.push 대신 window.location 사용
      window.location.href = `/mcp/1`;
    }
  };

  const handleAuthorClick = (e: React.MouseEvent) => {
    e.stopPropagation(); // 카드 클릭 이벤트 방지
    if (author?.name && author.name !== 'Unknown') {
      router.push(`/user/${author.name}`);
    }
  };

  return (
    <div 
      className={`bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 cursor-pointer relative h-71 flex flex-col border border-gray-200 ${
        status === 'pending' ? 'border-l-4 border-l-yellow-400' : ''
      }`}
      onClick={handleClick}
    >
      {/* GitHub 스타일 스타 버튼 */}
      <div className="absolute top-4 right-4 z-10">
        <button
          onClick={handleFavoriteClick}
          disabled={isLoading}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md border text-sm font-medium transition-all duration-200 ${
            isFavorite 
              ? 'bg-yellow-50 border-yellow-300 text-yellow-700 hover:bg-yellow-100' 
              : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
          } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          {isFavorite ? (
            <StarIconSolid className="h-4 w-4" />
          ) : (
            <StarIcon className="h-4 w-4" />
          )}
          <span>{favoritesCount}</span>
        </button>
      </div>

      <div className="p-6 flex flex-col h-full">
        <div className="flex items-center gap-2 mb-2">
          <h3 className="text-xl font-semibold text-gray-900 normal-case transition-colors hover:text-gray-700 cursor-pointer line-clamp-2">
            {title}
          </h3>
          {/* Active 상태만 표시 */}
          {healthStatus === 'healthy' && (
            <div className="flex items-center gap-1">
              <CheckCircleIcon className="h-4 w-4 text-green-500" />
              <span className="text-xs font-medium text-green-700">Active</span>
            </div>
          )}
          {status === 'pending' && (
            <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full whitespace-nowrap">
              {t('mypage.pendingBadge')}
            </span>
          )}
        </div>
        <p className="text-gray-600 mb-4 cursor-pointer line-clamp-3 flex-grow break-words overflow-hidden min-h-[4.5rem]">
          {stripMarkdown(desc)}
        </p>
        <div className="mb-4 min-h-[2rem] flex items-start">
          <TagList tags={tags} maxTags={4} onTagClick={onTagClick} />
        </div>
        <div 
          className="flex items-center gap-4 cursor-pointer hover:bg-gray-50 p-2 rounded-lg transition-colors mt-auto"
          onClick={handleAuthorClick}
        >
          <img
            src={author?.img || '/image/avatar1.jpg'}
            alt={author?.name || 'Unknown'}
            className="w-8 h-8 rounded-full"
          />
          <div>
            <p className="text-sm font-medium text-gray-900 mb-0.5 hover:text-blue-600 transition-colors">
              {String(author?.name || 'Unknown')}
            </p>
            <p className="text-xs text-gray-500">
              {date}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default BlogPostCard;