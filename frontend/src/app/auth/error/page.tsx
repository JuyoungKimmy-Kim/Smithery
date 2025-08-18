"use client";

import React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";

export default function AuthErrorPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const errorMessage = searchParams.get('message') || '알 수 없는 오류가 발생했습니다.';

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 text-center">
        <div className="rounded-md bg-red-50 p-4">
          <div className="text-sm text-red-700">
            <strong>로그인 오류</strong>
            <br />
            {errorMessage}
          </div>
        </div>
        
        <div className="space-y-4">
          <button
            onClick={() => router.push('/api/v1/oidc/login')}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            다시 시도하기
          </button>
          
          <Link
            href="/login"
            className="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            일반 로그인으로 돌아가기
          </Link>
        </div>
        
        <div className="text-center">
          <Link href="/" className="text-sm text-blue-600 hover:text-blue-500">
            메인 페이지로 돌아가기
          </Link>
        </div>
      </div>
    </div>
  );
} 