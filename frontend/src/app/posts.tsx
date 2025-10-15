"use client";

import React, { useState, useEffect } from "react";
import { ArrowSmallDownIcon, CheckIcon, PlusIcon } from "@heroicons/react/24/solid";
import BlogPostCard from "@/components/blog-post-card";
import { MCPServer } from "@/types/mcp";
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
  favorites_count?: number;
}

interface PostsProps {
  searchTerm?: string;
}

export function Posts({ searchTerm: initialSearchTerm = "" }: PostsProps) {
  const { isAuthenticated } = useAuth();
  const [posts, setPosts] = useState<Post[]>([]);
  const [allPosts, setAllPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [allTags, setAllTags] = useState<string[]>([]);
  const [tagCounts, setTagCounts] = useState<{[key: string]: number}>({});
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
          console.log('Fetched posts data:', data); // 전체 데이터 확인
          console.log('Number of posts:', data.length); // 포스트 개수 확인
          console.log('First post structure:', data[0]); // 첫 번째 포스트 구조 확인
          
          // favorites_count 확인
          console.log('Posts with favorites_count:', data.map((p: Post) => ({ 
            title: p.title, 
            favorites_count: p.favorites_count 
          })));
          
          // favorites_count 기준으로 정렬 (내림차순)
          const sortedData = [...data].sort((a: Post, b: Post) => {
            const aCount = a.favorites_count || 0;
            const bCount = b.favorites_count || 0;
            console.log(`Comparing: ${a.title} (${aCount}) vs ${b.title} (${bCount})`);
            return bCount - aCount;
          });
          
          console.log('Sorted posts:', sortedData.map((p: Post) => ({ 
            title: p.title, 
            favorites_count: p.favorites_count 
          })));
          
          setAllPosts(sortedData);
          setPosts(sortedData);
          
          // 모든 태그 추출 및 사용 빈도 계산
          const tagCountMap: {[key: string]: number} = {};
          data.forEach((post: Post) => {
            if (post.tags) {
              // 태그 파싱 (JSON, 배열 형태, 쉼표 구분 문자열 등 처리)
              let tagArray: string[] = [];
              try {
                const parsed = JSON.parse(post.tags);
                tagArray = Array.isArray(parsed) ? parsed : [parsed];
              } catch {
                if (typeof post.tags === 'string') {
                  if (post.tags.startsWith('[') && post.tags.endsWith(']')) {
                    const cleanTags = post.tags.slice(1, -1);
                    tagArray = cleanTags.split(',').map(tag => 
                      tag.trim().replace(/['"]/g, '')
                    ).filter(tag => tag.length > 0);
                  } else {
                    tagArray = post.tags.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0);
                  }
                }
              }
              tagArray.forEach(tag => {
                tagCountMap[tag] = (tagCountMap[tag] || 0) + 1;
              });
            }
          });
          
          // 사용 빈도순으로 정렬 (많이 사용된 순서)
          const sortedTags = Object.keys(tagCountMap).sort((a, b) => tagCountMap[b] - tagCountMap[a]);
          
          setTagCounts(tagCountMap);
          setAllTags(sortedTags);
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
    setSelectedTags([]); // 검색 시 태그 선택 리셋
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
    
    // favorites_count 기준으로 정렬 (내림차순)
    const sortedFilteredPosts = [...filteredPosts].sort((a: Post, b: Post) => 
      (b.favorites_count || 0) - (a.favorites_count || 0)
    );
    
    setPosts(sortedFilteredPosts);
  };

  // 태그 토글 핸들러 (선택/해제)
  const handleTagToggle = (tag: string) => {
    setVisibleCount(6); // 태그 변경 시 초기 6개로 리셋
    
    setSelectedTags(prev => {
      const newSelectedTags = prev.includes(tag)
        ? prev.filter(t => t !== tag) // 이미 선택된 태그면 제거
        : [...prev, tag]; // 선택되지 않은 태그면 추가
      
      // 필터링 적용
      applyTagFilter(newSelectedTags);
      return newSelectedTags;
    });
  };

  // 모든 태그 선택 해제
  const handleClearTags = () => {
    setSelectedTags([]);
    setVisibleCount(6);
    
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
      // favorites_count 기준으로 정렬 (내림차순)
      const sortedFilteredPosts = [...filteredPosts].sort((a: Post, b: Post) => 
        (b.favorites_count || 0) - (a.favorites_count || 0)
      );
      setPosts(sortedFilteredPosts);
    } else {
      setPosts(allPosts);
    }
  };

  // 태그 필터 적용
  const applyTagFilter = (tagsToFilter: string[]) => {
    if (tagsToFilter.length === 0) {
      // 선택된 태그가 없으면 검색어 필터만 적용
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
        // favorites_count 기준으로 정렬 (내림차순)
        const sortedFilteredPosts = [...filteredPosts].sort((a: Post, b: Post) => 
          (b.favorites_count || 0) - (a.favorites_count || 0)
        );
        setPosts(sortedFilteredPosts);
      } else {
        setPosts(allPosts);
      }
    } else {
      // 선택된 태그 중 하나라도 포함하는 포스트 필터링
      let filteredPosts = allPosts.filter(post => {
        if (!post.tags) return false;
        
        // 태그 파싱
        let tagArray: string[] = [];
        try {
          const parsed = JSON.parse(post.tags);
          tagArray = Array.isArray(parsed) ? parsed : [parsed];
        } catch {
          if (typeof post.tags === 'string') {
            if (post.tags.startsWith('[') && post.tags.endsWith(']')) {
              const cleanTags = post.tags.slice(1, -1);
              tagArray = cleanTags.split(',').map(t => 
                t.trim().replace(/['"]/g, '')
              ).filter(t => t.length > 0);
            } else {
              tagArray = post.tags.split(',').map(t => t.trim()).filter(t => t.length > 0);
            }
          }
        }
        
        // 선택된 태그 중 하나라도 포함하는지 확인 (OR 조건)
        return tagsToFilter.some(selectedTag => tagArray.includes(selectedTag));
      });
      
      // 검색어 필터링 추가
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
      
      // favorites_count 기준으로 정렬 (내림차순)
      const sortedFilteredPosts = [...filteredPosts].sort((a: Post, b: Post) => 
        (b.favorites_count || 0) - (a.favorites_count || 0)
      );
      
      setPosts(sortedFilteredPosts);
    }
  };

  // 태그 클릭 핸들러
  const handleTagClick = (tag: string) => {
    handleTagToggle(tag);
  };

  // VIEW MORE 버튼 클릭 시 더 많은 카드 표시
  const handleViewMore = () => {
    setVisibleCount(prev => prev + 6); // 6개씩 추가
  };

  // 즐겨찾기 상태 변경 시 리프레시
  const handleFavoriteChange = () => {
    setRefreshKey(prev => prev + 1);
  };

  // 상위 3개와 나머지 분리
  const topPosts = posts.slice(0, 3);
  const remainingPosts = posts.slice(3);
  
  // 현재 보여줄 나머지 카드들
  const visibleRemainingPosts = remainingPosts.slice(0, visibleCount);
  const hasMorePosts = visibleCount < remainingPosts.length;

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

        {/* 태그 선택 영역 */}
        {allTags.length > 0 && (
          <div className="w-full flex mb-8 flex-col items-center">
            <div className="flex flex-wrap gap-2 justify-center max-w-5xl">
              {allTags.map((tag) => (
                <button
                  key={tag}
                  onClick={() => handleTagToggle(tag)}
                  className={`px-4 py-2 text-sm font-medium transition-all duration-200 rounded-full flex items-center gap-2 ${
                    selectedTags.includes(tag)
                      ? 'bg-blue-500 text-white shadow-md scale-105'
                      : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <span>{tag}</span>
                  <span className="text-xs opacity-75">({tagCounts[tag]})</span>
                  {selectedTags.includes(tag) ? (
                    <CheckIcon className="h-4 w-4" />
                  ) : (
                    <PlusIcon className="h-4 w-4" />
                  )}
                </button>
              ))}
            </div>
          </div>
        )}

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
                : selectedTags.length > 0
                ? `선택한 태그에 해당하는 MCP 서버가 없습니다.`
                : `등록된 MCP 서버가 없습니다.`
              }
            </h3>
          </div>
        ) : (
          <div className="w-full">
            {/* Top 3 MCP Servers */}
            {topPosts.length > 0 && (
              <div className="mb-16">
                {/* 헤더 섹션 */}
                <div className="relative flex justify-center">
                  <span className="bg-white px-6 py-2 text-sm text-gray-500 font-medium rounded-full border border-gray-200">
                    Top 3 MCP Servers
                  </span>
                </div>
                <br></br>

                {/* 카드 그리드 */}
                <div className="grid grid-cols-1 gap-x-8 gap-y-8 items-start lg:grid-cols-3 mb-8">
                  {topPosts.map(({ category, tags, title, desc, date, author, id }, index) => (
                    <div key={`top-${id || title}-${refreshKey}`} className="relative">
                      {/* 순위 배지 */}
                      <div className={`absolute -top-3 -left-3 z-20 w-9 h-9 rounded-full flex items-center justify-center text-white font-bold text-base shadow-lg ${
                        index === 0 ? 'bg-gradient-to-br from-yellow-400 to-yellow-600' :
                        index === 1 ? 'bg-gradient-to-br from-gray-300 to-gray-500' :
                        'bg-gradient-to-br from-amber-600 to-amber-800'
                      }`}>
                        {index + 1}
                      </div>
                      
                      {/* 특별한 테두리 효과 */}
                      <div className={`absolute inset-0 rounded-lg ${
                        index === 0 ? 'bg-gradient-to-r from-yellow-400 via-yellow-500 to-amber-500' :
                        index === 1 ? 'bg-gradient-to-r from-gray-300 via-gray-400 to-gray-500' :
                        'bg-gradient-to-r from-amber-600 via-amber-700 to-amber-800'
                      } opacity-20 blur-xl`}></div>
                      
                      <div className="relative">
                        <BlogPostCard
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
                          onTagClick={handleTagClick}
                        />
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* 구분선 */}
                <div className="relative my-12">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t-2 border-gray-200"></div>
                  </div>
                  <div className="relative flex justify-center">
                    <span className="bg-white px-6 py-2 text-sm text-gray-500 font-medium rounded-full border border-gray-200">
                      More MCP Servers ({remainingPosts.length})
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* View All MCP Servers */}
            {remainingPosts.length > 0 && (
              <div>
                <div className="grid grid-cols-1 gap-x-8 gap-y-16 items-start lg:grid-cols-3">
                  {visibleRemainingPosts.map(({ category, tags, title, desc, date, author, id }) => (
                    <BlogPostCard
                      key={`${id || title}-${refreshKey}`}
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
                      onTagClick={handleTagClick}
                    />
                  ))}
                </div>
              </div>
            )}
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
