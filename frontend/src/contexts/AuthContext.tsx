"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { setLogoutCallback } from '@/lib/api-client';

interface User {
  id: number;
  username: string;
  email: string;
  nickname: string;
  is_admin: string;
  avatar_url?: string;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string, user: User) => void;
  logout: () => void;
  isAuthenticated: boolean;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// JWT 토큰의 만료 여부를 확인하는 함수
function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const exp = payload.exp;
    
    if (!exp) {
      return true;
    }
    
    // exp는 초 단위이므로 밀리초로 변환하여 비교
    const currentTime = Date.now() / 1000;
    return exp < currentTime;
  } catch (error) {
    console.error('Failed to decode token:', error);
    return true;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  };

  useEffect(() => {
    // API 클라이언트에 로그아웃 콜백 등록
    setLogoutCallback(logout);
  }, []);

  useEffect(() => {
    // 페이지 로드 시 localStorage에서 인증 정보 복원
    const storedToken = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    
    if (storedToken && storedUser) {
      try {
        // 토큰 만료 확인
        if (isTokenExpired(storedToken)) {
          console.log('Token has expired, clearing authentication');
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          return;
        }
        
        const userData = JSON.parse(storedUser);
        setToken(storedToken);
        setUser(userData);
      } catch (error) {
        console.error('Failed to parse stored user data:', error);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
    }
  }, []);

  const login = (newToken: string, userData: User) => {
    setToken(newToken);
    setUser(userData);
    localStorage.setItem('token', newToken);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  // 토큰이 있고 사용자 정보가 있으며, 토큰이 만료되지 않았을 때만 인증됨
  const isAuthenticated = !!token && !!user && !isTokenExpired(token);
  const isAdmin = user?.is_admin === 'admin';

  return (
    <AuthContext.Provider value={{
      user,
      token,
      login,
      logout,
      isAuthenticated,
      isAdmin,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
} 