"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
// components
// sections
import Hero from "./hero";
import Posts from "./posts";

export default function Campaign() {
  const [searchTerm, setSearchTerm] = useState("");
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();

  const handleSearch = (term: string) => {
    setSearchTerm(term);
  };

  useEffect(() => {
    // AD 인증 후 돌아온 경우 처리
    const adAuth = searchParams.get('ad_auth');
    const username = searchParams.get('username');
    const email = searchParams.get('email');

    if (adAuth === 'success' && username && email) {
      console.log('AD 인증 성공:', { username, email });
      
      // AD 로그인 API 호출
      const handleADLogin = async () => {
        try {
          const response = await fetch('/api/auth/ad-login', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, email }),
          });

          if (response.ok) {
            const result = await response.json();
            
            // AuthContext를 통해 로그인 처리
            login(result.access_token, result.user);
            
            alert('AD 로그인에 성공했습니다!');
            
            // URL 파라미터 제거
            router.replace('/');
          } else {
            const errorData = await response.json();
            alert(`AD 로그인 실패: ${errorData.detail}`);
            router.replace('/');
          }
        } catch (error) {
          console.error('AD 로그인 처리 중 오류:', error);
          alert('AD 로그인 처리 중 오류가 발생했습니다.');
          router.replace('/');
        }
      };

      handleADLogin();
    }
  }, [searchParams, login, router]);

  return (
    <>
      <Hero onSearch={handleSearch} />
      <Posts searchTerm={searchTerm} />
    </>
  );
}
