"use client";

import React, { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { useLanguage } from "@/contexts/LanguageContext";

export default function ADSignupPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const { t } = useLanguage();
  
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
        throw new Error(errorData.detail || t('signup.error'));
      }

      const result = await response.json();
      
      // AuthContext를 통해 로그인 처리
      login(result.access_token, result.user);
      
      // 메인 페이지로 이동
      router.push('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : t('signup.unknownError'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            {t('signup.title')}
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            {t('signup.subtitle')}
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
                {t('signup.knoxId')}
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
                {t('signup.nickname')} *
              </label>
              <input
                id="nickname"
                name="nickname"
                type="text"
                required
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder={t('signup.nicknamePlaceholder')}
                value={formData.nickname}
                onChange={(e) => handleInputChange('nickname', e.target.value)}
              />
              <p className="mt-1 text-xs text-gray-500">{t('signup.nicknameHelp')}</p>
            </div>

            {/* Bio (입력 가능) */}
            <div>
              <label htmlFor="bio" className="block text-sm font-medium text-gray-700">
                {t('signup.bio')}
              </label>
              <textarea
                id="bio"
                name="bio"
                rows={3}
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder={t('signup.bioPlaceholder')}
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
              {isLoading ? t('signup.submitting') : t('signup.submit')}
            </button>
          </div>

          <div className="text-center">
            <Link href="/login" className="text-sm text-blue-600 hover:text-blue-500">
              {t('signup.backToLogin')}
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
