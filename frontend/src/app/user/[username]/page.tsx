"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import BlogPostCard from "@/components/blog-post-card";
import { ArrowSmallDownIcon } from "@heroicons/react/24/solid";
import { useLanguage } from "@/contexts/LanguageContext";

interface Post {
  category: string;
  tags: string;
  title: string;
  desc: string;
  date: string;
  author: {
    img: string;
    name: string;
  };
  id?: string;
}

export default function UserServersPage() {
  const params = useParams();
  const username = params.username as string;
  const { t } = useLanguage();
  
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [visibleCount, setVisibleCount] = useState(6);

  useEffect(() => {
    const fetchUserServers = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const response = await fetch(`/api/mcp-servers/user/${username}`);
        
        if (response.ok) {
          const data = await response.json();
          setPosts(data);
        } else if (response.status === 404) {
          setError('userNotFound');
        } else {
          setError('loadError');
        }
      } catch (error) {
        console.error('Error fetching user servers:', error);
        setError('loadError');
      } finally {
        setLoading(false);
      }
    };

    if (username) {
      fetchUserServers();
    }
  }, [username]);

  const handleViewMore = () => {
    setVisibleCount(prev => prev + 6);
  };

  const handleFavoriteChange = () => {
    // 즐겨찾기 상태 변경 시 페이지 새로고침
    window.location.reload();
  };

  const visiblePosts = posts.slice(0, visibleCount);
  const hasMorePosts = visibleCount < posts.length;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h3 className="text-lg text-gray-600 mb-4">
            {t('userpage.loading', { username })}
          </h3>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h3 className="text-lg text-red-600 mb-4">{t(`userpage.${error}`)}</h3>
          <button 
            onClick={() => window.history.back()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            {t('userpage.goBack')}
          </button>
        </div>
      </div>
    );
  }

  return (
    <section className="min-h-screen p-8">
      <div className="mx-auto max-w-7xl w-full">
        {/* 헤더 영역 */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            {t('userpage.title', { username })}
          </h1>
          <p className="text-gray-600">
            {t('userpage.totalServers', { count: posts.length.toString() })}
          </p>
        </div>

        {/* 카드 영역 */}
        {posts.length === 0 ? (
          <div className="flex items-center justify-center h-[500px]">
            <div className="text-center">
              <h3 className="text-lg text-gray-600 mb-4">
                {t('userpage.noServers')}
              </h3>
              <button 
                onClick={() => window.history.back()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                {t('userpage.goBack')}
              </button>
            </div>
          </div>
        ) : (
          <div className="w-full">
            <div className="grid grid-cols-1 gap-x-8 gap-y-16 items-start lg:grid-cols-3">
              {visiblePosts.map(({ category, tags, title, desc, date, author, id }) => (
                <BlogPostCard
                  key={`${id || title}`}
                  category={category}
                  tags={tags}
                  title={title}
                  desc={desc}
                  date={date}
                  author={{
                    img: author?.img || '/default-avatar.png',
                    name: author?.name || 'Unknown Author',
                  }}
                  id={id}
                  onFavoriteChange={handleFavoriteChange}
                />
              ))}
            </div>
          </div>
        )}

        {/* VIEW MORE 버튼 */}
        {hasMorePosts && (
          <div className="flex justify-center mt-8">
            <button 
              onClick={handleViewMore}
              className="flex items-center gap-2 text-gray-700 hover:text-gray-900 transition-colors"
            >
              <ArrowSmallDownIcon className="h-5 w-5 font-bold text-gray-900" />
              {t('userpage.viewMore')}
            </button>
          </div>
        )}
      </div>
    </section>
  );
} 