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

  const placeholderText = "find your mcp server";
  const typingSpeed = 100; // 타이핑 속도 (ms)

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
    <header className="mt-5 bg-black py-16">
      <div className="container mx-auto flex flex-col justify-center items-center min-h-[320px] text-center">
        <h1
          className="mx-auto w-full text-[30px] lg:text-[48px] font-bold leading-[45px] lg:leading-[60px] text-white"
        >
          Where Agents Meet Skills
        </h1>
        <p
          className="mx-auto mt-8 mb-4 w-full px-8 text-gray-300 lg:w-10/12 lg:px-12 xl:w-8/12 xl:px-20 text-lg"
        >
          Join a growing community and explore MCP servers built for every use case.
        </p>
        <div className="grid place-items-start justify-center gap-2">
          <div className="mt-8 flex flex-col items-center justify-center gap-4 md:flex-row">
            <div className="w-80">
              <input 
                type="text" 
                placeholder={!isFocused ? (typedPlaceholder + (isTyping ? "|" : "")) : ""} 
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyPress={handleKeyPress}
                onFocus={handleFocus}
                onBlur={handleBlur}
                className="w-full px-3 py-2 bg-gray-800 text-white border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400"
              />
            </div>
            <button 
              onClick={handleSearch}
              className="px-6 py-2 bg-white text-black font-medium rounded-lg hover:bg-gray-100 transition-colors lg:w-max shrink-0 w-full"
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
