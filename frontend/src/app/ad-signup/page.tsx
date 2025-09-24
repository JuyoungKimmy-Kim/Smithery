"use client";

import React, { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";

export default function ADSignupPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    nickname: "",
    bio: "",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    // URL 파라미터에서 AD 로그인으로 받은 정보를 가져옴
    const username = searchParams.get('username');
    const email = searchParams.get('email');
    
    if (!username || !email) {
      // AD 로그인 정보가 없으면 로그인 페이지로 리다이렉트
      router.push('/login');
      return;
    }
    
    setFormData(prev => ({
      ...prev,
      username,
      email
    }));
  }, [searchParams, router]);

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    if (error) setError("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      const response = await fetch('/api/auth/ad-signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '회원가입에 실패했습니다.');
      }

      const result = await response.json();
      
      // AuthContext를 통해 로그인 처리
      login(result.access_token, result.user);
      
      // 메인 페이지로 이동
      router.push('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            회원가입
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            추가 정보를 입력하여 회원가입을 완료하세요
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="text-sm text-red-700">{error}</div>
            </div>
          )}
          
          <div className="space-y-4">
            {/* Username (읽기 전용) */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                Knox ID
              </label>
              <input
                id="username"
                name="username"
                type="text"
                disabled
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-500 bg-gray-100 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                value={formData.username}
              />
            </div>

            {/* Nickname (입력 가능) */}
            <div>
              <label htmlFor="nickname" className="block text-sm font-medium text-gray-700">
                닉네임 *
              </label>
              <input
                id="nickname"
                name="nickname"
                type="text"
                required
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="닉네임을 입력하세요"
                value={formData.nickname}
                onChange={(e) => handleInputChange('nickname', e.target.value)}
              />
              <p className="mt-1 text-xs text-gray-500">닉네임은 공개됩니다. 비속어, 혐오 표현 사용은 제한됩니다.</p>
            </div>

            {/* Bio (입력 가능) */}
            <div>
              <label htmlFor="bio" className="block text-sm font-medium text-gray-700">
                자기소개
              </label>
              <textarea
                id="bio"
                name="bio"
                rows={3}
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="자기소개를 입력하세요 (선택사항)"
                value={formData.bio}
                onChange={(e) => handleInputChange('bio', e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-3">
            <button
              type="submit"
              disabled={isLoading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? '회원가입 중...' : '회원가입 완료'}
            </button>
          </div>

          <div className="text-center">
            <Link href="/login" className="text-sm text-blue-600 hover:text-blue-500">
              로그인 페이지로 돌아가기
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
