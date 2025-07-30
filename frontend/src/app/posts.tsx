"use client";

import React, { useState, useEffect } from "react";
import { ArrowSmallDownIcon } from "@heroicons/react/24/solid";
import BlogPostCard from "@/components/blog-post-card";
import { MCPServer } from "@/types/mcp";
import { MCP_CATEGORIES } from "@/constants/categories";

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

export function Posts() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [allPosts, setAllPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("All");
  const [visibleCount, setVisibleCount] = useState(6); // 초기 6개 카드만 보이도록

  useEffect(() => {
    const fetchPosts = async () => {
      try {
        const response = await fetch('/api/posts');
        if (response.ok) {
          const data = await response.json();
          console.log('Fetched posts data:', data); // 전체 데이터 확인
          console.log('First post structure:', data[0]); // 첫 번째 포스트 구조 확인
          
          setAllPosts(data);
          setPosts(data);
        } else {
          console.error('Failed to fetch posts');
        }
      } catch (error) {
        console.error('Error fetching posts:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPosts();
  }, []);

  // 탭 변경 시 필터링
  const handleTabChange = (category: string) => {
    setActiveTab(category);
    setVisibleCount(6); // 탭 변경 시 초기 6개로 리셋
    
    if (category === "All") {
      setPosts(allPosts);
    } else {
      const filteredPosts = allPosts.filter(post => post.category === category);
      setPosts(filteredPosts);
    }
  };

  // VIEW MORE 버튼 클릭 시 더 많은 카드 표시
  const handleViewMore = () => {
    setVisibleCount(prev => prev + 6); // 6개씩 추가
  };

  // 현재 보여줄 카드들
  const visiblePosts = posts.slice(0, visibleCount);
  const hasMorePosts = visibleCount < posts.length;

  return (
    <section className="min-h-screen p-8">
      <div className="mx-auto max-w-7xl w-full">
        {/* 카테고리 탭 영역 */}
        <div className="w-full flex mb-8 flex-col items-center">
          <div className="h-10 w-full md:w-[50rem] border border-gray-300 rounded-lg bg-white bg-opacity-90 flex">
            <button
              onClick={() => handleTabChange("All")}
              className={`flex-1 px-4 py-2 text-sm font-medium transition-colors rounded-l-lg ${
                activeTab === "All"
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              All
            </button>
            {MCP_CATEGORIES.map((category) => (
              <button
                key={category}
                onClick={() => handleTabChange(category)}
                className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
                  activeTab === category
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-700 hover:bg-gray-100'
                } ${category === MCP_CATEGORIES[MCP_CATEGORIES.length - 1] ? 'rounded-r-lg' : ''}`}
              >
                {category}
              </button>
            ))}
          </div>
        </div>

        {/* 카드 영역 */}
        {loading ? (
          <div className="flex items-center justify-center h-[500px]">
            <h3 className="text-lg text-gray-600">
              Loading posts...
            </h3>
          </div>
        ) : posts.length === 0 ? (
          <div className="flex items-center justify-center h-[500px]">
            <h3 className="text-lg text-gray-600">
              No MCP servers found in {activeTab} category.
            </h3>
          </div>
        ) : (
          <div className="w-full">
            <div className="grid grid-cols-1 gap-x-8 gap-y-16 items-start lg:grid-cols-3">
              {visiblePosts.map(({ category, tags, title, desc, date, author, id }) => (
                <BlogPostCard
                  key={id || title} // id가 있으면 id 사용, 없으면 title 사용
                  category={category}
                  tags={tags}
                  title={title}
                  desc={desc}
                  date={date}
                  author={{
                    img: author?.img || '/default-avatar.png', // 기본 아바타 이미지
                    name: author?.name || 'Unknown Author', // 기본 작성자명
                  }}
                  id={id}
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
              VIEW MORE
            </button>
          </div>
        )}
      </div>
    </section>
  );
}

export default Posts;
