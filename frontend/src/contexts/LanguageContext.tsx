"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

type Language = 'en';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string, params?: Record<string, string>) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

// 번역 데이터
const translations: Record<Language, Record<string, string>> = {
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
    'mypage.pendingBadge': 'Pending Approval',
    'mypage.pendingServers': 'Pending Servers ({count})',
    'mypage.approvedServers': 'Registered Servers ({count})',
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
    'mypage.approveConfirm': 'Are you sure you want to approve this server?',
    'mypage.rejectConfirm': 'Are you sure you want to reject this server?',
    'mypage.approveFailed': 'Failed to approve.',
    'mypage.approveError': 'An error occurred during approval.',
    'mypage.rejectFailed': 'Failed to reject.',
    'mypage.rejectError': 'An error occurred during rejection.',
    
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
    
    // Submit Page
    'submit.title': 'Register a New MCP Server',
    'submit.autoSaved': 'Auto-saved: {time}',
    'submit.serverName': 'Server Name',
    'submit.serverNameRequired': 'Server Name is required.',
    'submit.serverNamePlaceholder': 'My MCP Server',
    'submit.githubLink': 'GitHub Link',
    'submit.githubLinkRequired': 'GitHub Link is required.',
    'submit.githubLinkInvalid': 'Please enter a valid GitHub URL.',
    'submit.githubLinkPlaceholder': 'https://github.com/username/repository',
    'submit.description': 'Description',
    'submit.descriptionRequired': 'Description is required.',
    'submit.descriptionPlaceholder': 'Describe your MCP server...',
    'submit.protocol': 'Transport Type',
    'submit.protocolRequired': 'Transport Type is required.',
    'submit.protocolSelect': 'Select a transport type',
    'submit.serverUrl': 'Server URL',
    'submit.serverUrlInvalid': 'Please enter a valid URL.',
    'submit.serverUrlPlaceholderStdio': 'python stdio_test_mcp_server.py',
    'submit.serverUrlPlaceholderHttp': 'http://localhost:3000',
    'submit.serverUrlHelpStdio': 'Enter the MCP server run command. When entered with Transport Type, tools will be previewed automatically.',
    'submit.serverUrlHelpHttp': 'Enter the MCP Server URL. When entered with Transport Type, tools will be previewed automatically.',
    'submit.serverConfig': 'Server Config (JSON)',
    'submit.serverConfigPlaceholder': '{"type": "streamable-http", "url": "http://localhost:3000"}',
    'submit.serverConfigHelp': 'Enter MCP Server configuration in JSON format.',
    'submit.serverConfigInvalid': 'Server Config JSON format is invalid.',
    'submit.loadingTools': 'Loading tools from MCP Server...',
    'submit.toolsPreview': 'MCP Server Tools ({count})',
    'submit.addAllTools': 'Add All',
    'submit.toolsAdded': '{count} tools have been added.',
    'submit.noDescription': 'No description',
    'submit.parameters': 'Parameters:',
    'submit.required': 'required',
    'submit.connectionError': 'Cannot connect to MCP Server. Please check the Server URL and Transport Type, and ensure the server is running.',
    'submit.stdioWarning': 'STDIO Transport Notice:',
    'submit.stdioWarningDesc1': 'STDIO transport cannot be previewed directly in the browser.',
    'submit.stdioWarningDesc2': 'Please add tools manually.',
    'submit.tools': 'Tools ({count})',
    'submit.addTool': 'Add Tool',
    'submit.editTool': 'Edit Tool',
    'submit.addNewTool': 'Add New Tool',
    'submit.toolName': 'Tool Name',
    'submit.toolNameRequired': 'Tool name and description are required.',
    'submit.toolNamePlaceholder': 'tool_name',
    'submit.toolDescription': 'Description',
    'submit.toolDescriptionPlaceholder': 'Tool description...',
    'submit.addParameter': 'Add Parameter',
    'submit.editParameter': 'Edit Parameter',
    'submit.parameterName': 'Parameter name',
    'submit.parameterNameRequired': 'Parameter name is required.',
    'submit.parameterDescription': 'Description (optional)',
    'submit.selectType': 'Select type',
    'submit.noType': 'no type',
    'submit.update': 'Update',
    'submit.add': 'Add',
    'submit.cancel': 'Cancel',
    'submit.updateTool': 'Update Tool',
    'submit.addToolButton': 'Add Tool',
    'submit.deleteToolConfirm': 'Are you sure you want to delete this tool?',
    'submit.submitting': 'Submitting...',
    'submit.submitButton': 'Register MCP Server',
    'submit.signInRequired': 'Sign in required.',
    'submit.checkingAuth': 'Checking authentication...',
    'submit.sessionExpired': 'Session Expired',
    'submit.draftSaved': 'Draft saved automatically.',
    'submit.loginAgain': 'Log in again to continue.',
    'submit.ok': 'OK',
    'submit.successTitle': 'MCP Server registration completed.',
    'submit.successDesc1': 'After approval, it can be viewed in the MCP list,',
    'submit.successDesc2': 'and your registered servers can be found on My Page.',
    'submit.viewMcpList': 'View MCP List',
    'submit.viewMyPage': 'My Page',
    'submit.restorePrompt': 'You have unsaved work. Do you want to restore it?',
    'submit.leaveConfirm': 'Your work has been auto-saved.\nDo you want to leave this page?',
    
    // Edit Page
    'edit.title': 'Edit MCP Server',
    'edit.autoSaved': 'Auto-saved: {time}',
    'edit.loading': 'Loading MCP server...',
    'edit.notFound': 'MCP server not found',
    'edit.serverName': 'Server Name',
    'edit.githubLink': 'GitHub Link',
    'edit.description': 'Description',
    'edit.descriptionRequired': 'Description is required.',
    'edit.descriptionPlaceholder': 'Enter a detailed description of your MCP server',
    'edit.protocol': 'Transport Type',
    'edit.protocolRequired': 'Transport Type is required.',
    'edit.protocolSelect': 'Select a transport type',
    'edit.serverUrl': 'Server URL',
    'edit.serverUrlInvalid': 'Please enter a valid URL.',
    'edit.serverUrlPlaceholderStdio': 'python stdio_test_mcp_server.py',
    'edit.serverUrlPlaceholderHttp': 'http://localhost:3000',
    'edit.serverUrlHelpStdio': 'Enter the MCP server run command.',
    'edit.serverUrlHelpHttp': 'Enter the MCP Server URL.',
    'edit.serverConfig': 'Server Config (JSON)',
    'edit.serverConfigPlaceholder': '{"mcpServers": {"example": {"command": "python", "args": ["server.py"]}}}',
    'edit.serverConfigHelp': 'Enter server configuration in JSON format. Default configuration will be used if left blank.',
    'edit.serverConfigInvalid': 'Server Config JSON format is invalid.',
    'edit.loadingTools': 'Loading tools from MCP Server...',
    'edit.toolsPreview': 'MCP Server Tools ({count})',
    'edit.addAllTools': 'Add All',
    'edit.toolsAdded': '{count} tools have been added.',
    'edit.noDescription': 'No description',
    'edit.connectionError': 'Cannot connect to MCP Server. Please check the Server URL and Transport Type, and ensure the server is running.',
    'edit.duplicateToolsTitle': 'Duplicate Tools Found',
    'edit.duplicateToolsDesc': 'Tools with the same name already exist. Please select which version to use for each tool.',
    'edit.existingTool': 'Existing Tool',
    'edit.newTool': 'New Tool',
    'edit.applyChoices': 'Apply Choices',
    'edit.stdioWarning': 'STDIO Transport Notice:',
    'edit.stdioWarningDesc1': 'STDIO transport cannot be previewed directly in the browser.',
    'edit.stdioWarningDesc2': 'Please add tools manually.',
    'edit.tools': 'Tools ({count})',
    'edit.addTool': 'Add Tool',
    'edit.editTool': 'Edit Tool',
    'edit.addNewTool': 'Add New Tool',
    'edit.toolName': 'Tool Name',
    'edit.toolNameRequired': 'Tool name and description are required.',
    'edit.toolNamePlaceholder': 'tool_name',
    'edit.toolDescription': 'Description',
    'edit.toolDescriptionPlaceholder': 'Tool description...',
    'edit.parameters': 'Parameters',
    'edit.addParameter': 'Add Parameter',
    'edit.editParameter': 'Edit Parameter',
    'edit.parameterName': 'Parameter name',
    'edit.parameterNameRequired': 'Parameter name is required.',
    'edit.parameterDescription': 'Description (optional)',
    'edit.selectType': 'Select type',
    'edit.noType': 'no type',
    'edit.required': 'required',
    'edit.update': 'Update',
    'edit.add': 'Add',
    'edit.cancel': 'Cancel',
    'edit.updateTool': 'Update Tool',
    'edit.addToolButton': 'Add Tool',
    'edit.deleteToolConfirm': 'Are you sure you want to delete this tool?',
    'edit.cancelButton': 'Cancel',
    'edit.updating': 'Updating...',
    'edit.updateButton': 'Update Server',
    'edit.sessionExpired': 'Session Expired',
    'edit.draftSaved': 'Draft saved automatically.',
    'edit.loginAgain': 'Log in again to continue.',
    'edit.ok': 'OK',
    'edit.successTitle': 'MCP Server update completed.',
    'edit.successDesc1': 'Changes have been applied,',
    'edit.successDesc2': 'and can be viewed in the MCP list.',
    'edit.viewDetail': 'View Detail',
    'edit.viewMcpList': 'View MCP List',
    'edit.restorePrompt': 'You have unsaved edits. Do you want to restore them?',
    'edit.leaveConfirm': 'Your edits have been auto-saved.\nDo you want to leave this page?',
  },
};

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>('en');

  useEffect(() => {
    // 페이지 로드 시 localStorage에서 언어 설정 복원
    const storedLanguage = localStorage.getItem('language') as Language;
    if (storedLanguage === 'en') {
      setLanguageState('en');
    } else {
      // localStorage에 저장된 언어가 없거나 다른 값이면 영어를 기본값으로 설정
      setLanguageState('en');
      localStorage.setItem('language', 'en');
    }
  }, []);

  const setLanguage = (_lang: Language) => {
    setLanguageState('en');
    localStorage.setItem('language', 'en');
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

