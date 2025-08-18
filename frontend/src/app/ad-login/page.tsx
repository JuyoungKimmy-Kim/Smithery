"use client";

import React, { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function ADLoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isProcessing, setIsProcessing] = useState(true);
  const [message, setMessage] = useState("AD 인증을 처리하고 있습니다...");

  useEffect(() => {
    // URL 파라미터에서 username과 email을 받아옴 (실제 AD 로그인에서는 여기서 받음)
    const username = searchParams.get('username') || 'ad_user_' + Math.random().toString(36).substr(2, 9);
    const email = searchParams.get('email') || username + '@company.com';

    // AD 인증 처리 시뮬레이션
    const simulateADAuth = async () => {
      try {
        setMessage("AD 서버에 인증 요청 중...");
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        setMessage("사용자 정보 검증 중...");
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        setMessage("인증 완료! 메인 페이지로 리다이렉트 중...");
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // 메인 페이지로 리다이렉트하면서 username과 email 정보 전달
        router.push(`/?ad_auth=success&username=${encodeURIComponent(username)}&email=${encodeURIComponent(email)}`);
      } catch (error) {
        setMessage("AD 인증 중 오류가 발생했습니다.");
        setTimeout(() => {
          router.push('/login');
        }, 2000);
      }
    };

    simulateADAuth();
  }, [router, searchParams]);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            AD 로그인
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Active Directory 인증을 처리하고 있습니다
          </p>
        </div>
        
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
          <p className="mt-4 text-center text-gray-700">{message}</p>
        </div>
        
        <div className="text-center">
          <button
            onClick={() => router.push('/login')}
            className="text-sm text-blue-600 hover:text-blue-500"
          >
            로그인 페이지로 돌아가기
          </button>
        </div>
      </div>
    </div>
  );
} 