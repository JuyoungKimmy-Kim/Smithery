"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

type Language = 'ko' | 'en';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string, params?: Record<string, string>) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

// 번역 데이터
const translations: Record<Language, Record<string, string>> = {
  ko: {
    // Navbar
    'nav.register': 'Register',
    'nav.mypage': 'My Page',
    'nav.signout': 'Sign Out',
    'nav.signin': 'Sign In',
    'nav.signInRequired': '로그인 필요',
    'nav.signInRequiredDesc': '새로운 MCP 서버를 등록하려면 로그인이 필요합니다.',
    'nav.cancel': '취소',
    'nav.wiki': 'Wiki',
    'nav.gettingStarted': 'Getting Started',
    'nav.howToUse': 'How to Use',
    'nav.roadmap': 'Roadmap',
    
    // MyPage
    'mypage.title': 'My Page',
    'mypage.welcome': '안녕하세요, {username}님! 등록한 서버와 즐겨찾기를 관리하세요.',
    'mypage.myServers': '내가 등록한 서버',
    'mypage.favorites': '즐겨찾기',
    'mypage.pending': '승인 대기중',
    'mypage.loading': '로딩 중...',
    'mypage.noServers': '등록한 서버가 없습니다',
    'mypage.noServersDesc': '새로운 MCP 서버를 등록해보세요!',
    'mypage.registerServer': '서버 등록하기',
    'mypage.noFavorites': '즐겨찾기한 서버가 없습니다',
    'mypage.noFavoritesDesc': '마음에 드는 MCP 서버에 즐겨찾기를 추가해보세요!',
    'mypage.browse': '서버 둘러보기',
    'mypage.noPending': '승인 대기중인 서버가 없습니다',
    'mypage.noPendingDesc': '모든 MCP 서버가 승인되었습니다.',
    'mypage.pendingCount': '승인 대기중인 서버 ({count}개)',
    'mypage.approveAll': '전체 승인',
    
    // User Page
    'userpage.loading': '{username}의 서버 목록을 불러오는 중...',
    'userpage.userNotFound': '사용자를 찾을 수 없습니다.',
    'userpage.loadError': '서버 목록을 불러오는 중 오류가 발생했습니다.',
    'userpage.goBack': '뒤로 가기',
    'userpage.title': '{username}의 MCP 서버',
    'userpage.totalServers': '총 {count}개의 서버가 등록되어 있습니다.',
    'userpage.noServers': '등록된 MCP 서버가 없습니다.',
    'userpage.viewMore': 'VIEW MORE',
    
    // Comments
    'comments.title': '댓글',
    'comments.writeComment': '댓글을 작성해주세요...',
    'comments.loginRequired': '댓글을 작성하려면 로그인해주세요.',
    'comments.submitting': '작성 중...',
    'comments.submit': '작성',
    'comments.loading': '댓글을 불러오는 중...',
    'comments.noComments': '아직 댓글이 없습니다. 첫 번째 댓글을 작성해보세요!',
    'comments.edited': '(수정됨)',
    'comments.save': '저장',
    'comments.cancel': '취소',
    'comments.edit': '수정',
    'comments.delete': '삭제',
    'comments.deleteConfirm': '댓글을 삭제하시겠습니까?',
    'comments.justNow': '방금 전',
    'comments.hoursAgo': '{hours}시간 전',
    'comments.writeError': '댓글 작성 실패: {error}',
    'comments.writeErrorUnknown': '댓글 작성 중 오류가 발생했습니다.',
    'comments.editError': '댓글 수정 실패: {error}',
    'comments.editErrorUnknown': '댓글 수정 중 오류가 발생했습니다.',
    'comments.deleteError': '댓글 삭제 실패: {error}',
    'comments.deleteErrorUnknown': '댓글 삭제 중 오류가 발생했습니다.',
    
    // Signup Page
    'signup.title': '회원가입',
    'signup.subtitle': '추가 정보를 입력하여 회원가입을 완료하세요',
    'signup.knoxId': 'Knox ID',
    'signup.nickname': '닉네임',
    'signup.nicknamePlaceholder': '닉네임을 입력하세요',
    'signup.nicknameHelp': '닉네임은 공개됩니다. 비속어, 혐오 표현 사용은 제한됩니다.',
    'signup.bio': '자기소개',
    'signup.bioPlaceholder': '자기소개를 입력하세요 (선택사항)',
    'signup.submitting': '회원가입 중...',
    'signup.submit': '회원가입 완료',
    'signup.backToLogin': '로그인 페이지로 돌아가기',
    'signup.error': '회원가입에 실패했습니다.',
    'signup.unknownError': '알 수 없는 오류가 발생했습니다.',
    
    // Main Page Ranking
    'ranking.top3': 'Top 3',
    'ranking.latest': '최신 등록',
    'ranking.topUsers': 'Top Users',
    'ranking.favorites': 'favorites',
    'ranking.servers': 'servers',
    'ranking.viewDetails': 'VIEW',
    'ranking.mcpDeveloper': 'MCP 서버 개발자',
    'ranking.serverCount': '{count}개 서버',
    'ranking.developer': '개발자',
    'ranking.viewProfile': 'VIEW',
  },
  en: {
    // Navbar
    'nav.register': 'Register',
    'nav.mypage': 'My Page',
    'nav.signout': 'Sign Out',
    'nav.signin': 'Sign In',
    'nav.signInRequired': 'Sign In Required',
    'nav.signInRequiredDesc': 'You need to sign in to register a new MCP server.',
    'nav.cancel': 'Cancel',
    'nav.wiki': 'Wiki',
    'nav.gettingStarted': 'Getting Started',
    'nav.howToUse': 'How to Use',
    'nav.roadmap': 'Roadmap',
    
    // MyPage
    'mypage.title': 'My Page',
    'mypage.welcome': 'Welcome, {username}! Manage your registered servers and favorites.',
    'mypage.myServers': 'My Servers',
    'mypage.favorites': 'Favorites',
    'mypage.pending': 'Pending Approval',
    'mypage.loading': 'Loading...',
    'mypage.noServers': 'No registered servers',
    'mypage.noServersDesc': 'Register a new MCP server!',
    'mypage.registerServer': 'Register Server',
    'mypage.noFavorites': 'No favorite servers',
    'mypage.noFavoritesDesc': 'Add your favorite MCP servers to your favorites!',
    'mypage.browse': 'Browse Servers',
    'mypage.noPending': 'No pending servers',
    'mypage.noPendingDesc': 'All MCP servers have been approved.',
    'mypage.pendingCount': 'Pending Servers ({count})',
    'mypage.approveAll': 'Approve All',
    
    // User Page
    'userpage.loading': 'Loading {username}\'s servers...',
    'userpage.userNotFound': 'User not found.',
    'userpage.loadError': 'An error occurred while loading the server list.',
    'userpage.goBack': 'Go Back',
    'userpage.title': '{username}\'s MCP Servers',
    'userpage.totalServers': 'Total {count} servers registered.',
    'userpage.noServers': 'No MCP servers registered.',
    'userpage.viewMore': 'VIEW MORE',
    
    // Comments
    'comments.title': 'Comments',
    'comments.writeComment': 'Write a comment...',
    'comments.loginRequired': 'Please log in to write a comment.',
    'comments.submitting': 'Submitting...',
    'comments.submit': 'Submit',
    'comments.loading': 'Loading comments...',
    'comments.noComments': 'No comments yet. Be the first to comment!',
    'comments.edited': '(edited)',
    'comments.save': 'Save',
    'comments.cancel': 'Cancel',
    'comments.edit': 'Edit',
    'comments.delete': 'Delete',
    'comments.deleteConfirm': 'Are you sure you want to delete this comment?',
    'comments.justNow': 'Just now',
    'comments.hoursAgo': '{hours} hours ago',
    'comments.writeError': 'Failed to write comment: {error}',
    'comments.writeErrorUnknown': 'An error occurred while writing the comment.',
    'comments.editError': 'Failed to edit comment: {error}',
    'comments.editErrorUnknown': 'An error occurred while editing the comment.',
    'comments.deleteError': 'Failed to delete comment: {error}',
    'comments.deleteErrorUnknown': 'An error occurred while deleting the comment.',
    
    // Signup Page
    'signup.title': 'Sign Up',
    'signup.subtitle': 'Complete your registration by entering additional information',
    'signup.knoxId': 'Knox ID',
    'signup.nickname': 'Nickname',
    'signup.nicknamePlaceholder': 'Enter your nickname',
    'signup.nicknameHelp': 'Your nickname will be public. Profanity and hate speech are prohibited.',
    'signup.bio': 'Bio',
    'signup.bioPlaceholder': 'Enter your bio (optional)',
    'signup.submitting': 'Signing up...',
    'signup.submit': 'Complete Sign Up',
    'signup.backToLogin': 'Back to Login',
    'signup.error': 'Sign up failed.',
    'signup.unknownError': 'An unknown error occurred.',
    
    // Main Page Ranking
    'ranking.top3': 'Top 3',
    'ranking.latest': 'Latest',
    'ranking.topUsers': 'Top Users',
    'ranking.favorites': 'favorites',
    'ranking.servers': 'servers',
    'ranking.viewDetails': 'VIEW',
    'ranking.mcpDeveloper': 'MCP Server Developer',
    'ranking.serverCount': '{count} servers',
    'ranking.developer': 'Developer',
    'ranking.viewProfile': 'VIEW',
  },
};

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>('ko');

  useEffect(() => {
    // 페이지 로드 시 localStorage에서 언어 설정 복원
    const storedLanguage = localStorage.getItem('language') as Language;
    if (storedLanguage && (storedLanguage === 'ko' || storedLanguage === 'en')) {
      setLanguageState(storedLanguage);
    }
  }, []);

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem('language', lang);
  };

  const t = (key: string, params?: Record<string, string>) => {
    let text = translations[language][key] || key;
    
    // 파라미터 치환
    if (params) {
      Object.keys(params).forEach(paramKey => {
        text = text.replace(`{${paramKey}}`, params[paramKey]);
      });
    }
    
    return text;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}

