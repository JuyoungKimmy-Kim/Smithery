"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useLanguage } from "@/contexts/LanguageContext";
import { useRouter } from "next/navigation";
import BlogPostCard from "@/components/blog-post-card";
import AdminServerCard from "@/components/admin-server-card";
import { apiFetch } from "@/lib/api-client";
import { Notification } from "@/types/notification";

interface Post {
  category: string;
  tags: string;
  title: string;
  desc: string;
  date: string;
  status?: string; // status 추가
  health_status?: string; // health status 추가
  author: {
    img: string;
    name: string;
  };
  id?: string;
  favorites_count?: number;
}

export default function MyPage() {
  const { user, isAuthenticated } = useAuth();
  const { t } = useLanguage();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState("notifications");
  const [myServers, setMyServers] = useState<Post[]>([]);
  const [favorites, setFavorites] = useState<Post[]>([]);
  const [pendingServers, setPendingServers] = useState<Post[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
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

        // 알림 가져오기
        const notificationsResponse = await apiFetch('/api/notifications?limit=50', {
          requiresAuth: true
        });

        console.log('Notifications response status:', notificationsResponse.status);

        if (notificationsResponse.ok) {
          const notificationsData = await notificationsResponse.json();
          console.log('Notifications data:', notificationsData);
          setNotifications(notificationsData);
        } else {
          const errorText = await notificationsResponse.text();
          console.error('Notifications error:', errorText);
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
            {t('mypage.title')}
          </h1>
          <p className="text-gray-600">
            {t('mypage.welcome', { username: user?.username || '' })}
          </p>
        </div>

        {/* 탭 네비게이션 */}
        <div className="mb-8">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab("notifications")}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === "notifications"
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                Notifications ({notifications.length})
              </button>
              <button
                onClick={() => setActiveTab("my-servers")}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === "my-servers"
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                {t('mypage.myServers')} ({myServers.length})
              </button>
              <button
                onClick={() => setActiveTab("favorites")}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === "favorites"
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                {t('mypage.favorites')} ({favorites.length})
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
                  {t('mypage.pending')} ({pendingServers.length})
                </button>
              )}
            </nav>
          </div>
        </div>

        {/* 콘텐츠 */}
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-lg text-gray-600">{t('mypage.loading')}</div>
          </div>
        ) : (
          <div className="space-y-8">
            {activeTab === "my-servers" && (
              <div>
                {myServers.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="text-gray-400 text-6xl mb-4">📝</div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      {t('mypage.noServers')}
                    </h3>
                    <p className="text-gray-600 mb-4">
                      {t('mypage.noServersDesc')}
                    </p>
                    <button
                      onClick={() => router.push('/submit')}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
                    >
                      {t('mypage.registerServer')}
                    </button>
                  </div>
                ) : (
                  <div className="space-y-12">
                    {/* 승인 대기중인 서버 */}
                    {myServers.filter(s => s.status === 'pending').length > 0 && (
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-6">
                          {t('mypage.pendingServers', { count: String(myServers.filter(s => s.status === 'pending').length) })}
                        </h3>
                        <div className="grid grid-cols-1 gap-x-8 gap-y-16 items-start lg:grid-cols-3">
                          {myServers.filter(s => s.status === 'pending').map((server) => (
                            <BlogPostCard
                              key={server.id || server.title}
                              category={server.category}
                              tags={server.tags}
                              title={server.title}
                              desc={server.desc}
                              date={server.date}
                              status={server.status}
                              healthStatus={server.health_status}
                              author={server.author}
                              id={server.id}
                              favoritesCount={server.favorites_count || 0}
                            />
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 등록된 서버 (승인된 서버) */}
                    {myServers.filter(s => s.status !== 'pending').length > 0 && (
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-6">
                          {t('mypage.approvedServers', { count: String(myServers.filter(s => s.status !== 'pending').length) })}
                        </h3>
                        <div className="grid grid-cols-1 gap-x-8 gap-y-16 items-start lg:grid-cols-3">
                          {myServers.filter(s => s.status !== 'pending').map((server) => (
                            <BlogPostCard
                              key={server.id || server.title}
                              category={server.category}
                              tags={server.tags}
                              title={server.title}
                              desc={server.desc}
                              date={server.date}
                              status={server.status}
                              healthStatus={server.health_status}
                              author={server.author}
                              id={server.id}
                              favoritesCount={server.favorites_count || 0}
                            />
                          ))}
                        </div>
                      </div>
                    )}
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
                      {t('mypage.noFavorites')}
                    </h3>
                    <p className="text-gray-600 mb-4">
                      {t('mypage.noFavoritesDesc')}
                    </p>
                    <button
                      onClick={() => router.push('/')}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
                    >
                      {t('mypage.browse')}
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
                        healthStatus={server.health_status}
                        author={server.author}
                        id={server.id}
                        favoritesCount={server.favorites_count || 0}
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
                      {t('mypage.noPending')}
                    </h3>
                    <p className="text-gray-600 mb-4">
                      {t('mypage.noPendingDesc')}
                    </p>
                  </div>
                ) : (
                  <div>
                    <div className="mb-6 flex justify-between items-center">
                      <h3 className="text-lg font-medium text-gray-900">
                        {t('mypage.pendingCount', { count: pendingServers.length.toString() })}
                      </h3>
                      <button
                        onClick={handleBulkApprove}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                      >
                        {t('mypage.approveAll')}
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

            {activeTab === "notifications" && (
              <NotificationsTab
                notifications={notifications}
                onNotificationsChange={(updatedNotifications) => setNotifications(updatedNotifications)}
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Notifications Tab Component
function NotificationsTab({
  notifications,
  onNotificationsChange
}: {
  notifications: Notification[];
  onNotificationsChange: (notifications: Notification[]) => void;
}) {
  const router = useRouter();
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  const filteredNotifications = filter === 'unread'
    ? notifications.filter(n => !n.is_read)
    : notifications;

  const markAsRead = async (notificationId: number) => {
    try {
      await apiFetch(`/api/notifications/${notificationId}/read`, {
        method: 'POST',
        requiresAuth: true
      });

      onNotificationsChange(
        notifications.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
      );
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await apiFetch('/api/notifications/read-all', {
        method: 'POST',
        requiresAuth: true
      });

      onNotificationsChange(notifications.map(n => ({ ...n, is_read: true })));
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    }
  };

  const handleNotificationClick = (notification: Notification) => {
    if (!notification.is_read) {
      markAsRead(notification.id);
    }

    if (notification.mcp_server_id) {
      router.push(`/mcp/${notification.mcp_server_id}`);
    }
  };

  const getRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffHours < 24) return `${diffHours} hr ago`;
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString('en-US');
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'comment': return '💬';
      case 'favorite': return '⭐';
      case 'status_change': return '✅';
      case 'new_mcp': return '🆕';
      default: return '🔔';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm">
      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {/* Filter Tabs */}
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              All ({notifications.length})
            </button>
            <button
              onClick={() => setFilter('unread')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === 'unread'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Unread ({notifications.filter(n => !n.is_read).length})
            </button>
          </div>

          {/* Mark All as Read Button */}
          {notifications.some(n => !n.is_read) && (
            <button
              onClick={markAllAsRead}
              className="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors"
            >
              Mark all as read
            </button>
          )}
        </div>
      </div>

      {/* Notifications List */}
      <div>
        {filteredNotifications.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <div className="text-6xl mb-4">🔔</div>
            <p className="text-gray-500 text-lg">
              {filter === 'unread' ? 'No unread notifications' : 'No notifications'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {filteredNotifications.map((notification) => (
              <div
                key={notification.id}
                onClick={() => handleNotificationClick(notification)}
                className={`px-6 py-4 cursor-pointer transition-colors ${
                  notification.is_read
                    ? 'bg-white hover:bg-gray-50'
                    : 'bg-blue-50 hover:bg-blue-100'
                }`}
              >
                <div className="flex items-start gap-4">
                  <div className="text-3xl flex-shrink-0">
                    {getNotificationIcon(notification.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm ${notification.is_read ? 'text-gray-700' : 'text-gray-900 font-medium'}`}>
                      {notification.message}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {getRelativeTime(notification.created_at)}
                    </p>
                  </div>
                  {!notification.is_read && (
                    <div className="flex-shrink-0">
                      <div className="w-2.5 h-2.5 bg-blue-600 rounded-full"></div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
} 