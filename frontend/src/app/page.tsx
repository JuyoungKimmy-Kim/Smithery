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
    // AD 로그인 후 돌아온 경우 처리
    const adAuth = searchParams.get('ad_auth');
    
    if (adAuth === 'success') {
      // AD 로그인 성공
      const token = searchParams.get('token');
      const userId = searchParams.get('user_id');
      const username = searchParams.get('username');
      const email = searchParams.get('email');
      
      if (token && userId && username && email) {
        console.log('AD 로그인 성공:', { userId, username, email });
        
        // 사용자 정보 구성
        const user = {
          id: parseInt(userId),
          username: username,
          email: email,
          is_admin: "user",
          avatar_url: undefined,
          created_at: new Date().toISOString()
        };
        
        // AuthContext를 통해 로그인 처리
        login(token, user);
        
        alert('AD 로그인에 성공했습니다!');
        
        // URL 파라미터 제거
        router.replace('/');
      }
    } else if (adAuth === 'error') {
      // AD 로그인 실패
      const errorMessage = searchParams.get('error_message');
      console.error('AD 로그인 실패:', errorMessage);
      
      alert(`AD 로그인에 실패했습니다: ${errorMessage}`);
      
      // URL 파라미터 제거
      router.replace('/');
    }
  }, [searchParams, login, router]);

  return (
    <>
      <Hero onSearch={handleSearch} />
      <Posts searchTerm={searchTerm} />
    </>
  );
}
