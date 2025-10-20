"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";
import BlogPostCard from "@/components/blog-post-card";
import AdminServerCard from "@/components/admin-server-card";
import { apiFetch } from "@/lib/api-client";

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

export default function MyPage() {
  const { user, isAuthenticated } = useAuth();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState("my-servers");
  const [myServers, setMyServers] = useState<Post[]>([]);
  const [favorites, setFavorites] = useState<Post[]>([]);
  const [pendingServers, setPendingServers] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  
  const isAdmin = user?.is_admin === "admin";

  // 승인/거부 후 목록에서 제거
  const handleApprove = (serverId: string) => {
    setPendingServers(prev => prev.filter(server => server.id !== serverId));
  };

  const handleReject = (serverId: string) => {
    setPendingServers(prev => prev.filter(server => server.id !== serverId));
  };

  // 일괄 승인
  const handleBulkApprove = async () => {
    if (pendingServers.length === 0) return;
    
    if (!confirm(`모든 ${pendingServers.length}개의 서버를 승인하시겠습니까?`)) {
      return;
    }

    const token = localStorage.getItem('token');
    if (!token) {
      alert('로그인이 필요합니다.');
      return;
    }

    try {
      console.log('Starting bulk approve for', pendingServers.length, 'servers');
      
      const response = await apiFetch('/api/mcp-servers/admin/approve-all', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        requiresAuth: true
      });

      const responseData = await response.json();
      console.log('Bulk approve response:', responseData);

      if (response.ok) {
        alert(responseData.message || '모든 서버가 승인되었습니다.');
        setPendingServers([]);
      } else {
        alert('일괄 승인에 실패했습니다: ' + (responseData.error || '알 수 없는 오류'));
      }
    } catch (error) {
      console.error('Bulk approve error:', error);
      alert('일괄 승인 중 오류가 발생했습니다.');
    }
  };

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    const fetchData = async () => {
      try {
        console.log('Fetching user data...');
        const token = localStorage.getItem('token');
        console.log('Token:', token ? 'exists' : 'not found');
        
        if (!token) {
          console.error('No token found, redirecting to login');
          router.push('/login');
          return;
        }
        
        // 내가 등록한 서버 가져오기
        const myServersResponse = await apiFetch('/api/mcp-servers/user/my-servers', {
          requiresAuth: true
        });
        
        console.log('My servers response status:', myServersResponse.status);
        
        if (myServersResponse.ok) {
          const myServersData = await myServersResponse.json();
          console.log('My servers data:', myServersData);
          setMyServers(myServersData);
        } else {
          const errorText = await myServersResponse.text();
          console.error('My servers error:', errorText);
        }

        // 즐겨찾기한 서버 가져오기
        const favoritesResponse = await apiFetch('/api/mcp-servers/user/favorites', {
          requiresAuth: true
        });
        
        console.log('Favorites response status:', favoritesResponse.status);
        
        if (favoritesResponse.ok) {
          const favoritesData = await favoritesResponse.json();
          console.log('Favorites data:', favoritesData);
          setFavorites(favoritesData);
        } else {
          const errorText = await favoritesResponse.text();
          console.error('Favorites error:', errorText);
        }

        // Admin인 경우 승인 대기중인 서버 가져오기
        if (isAdmin) {
          const pendingResponse = await apiFetch('/api/mcp-servers/admin/pending', {
            requiresAuth: true
          });
          
          console.log('Pending servers response status:', pendingResponse.status);
          
          if (pendingResponse.ok) {
            const pendingData = await pendingResponse.json();
            console.log('Pending servers data:', pendingData);
            setPendingServers(pendingData);
          } else {
            const errorText = await pendingResponse.text();
            console.error('Pending servers error:', errorText);
          }
        }
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [isAuthenticated, router]);

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 헤더 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            My Page
          </h1>
          <p className="text-gray-600">
            안녕하세요, {user?.username}님! 등록한 서버와 즐겨찾기를 관리하세요.
          </p>
        </div>

        {/* 탭 네비게이션 */}
        <div className="mb-8">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab("my-servers")}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === "my-servers"
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                내가 등록한 서버 ({myServers.length})
              </button>
              <button
                onClick={() => setActiveTab("favorites")}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === "favorites"
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                즐겨찾기 ({favorites.length})
              </button>
              {isAdmin && (
                <button
                  onClick={() => setActiveTab("pending")}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === "pending"
                      ? "border-blue-500 text-blue-600"
                      : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                  }`}
                >
                  승인 대기중 ({pendingServers.length})
                </button>
              )}
            </nav>
          </div>
        </div>

        {/* 콘텐츠 */}
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-lg text-gray-600">로딩 중...</div>
          </div>
        ) : (
          <div className="space-y-8">
            {activeTab === "my-servers" && (
              <div>
                {myServers.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="text-gray-400 text-6xl mb-4">📝</div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      등록한 서버가 없습니다
                    </h3>
                    <p className="text-gray-600 mb-4">
                      새로운 MCP 서버를 등록해보세요!
                    </p>
                    <button
                      onClick={() => router.push('/submit')}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
                    >
                      서버 등록하기
                    </button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 gap-x-8 gap-y-16 items-start lg:grid-cols-3">
                    {myServers.map((server) => (
                      <BlogPostCard
                        key={server.id || server.title}
                        category={server.category}
                        tags={server.tags}
                        title={server.title}
                        desc={server.desc}
                        date={server.date}
                        author={server.author}
                        id={server.id}
                      />
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === "favorites" && (
              <div>
                {favorites.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="text-gray-400 text-6xl mb-4">⭐</div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      즐겨찾기한 서버가 없습니다
                    </h3>
                    <p className="text-gray-600 mb-4">
                      마음에 드는 MCP 서버에 즐겨찾기를 추가해보세요!
                    </p>
                    <button
                      onClick={() => router.push('/')}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
                    >
                      서버 둘러보기
                    </button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 gap-x-8 gap-y-16 items-start lg:grid-cols-3">
                    {favorites.map((server) => (
                      <BlogPostCard
                        key={server.id || server.title}
                        category={server.category}
                        tags={server.tags}
                        title={server.title}
                        desc={server.desc}
                        date={server.date}
                        author={server.author}
                        id={server.id}
                      />
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === "pending" && (
              <div>
                {pendingServers.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="text-gray-400 text-6xl mb-4">⏳</div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      승인 대기중인 서버가 없습니다
                    </h3>
                    <p className="text-gray-600 mb-4">
                      모든 MCP 서버가 승인되었습니다.
                    </p>
                  </div>
                ) : (
                  <div>
                    <div className="mb-6 flex justify-between items-center">
                      <h3 className="text-lg font-medium text-gray-900">
                        승인 대기중인 서버 ({pendingServers.length}개)
                      </h3>
                      <button
                        onClick={handleBulkApprove}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                      >
                        전체 승인
                      </button>
                    </div>
                    <div className="grid grid-cols-1 gap-x-8 gap-y-16 items-start lg:grid-cols-3">
                      {pendingServers.map((server) => (
                        <AdminServerCard
                          key={server.id || server.title}
                          category={server.category}
                          tags={server.tags}
                          title={server.title}
                          desc={server.desc}
                          date={server.date}
                          author={server.author}
                          id={server.id}
                          onApprove={handleApprove}
                          onReject={handleReject}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
} 