"use client";

import Image from "next/image";
import { useState, useEffect } from "react";

interface HeroProps {
  onSearch?: (searchTerm: string) => void;
}

function Hero({ onSearch }: HeroProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [typedPlaceholder, setTypedPlaceholder] = useState("");
  const [isTyping, setIsTyping] = useState(true);
  const [isFocused, setIsFocused] = useState(false);
  const [isVisible, setIsVisible] = useState(false);

  const placeholderText = "find your mcp server";
  const typingSpeed = 100; // 타이핑 속도 (ms)

  useEffect(() => {
    // 페이지 로드 시 페이드인 애니메이션
    setIsVisible(true);
  }, []);

  useEffect(() => {
    let timeout: NodeJS.Timeout;
    
    // 포커스된 상태가 아니고 타이핑 중일 때만 타이핑 효과 실행
    if (!isFocused && isTyping && typedPlaceholder.length < placeholderText.length) {
      timeout = setTimeout(() => {
        setTypedPlaceholder(placeholderText.slice(0, typedPlaceholder.length + 1));
      }, typingSpeed);
    } else if (!isFocused && typedPlaceholder.length === placeholderText.length) {
      // 타이핑 완료 후 잠시 대기
      timeout = setTimeout(() => {
        setIsTyping(false);
        setTypedPlaceholder("");
        setIsTyping(true);
      }, 2000);
    }

    return () => clearTimeout(timeout);
  }, [typedPlaceholder, isTyping, placeholderText, isFocused]);

  const handleSearch = () => {
    if (onSearch && searchTerm.trim()) {
      onSearch(searchTerm.trim());
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleFocus = () => {
    setIsFocused(true);
    setIsTyping(false);
  };

  const handleBlur = () => {
    setIsFocused(false);
    setIsTyping(true);
    setTypedPlaceholder("");
  };

  return (
    <header className="mt-5 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 py-16 relative overflow-hidden">
      {/* 애니메이션 배경 효과 */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-400/10 via-purple-400/10 to-pink-400/10 animate-pulse"></div>
      <div className="absolute top-0 left-0 w-full h-full">
        {/* 배경 애니메이션 요소들 제거됨 */}
      </div>
      
      <div className="container mx-auto flex flex-col justify-center items-center min-h-[320px] text-center relative z-10">
        <h1
          className={`mx-auto w-full text-[30px] lg:text-[48px] font-bold leading-[45px] lg:leading-[60px] text-gray-800 transform transition-all duration-1000 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
          style={{ transitionDelay: '0.2s' }}
        >
          <div className="flex items-center justify-center gap-3">
            <svg 
              className="w-8 h-8 lg:w-12 lg:h-12 text-blue-600 animate-spin" 
              style={{ animationDuration: '3s' }}
              viewBox="0 0 24 24" 
              fill="currentColor"
            >
              <path d="M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.22,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.22,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.68 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z" />
            </svg>
            <span>Where Agents Meet Skills</span>
          </div>
        </h1>
        <p
          className={`mx-auto mt-8 mb-4 w-full px-8 text-gray-600 lg:w-10/12 lg:px-12 xl:w-8/12 xl:px-20 text-lg transform transition-all duration-1000 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
          style={{ transitionDelay: '0.4s' }}
        >
          Join a growing community and explore MCP servers built for every use case.
        </p>
        <div className="grid place-items-start justify-center gap-2">
          <div className={`mt-8 flex flex-col items-center justify-center gap-4 md:flex-row transform transition-all duration-1000 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
          style={{ transitionDelay: '0.6s' }}>
            <div className="w-80">
              <input 
                type="text" 
                placeholder={!isFocused ? (typedPlaceholder + (isTyping ? "|" : "")) : ""} 
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyPress={handleKeyPress}
                onFocus={handleFocus}
                onBlur={handleBlur}
                className="w-full px-4 py-3 bg-white text-gray-800 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-400 shadow-sm transition-all duration-300 hover:shadow-lg hover:scale-105 focus:scale-105"
              />
            </div>
            <button 
              onClick={handleSearch}
              className="px-6 py-2 bg-white text-black font-medium rounded-lg hover:bg-gray-100 transition-all duration-300 lg:w-max shrink-0 w-full hover:scale-105 hover:shadow-lg active:scale-95"
            >
              Search
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
export default Hero;
