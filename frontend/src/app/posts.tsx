"use client";

import React, { useState, useEffect } from "react";
import { ArrowSmallDownIcon } from "@heroicons/react/24/solid";
import BlogPostCard from "@/components/blog-post-card";
import { MCPServer } from "@/types/mcp";
import { MCP_CATEGORIES } from "@/constants/categories";
import { useAuth } from "@/contexts/AuthContext";

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

interface PostsProps {
  searchTerm?: string;
}

export function Posts({ searchTerm: initialSearchTerm = "" }: PostsProps) {
  const { isAuthenticated } = useAuth();
  const [posts, setPosts] = useState<Post[]>([]);
  const [allPosts, setAllPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("All");
  const [visibleCount, setVisibleCount] = useState(6); // 초기 6개 카드만 보이도록
  const [refreshKey, setRefreshKey] = useState(0); // 즐겨찾기 상태 변경 시 리프레시용
  const [searchTerm, setSearchTerm] = useState(initialSearchTerm); // 검색어 상태 추가

  // 외부에서 전달된 검색어가 변경될 때 처리
  useEffect(() => {
    if (initialSearchTerm !== searchTerm) {
      handleSearch(initialSearchTerm);
    }
  }, [initialSearchTerm]);

  useEffect(() => {
    const fetchPosts = async () => {
      try {
        console.log('Fetching posts from /api/posts...');
        const response = await fetch('/api/posts');
        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);
        
        if (response.ok) {
          const data = await response.json();
          console.log('=== POSTS API RESPONSE DEBUG ===');
          console.log('Response status:', response.status);
          console.log('Raw data length:', data.length);
          console.log('Raw data:', data);
          console.log('First item structure:', data[0]);
          
          // 백엔드 데이터를 프론트엔드 형태로 변환
          const transformedData = data.map((mcp: any, index: number) => {
            console.log(`Transforming item ${index}:`, mcp);
            
            // tag 처리 로직 개선
            let tagString = '';
            if (mcp.tags) {
              if (Array.isArray(mcp.tags)) {
                // tag가 배열인 경우
                if (mcp.tags.length > 0 && typeof mcp.tags[0] === 'object' && mcp.tags[0].name) {
                  // tag가 객체 배열인 경우 (예: [{name: "tag1"}, {name: "tag2"}])
                  tagString = mcp.tags.map((tag: any) => tag.name || tag).join(', ');
                } else {
                  // tag가 문자열 배열인 경우 (예: ["tag1", "tag2"])
                  tagString = mcp.tags.join(', ');
                }
              } else if (typeof mcp.tags === 'string') {
                // tag가 이미 문자열인 경우
                tagString = mcp.tags;
              }
            }
            
            const transformed = {
              id: mcp.id,
              category: mcp.category || 'Unknown',
              tags: tagString,
              title: mcp.name || 'Unknown Name',
              desc: mcp.description || 'No description',
              date: mcp.created_at || 'Unknown date',
              author: {
                img: '/image/avatar1.jpg', // 올바른 아바타 경로 사용
                name: mcp.owner?.username || 'Unknown Author'
              }
            };
            
            console.log(`Transformed item ${index}:`, transformed);
            return transformed;
          });
          
          console.log('Final transformed data length:', transformedData.length);
          console.log('Final transformed data:', transformedData);
          console.log('=== END DEBUG ===');
          
          setAllPosts(transformedData);
          setPosts(transformedData);
        } else {
          console.error('Failed to fetch posts, status:', response.status);
          const errorText = await response.text();
          console.error('Error response:', errorText);
        }
      } catch (error) {
        console.error('Error fetching posts:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPosts();
  }, [refreshKey]); // refreshKey가 변경될 때마다 다시 가져오기

  // 검색 기능 추가
  const handleSearch = (searchTerm: string) => {
    setSearchTerm(searchTerm);
    setActiveTab("All"); // 검색 시 All 탭으로 리셋
    setVisibleCount(6); // 검색 시 초기 6개로 리셋
    
    if (!searchTerm.trim()) {
      setPosts(allPosts);
      return;
    }

    const filteredPosts = allPosts.filter(post => {
      const searchLower = searchTerm.toLowerCase();
      return (
        post.title.toLowerCase().includes(searchLower) ||
        post.desc.toLowerCase().includes(searchLower) ||
        post.tags.toLowerCase().includes(searchLower) ||
        post.category.toLowerCase().includes(searchLower)
      );
    });
    
    setPosts(filteredPosts);
  };

  // 탭 변경 시 필터링
  const handleTabChange = (category: string) => {
    setActiveTab(category);
    setVisibleCount(6); // 탭 변경 시 초기 6개로 리셋
    
    if (category === "All") {
      // 검색어가 있으면 검색 결과를 유지, 없으면 전체 표시
      if (searchTerm.trim()) {
        const filteredPosts = allPosts.filter(post => {
          const searchLower = searchTerm.toLowerCase();
          return (
            post.title.toLowerCase().includes(searchLower) ||
            post.desc.toLowerCase().includes(searchLower) ||
            post.tags.toLowerCase().includes(searchLower) ||
            post.category.toLowerCase().includes(searchLower)
          );
        });
        setPosts(filteredPosts);
      } else {
        setPosts(allPosts);
      }
    } else {
      // 카테고리 필터링 + 검색어 필터링
      let filteredPosts = allPosts.filter(post => post.category === category);
      
      if (searchTerm.trim()) {
        filteredPosts = filteredPosts.filter(post => {
          const searchLower = searchTerm.toLowerCase();
          return (
            post.title.toLowerCase().includes(searchLower) ||
            post.desc.toLowerCase().includes(searchLower) ||
            post.tags.toLowerCase().includes(searchLower) ||
            post.category.toLowerCase().includes(searchLower)
          );
        });
      }
      
      setPosts(filteredPosts);
    }
  };

  // VIEW MORE 버튼 클릭 시 더 많은 카드 표시
  const handleViewMore = () => {
    setVisibleCount(prev => prev + 6); // 6개씩 추가
  };

  // 즐겨찾기 상태 변경 시 리프레시
  const handleFavoriteChange = () => {
    setRefreshKey(prev => prev + 1);
  };

  // 현재 보여줄 카드들
  const visiblePosts = posts.slice(0, visibleCount);
  const hasMorePosts = visibleCount < posts.length;

  return (
    <section className="min-h-screen p-8">
      <div className="mx-auto max-w-7xl w-full">
        {/* 검색 결과 표시 */}
        {searchTerm && (
          <div className="mb-6 text-center">
            <p className="text-gray-600">
              검색 결과: "{searchTerm}" ({posts.length}개 서버)
            </p>
          </div>
        )}

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
              {searchTerm 
                ? `"${searchTerm}"에 대한 검색 결과가 없습니다.`
                : `No MCP servers found in ${activeTab} category.`
              }
            </h3>
          </div>
        ) : (
          <div className="w-full">
            <div className="grid grid-cols-1 gap-x-8 gap-y-16 items-start lg:grid-cols-3">
              {visiblePosts.map(({ category, tags, title, desc, date, author, id }) => (
                <BlogPostCard
                  key={`${id || title}-${refreshKey}`} // refreshKey를 포함하여 리렌더링 보장
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
              VIEW MORE
            </button>
          </div>
        )}
      </div>
    </section>
  );
}

export default Posts;
