"use client";

import React, { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

export default function AuthSuccessPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const [isProcessing, setIsProcessing] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = searchParams.get('token');
    
    if (!token) {
      setError("인증 토큰을 찾을 수 없습니다.");
      setIsProcessing(false);
      return;
    }

    // 토큰을 사용하여 사용자 정보 가져오기
    const fetchUserInfo = async () => {
      try {
        const response = await fetch('/api/v1/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error('사용자 정보를 가져올 수 없습니다.');
        }

        const user = await response.json();
        
        // AuthContext를 통해 로그인 처리
        login(token, user);
        
        // 성공 메시지 표시 후 메인 페이지로 이동
        setTimeout(() => {
          router.push('/');
        }, 2000);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.');
        setIsProcessing(false);
      }
    };

    fetchUserInfo();
  }, [searchParams, login, router]);

  if (isProcessing) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <h2 className="text-xl font-semibold text-gray-900">
            로그인 처리 중...
          </h2>
          <p className="text-gray-600">
            잠시만 기다려주세요.
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8 text-center">
          <div className="rounded-md bg-red-50 p-4">
            <div className="text-sm text-red-700">{error}</div>
          </div>
          <button
            onClick={() => router.push('/login')}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            로그인 페이지로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 text-center">
        <div className="rounded-md bg-green-50 p-4">
          <div className="text-sm text-green-700">
            로그인에 성공했습니다! 메인 페이지로 이동합니다.
          </div>
        </div>
      </div>
    </div>
  );
} 