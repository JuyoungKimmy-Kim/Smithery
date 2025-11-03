"use client";

import { useState } from 'react';
import { ChevronDownIcon, ChevronUpIcon, CheckCircleIcon, ClockIcon, SparklesIcon, PauseIcon, LanguageIcon } from '@heroicons/react/24/solid';
import { useLanguage } from '@/contexts/LanguageContext';

interface Feature {
  title: string;
  description: string;
  implementation?: string;
  status?: 'completed' | 'in-progress' | 'planned' | 'on-hold';
}

interface Version {
  version: string;
  releaseDate?: string;
  expectedDate?: string;
  status: 'released' | 'in-progress' | 'planned';
  description: string;
  features: Feature[];
  improvements?: string[];
  bugFixes?: string[];
}

const roadmapDataKo: Version[] = [
  {
    version: 'v0.5',
    releaseDate: '2025년 8월 14일',
    status: 'released',
    description: 'mcp hub 의 첫 번째 정식 버전입니다. 기본적인 서버 등록 및 검색 기능을 제공합니다.',
    features: [
      {
        title: '사용자 인증 시스템',
        description: '로그인, 로그아웃 기능을 구현했습니다. 안전한 비밀번호 해싱과 세션 관리를 지원합니다.',
        status: 'completed'
      },
      {
        title: 'MCP 서버 등록',
        description: '사용자가 새로운 MCP 서버를 등록할 수 있습니다. 서버 이름, 설명, Repository URL, 카테고리, 태그 등을 입력할 수 있습니다.',
        status: 'completed'
      },
      {
        title: '서버 검색 및 필터링',
        description: '등록된 서버를 검색하고 카테고리별로 필터링할 수 있습니다. 키워드 검색과 태그 기반 검색을 지원합니다.',
        status: 'completed'
      },
      {
        title: '서버 상세 페이지',
        description: '각 서버의 상세 정보를 확인할 수 있는 페이지입니다. 설치 방법, 사용 예시, Repository 링크 등을 제공합니다.',
        status: 'completed'
      },
      {
        title: '즐겨찾기 기능',
        description: '관심있는 서버를 즐겨찾기에 추가하고 My Page에서 관리할 수 있습니다.',
        status: 'completed'
      },
      {
        title: 'My Page',
        description: '내가 등록한 서버, 즐겨찾기한 서버를 한눈에 관리할 수 있는 개인 페이지입니다.',
        status: 'completed'
      },
      {
        title: '사용자 프로필 페이지',
        description: '다른 사용자의 프로필을 확인하고 그들이 등록한 서버 목록을 볼 수 있습니다.',
        status: 'completed'
      },
      {
        title: '관리자 승인 시스템',
        description: '새로 등록된 서버는 관리자의 승인을 거쳐 공개됩니다. 관리자는 My Page에서 승인 대기 중인 서버를 확인하고 관리할 수 있습니다.',
        status: 'completed'
      }
    ],
  },
  {
    version: 'v1.0',
    releaseDate: '2025년 9월 29일',
    status: 'released',
    description: '인증 시스템 고도화 및 MCP 서버 상세 정보 관리 기능을 추가한 주요 업데이트입니다.',
    features: [
      {
        title: '회원가입 기능 구현',
        description: '사용자가 직접 계정을 생성할 수 있는 회원가입 기능을 추가했습니다. 사용자 프로필에 nickname과 bio 정보를 저장할 수 있는 데이터베이스 필드를 추가하여 개성있는 프로필 구성이 가능합니다.',
        status: 'completed'
      },
      {
        title: 'AD SSO Login 인증 연동',
        description: 'AD SSO 로그인 인증 기능을 추가하여 사내 통합 인증을 지원합니다.',
        status: 'completed'
      },
      {
        title: 'Tools 자동 수집 및 관리 시스템',
        description: 'Server Config를 이용하여 실제 MCP 서버에 접속해 tools와 parameter 정보를 자동으로 가져옵니다. 서버 접속이 불가능한 경우 수동으로 tools와 parameter를 입력할 수 있어 유연한 서버 등록이 가능합니다.',
        status: 'completed'
      }
    ],
    bugFixes: [
      'Time Zone을 Seoul(KST)로 변경하여 시간 표시 오류 해결',
      '로그아웃 후 페이지 새로고침 문제 해결'
    ]
  },
  {
    version: 'v1.5',
    releaseDate: '2025년 10월 23일',
    status: 'released',
    description: '커뮤니티 기능 강화 및 사용자 경험 개선을 위한 업데이트입니다.',
    features: [
      {
        title: '댓글 시스템',
        description: '서버 상세 페이지에서 댓글을 작성하고 소통할 수 있습니다. 자신의 댓글은 수정 및 삭제가 가능합니다.',
        status: 'completed'
      },
      {
        title: 'Notice(공지사항) 기능',
        description: 'MCP 서버를 등록한 사용자가 해당 서버의 상세 페이지에 공지사항을 등록하고 관리할 수 있습니다. 업데이트 정보나 중요한 알림을 사용자들에게 전달할 수 있습니다.',
        status: 'in-progress'
      },
      {
        title: 'Ranking 시스템',
        description: '인기 MCP 서버 랭킹(좋아요 수 기준)과 기여도 높은 사용자 랭킹(등록한 서버 수 기준)을 제공합니다. 메인 페이지에서 인기 콘텐츠를 한눈에 확인할 수 있습니다.',
        status: 'completed'
      },
      {
        title: '다국어 지원 (한국어/영어)',
        description: '한국어와 영어를 지원하여 글로벌 사용자들이 편리하게 이용할 수 있습니다. 언어는 navbar에서 쉽게 전환할 수 있습니다.',
        status: 'on-hold'
      },
      {
        title: 'Wiki 섹션',
        description: 'Getting Started, How to Use, Roadmap 페이지를 추가하여 사용자가 플랫폼을 쉽게 이해하고 사용할 수 있도록 했습니다.',
        status: 'completed'
      }
    ],
    improvements: [
      'GUI 개선: Footer의 불필요한 링크 정리 및 디자인 간소화',
      '태그 기반 필터링: 카테고리 대신 태그로 서버 필터링 가능',
      '서버 등록/수정 시 브라우저에 입력 정보 임시 저장',
      'Sign In 절차 간소화: AD Login으로 바로 접근 가능'
    ],
    bugFixes: [
      '좋아요 수(Favorite Count) 숫자 렌더링 이슈 해결'
    ]
  },
  {
    version: 'v1.7',
    releaseDate: '2025년 11월 3일',
    status: 'released',
    description: 'MCP 서버 등록 시 tools 자동 수집 기능을 모든 프로토콜에 적용 가능하도록 개선하고, Prompt와 Resources 자동 수집 및 Health check 기능을 추가하는 업데이트입니다.',
    features: [
      {
        title: '범용 Tools 자동 수집 시스템',
        description: '현재 JSON-RPC를 이용한 tools 자동 수집이 모든 MCP 프로토콜에 적용되지 않는 문제를 해결합니다. 다양한 MCP 프로토콜과 서버 구현 방식에 맞춰 tools 정보를 자동으로 가져올 수 있도록 범용적으로 개선합니다.',
        implementation: '다양한 MCP 프로토콜 지원, 서버별 맞춤형 연결 방식 구현, 에러 처리 및 폴백 메커니즘 강화',
        status: 'completed'
      },
      {
        title: 'Prompt, Resources 자동 수집 기능',
        description: 'MCP 서버 등록 시 tools와 함께 prompts와 resources 정보도 자동으로 수집하여 서버의 전체 기능을 더욱 상세하게 파악할 수 있도록 합니다.',
        status: 'completed'
      },
      {
        title: 'MCP Health check 기능',
        description: '등록된 MCP 서버의 상태를 주기적으로 확인하고, 서버 접속 가능 여부와 응답 시간을 모니터링합니다. 서버 상세 페이지에서 실시간 상태를 확인할 수 있습니다.',
        status: 'completed'
      }
    ],
    improvements: [
      'Tools 수집 성공률 향상',
      '지원 프로토콜 확장',
      '서버 정보 자동 수집 범위 확대'
    ],
    bugFixes: [
      '특정 MCP 서버에서 tools 수집 실패 문제 해결',
      '프로토콜별 연결 방식 차이로 인한 오류 수정'
    ]
  },
  {
    version: 'v1.8',
    expectedDate: '2025년 11월 7일 (예정)',
    status: 'in-progress',
    description: 'mcp hub 자체를 MCP 서버로 제공하고, MCP playground를 통해 서버를 바로 테스트할 수 있는 기능을 추가하는 업데이트입니다.',
    features: [
      {
        title: 'mcp hub MCP 서버',
        description: 'mcp hub 자체를 MCP 서버로 제공하여 외부 AI 클라이언트에서 직접 MCP 서버 정보를 조회하고 검색할 수 있습니다. roocode 등에서 mcp hub의 데이터를 활용할 수 있습니다.',
        implementation: 'MCP 서버 프로토콜 구현, 서버 검색/조회 API 제공, MCP 클라이언트 연동 가이드 제공',
        status: 'planned'
      },
      {
        title: 'MCP Playground',
        description: 'MCP 서버 상세 페이지에서 바로 해당 MCP 서버를 테스트해볼 수 있는 playground를 제공합니다. tools 호출, prompts 테스트, resources 조회 등을 웹 인터페이스에서 직접 실행해볼 수 있습니다.',
        implementation: '브라우저 기반 MCP 클라이언트 구현, 서버 연결 및 통신 처리, 실시간 결과 표시',
        status: 'planned'
      }
    ],
    improvements: [
      '서버 테스트 편의성 향상',
      'MCP 서버 직접 체험 가능',
      '외부 AI 도구와의 연동 지원'
    ]
  },
  {
    version: 'v2.0',
    expectedDate: '2025년 11월 21일 (예정)',
    status: 'planned',
    description: '데이터 분석 및 사용자 행동 추적 시스템을 도입하는 업데이트입니다.',
    features: [
      {
        title: '검색 키워드 분석 시스템',
        description: '사용자들의 검색 키워드 사용량과 트렌드를 실시간으로 분석하고 시각화합니다. 인기 검색어, 검색 빈도, 검색 성공률 등을 제공하여 콘텐츠 최적화에 활용할 수 있습니다.',
        implementation: 'Matomo Site Search 기능 + 검색 이벤트를 trackEvent로 전송, 선택적으로 DB에 검색 로그 저장',
        status: 'planned'
      },
      {
        title: 'MCP 서버 조회 추적 시스템',
        description: '각 MCP 서버 카드의 클릭 수, 상세 페이지 조회 시간, 이탈률 등을 추적합니다. 서버별 인기도와 사용자 관심도를 정량적으로 측정할 수 있습니다.',
        implementation: '서버 카드 클릭 시 Matomo trackEvent 전송, 페이지 뷰 및 체류 시간은 Matomo 자동 추적, Matomo API로 통계 조회',
        status: 'planned'
      },
      {
        title: '사용자 행동 분석 대시보드',
        description: '관리자와 서버 등록자가 사용자 행동 패턴을 분석할 수 있는 대시보드를 제공합니다. 페이지 뷰, 세션 시간, 사용자 여정 등을 시각화합니다.',
        implementation: 'Matomo API를 활용한 커스텀 대시보드 구축 또는 Matomo 대시보드 iframe 임베드',
        status: 'planned'
      },
    ],
    improvements: [
      'Matomo 커스텀 이벤트 트래킹 추가',
      'Matomo API 연동 및 통계 조회 기능',
    ]
  },
  {
    version: 'v3.0',
    expectedDate: '2025년 11월 28일 (예정)',
    status: 'planned',
    description: 'AI 기반 추천 시스템과 MCP 서버 자동 생성 도구를 도입하는 업데이트입니다.',
    features: [
      {
        title: 'AI 서버 추천',
        description: '사용자의 관심사와 사용 패턴을 분석하여 맞춤형 MCP 서버를 추천합니다.',
        status: 'planned'
      },
      {
        title: '자동 문서 생성',
        description: 'Repository를 분석하여 기본적인 description과 Server Config 등을 자동으로 생성합니다.',
        status: 'planned'
      },
      {
        title: 'MCP 서버 생성 도구',
        description: 'roocode 같은 AI 도구에서 mcp hub의 MCP 서버를 통해 자연어로 요청하면 원하는 기능을 가진 MCP 서버를 자동으로 생성하고 배포할 수 있습니다.',
        implementation: 'MCP 서버 템플릿 제공, AI 기반 자동 코드 생성, 자동 배포 파이프라인 구축',
        status: 'planned'
      }
    ],
  }
];

const roadmapDataEn: Version[] = [
  {
    version: 'v0.5',
    releaseDate: 'August 14, 2025',
    status: 'released',
    description: 'The first official version of MCP Hub. Provides basic server registration and search functionality.',
    features: [
      {
        title: 'User Authentication System',
        description: 'Implemented login and logout functionality. Supports secure password hashing and session management.',
        status: 'completed'
      },
      {
        title: 'MCP Server Registration',
        description: 'Users can register new MCP servers. Can input server name, description, repository URL, category, tags, etc.',
        status: 'completed'
      },
      {
        title: 'Server Search and Filtering',
        description: 'Search registered servers and filter by category. Supports keyword search and tag-based search.',
        status: 'completed'
      },
      {
        title: 'Server Detail Page',
        description: 'A page where you can check detailed information for each server. Provides installation methods, usage examples, repository links, etc.',
        status: 'completed'
      },
      {
        title: 'Favorites Feature',
        description: 'Add servers of interest to favorites and manage them in My Page.',
        status: 'completed'
      },
      {
        title: 'My Page',
        description: 'A personal page where you can manage your registered servers and favorite servers at a glance.',
        status: 'completed'
      },
      {
        title: 'User Profile Page',
        description: 'Check other users\' profiles and view the list of servers they have registered.',
        status: 'completed'
      },
      {
        title: 'Admin Approval System',
        description: 'Newly registered servers are published after admin approval. Admins can check and manage pending servers in My Page.',
        status: 'completed'
      }
    ],
  },
  {
    version: 'v1.0',
    releaseDate: 'September 29, 2025',
    status: 'released',
    description: 'A major update with enhanced authentication system and MCP server detailed information management features.',
    features: [
      {
        title: 'Sign-up Feature Implementation',
        description: 'Added sign-up functionality where users can create their own accounts. Added database fields to store nickname and bio information in user profiles for personalized profile setup.',
        status: 'completed'
      },
      {
        title: 'AD SSO Login Authentication Integration',
        description: 'Added AD SSO login authentication to support corporate integrated authentication.',
        status: 'completed'
      },
      {
        title: 'Automatic Tools Collection and Management System',
        description: 'Uses Server Config to automatically fetch tools and parameter information by connecting to the actual MCP server. If the server connection is not possible, tools and parameters can be manually entered for flexible server registration.',
        status: 'completed'
      }
    ],
    bugFixes: [
      'Fixed time display error by changing Time Zone to Seoul(KST)',
      'Fixed page refresh issue after logout'
    ]
  },
  {
    version: 'v1.5',
    releaseDate: 'October 23, 2025',
    status: 'released',
    description: 'An update for community feature enhancement and user experience improvement.',
    features: [
      {
        title: 'Comment System',
        description: 'You can write comments and communicate on the server detail page. You can edit and delete your own comments.',
        status: 'completed'
      },
      {
        title: 'Notice Feature',
        description: 'Users who registered MCP servers can register and manage notices on the server detail page. Can deliver update information or important notifications to users.',
        status: 'in-progress'
      },
      {
        title: 'Ranking System',
        description: 'Provides popular MCP server rankings (based on likes) and high-contributing user rankings (based on number of registered servers). You can check popular content at a glance on the main page.',
        status: 'completed'
      },
      {
        title: 'Multi-language Support (Korean/English)',
        description: 'Supports Korean and English for convenient use by global users. Language can be easily switched in the navbar.',
        status: 'on-hold'
      },
      {
        title: 'Wiki Section',
        description: 'Added Getting Started, How to Use, and Roadmap pages to help users easily understand and use the platform.',
        status: 'completed'
      }
    ],
    improvements: [
      'GUI improvement: Cleaned up unnecessary links in Footer and simplified design',
      'Tag-based filtering: Server filtering possible with tags instead of categories',
      'Temporarily save input information in browser when registering/modifying server',
      'Simplified Sign In process: Direct access with AD Login'
    ],
    bugFixes: [
      'Fixed favorite count rendering issue'
    ]
  },
  {
    version: 'v1.7',
    releaseDate: 'November 3, 2025',
    status: 'released',
    description: 'An update to improve the automatic tools collection feature for all protocols when registering MCP servers, and add automatic Prompt and Resources collection along with Health check functionality.',
    features: [
      {
        title: 'Universal Tools Automatic Collection System',
        description: 'Solves the problem that current JSON-RPC-based tools automatic collection does not apply to all MCP protocols. Universally improved to automatically fetch tools information according to various MCP protocols and server implementation methods.',
        implementation: 'Support for various MCP protocols, implementation of customized connection methods for each server, strengthened error handling and fallback mechanisms',
        status: 'completed'
      },
      {
        title: 'Prompt and Resources Automatic Collection Feature',
        description: 'When registering MCP servers, automatically collects prompts and resources information along with tools, allowing for a more detailed understanding of the server\'s full capabilities.',
        status: 'completed'
      },
      {
        title: 'MCP Health Check Feature',
        description: 'Periodically checks the status of registered MCP servers and monitors server accessibility and response time. Real-time status can be checked on the server detail page.',
        status: 'completed'
      }
    ],
    improvements: [
      'Improved tools collection success rate',
      'Expanded supported protocols',
      'Extended automatic server information collection scope'
    ],
    bugFixes: [
      'Fixed tools collection failure issue on specific MCP servers',
      'Fixed errors due to protocol-specific connection method differences'
    ]
  },
  {
    version: 'v1.8',
    expectedDate: 'November 7, 2025 (Expected)',
    status: 'in-progress',
    description: 'An update that provides MCP Hub itself as an MCP server and adds MCP playground functionality to test servers immediately.',
    features: [
      {
        title: 'MCP Hub MCP Server',
        description: 'Provides MCP Hub itself as an MCP server so external AI clients can directly query and search MCP server information. MCP Hub data can be used in roocode, etc.',
        implementation: 'Implement MCP server protocol, provide server search/query API, provide MCP client integration guide',
        status: 'planned'
      },
      {
        title: 'MCP Playground',
        description: 'Provides a playground on the MCP server detail page where you can immediately test the MCP server. You can directly execute tools calls, test prompts, query resources, etc. through the web interface.',
        implementation: 'Browser-based MCP client implementation, server connection and communication handling, real-time result display',
        status: 'planned'
      }
    ],
    improvements: [
      'Enhanced server testing convenience',
      'Direct MCP server experience',
      'Integration support with external AI tools'
    ]
  },
  {
    version: 'v2.0',
    expectedDate: 'November 21, 2025 (Expected)',
    status: 'planned',
    description: 'An update introducing data analysis and user behavior tracking systems.',
    features: [
      {
        title: 'Search Keyword Analysis System',
        description: 'Analyzes and visualizes user search keyword usage and trends in real time. Provides popular search terms, search frequency, search success rate, etc. for use in content optimization.',
        implementation: 'Matomo Site Search feature + Send search events with trackEvent, optionally save search logs to DB',
        status: 'planned'
      },
      {
        title: 'MCP Server View Tracking System',
        description: 'Tracks click count for each MCP server card, detail page view time, bounce rate, etc. Can quantitatively measure server popularity and user interest.',
        implementation: 'Send Matomo trackEvent when server card is clicked, page views and dwell time are automatically tracked by Matomo, query statistics with Matomo API',
        status: 'planned'
      },
      {
        title: 'User Behavior Analysis Dashboard',
        description: 'Provides a dashboard where admins and server registrants can analyze user behavior patterns. Visualizes page views, session time, user journey, etc.',
        implementation: 'Build custom dashboard using Matomo API or embed Matomo dashboard iframe',
        status: 'planned'
      },
    ],
    improvements: [
      'Added Matomo custom event tracking',
      'Matomo API integration and statistics query function',
    ]
  },
  {
    version: 'v3.0',
    expectedDate: 'November 28, 2025 (Expected)',
    status: 'planned',
    description: 'An update introducing an AI-based recommendation system and automatic MCP server creation tool.',
    features: [
      {
        title: 'AI Server Recommendations',
        description: 'Analyzes user interests and usage patterns to recommend customized MCP servers.',
        status: 'planned'
      },
      {
        title: 'Automatic Documentation Generation',
        description: 'Analyzes repositories to automatically generate basic descriptions and Server Config.',
        status: 'planned'
      },
      {
        title: 'MCP Server Creation Tool',
        description: 'When requesting in natural language through MCP Hub\'s MCP server in AI tools like roocode, it can automatically create and deploy an MCP server with the desired functionality.',
        implementation: 'Provide MCP server template, AI-based automatic code generation, build automatic deployment pipeline',
        status: 'planned'
      }
    ],
  }
];

function StatusBadge({ status }: { status: 'released' | 'in-progress' | 'planned' }) {
  const badges = {
    released: { text: 'Released', color: 'bg-green-100 text-green-800', icon: CheckCircleIcon },
    'in-progress': { text: 'In Progress', color: 'bg-blue-100 text-blue-800', icon: SparklesIcon },
    planned: { text: 'Planned', color: 'bg-gray-100 text-gray-800', icon: ClockIcon }
  };

  const badge = badges[status];
  const Icon = badge.icon;

  return (
    <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${badge.color}`}>
      <Icon className="h-4 w-4" />
      {badge.text}
    </span>
  );
}

function FeatureStatusIcon({ status }: { status?: 'completed' | 'in-progress' | 'planned' | 'on-hold' }) {
  if (!status) return null;
  
  const icons = {
    completed: <CheckCircleIcon className="h-5 w-5 text-green-600" />,
    'in-progress': <SparklesIcon className="h-5 w-5 text-blue-600" />,
    planned: <ClockIcon className="h-5 w-5 text-gray-400" />,
    'on-hold': <PauseIcon className="h-5 w-5 text-orange-500" />
  };

  return icons[status];
}

export default function RoadmapPage() {
  const [expandedVersion, setExpandedVersion] = useState<string | null>('v1.8');
  const { language, setLanguage } = useLanguage();
  
  const roadmapData = language === 'en' ? roadmapDataEn : roadmapDataKo;

  const toggleVersion = (version: string) => {
    setExpandedVersion(expandedVersion === version ? null : version);
  };

  const handleLanguageToggle = () => {
    setLanguage(language === 'ko' ? 'en' : 'ko');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-5xl mx-auto">
          {/* Language Toggle Button */}
          <div className="flex justify-end mb-6">
            <button
              onClick={handleLanguageToggle}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              <LanguageIcon className="h-5 w-5" />
              {language === 'ko' ? '한국어 (KO)' : 'English (EN)'}
            </button>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Roadmap</h1>
          <p className="text-lg text-gray-600 mb-12">
            {language === 'en' 
              ? 'Check the development plans and version-specific changes for MCP Server Hub.'
              : 'MCP Server Hub의 개발 계획과 버전별 변경 사항을 확인하세요.'}
          </p>

          <div className="space-y-6">
            {roadmapData.map((versionData) => {
              const isExpanded = expandedVersion === versionData.version;
              
              return (
                <div
                  key={versionData.version}
                  className="bg-white rounded-lg shadow-md overflow-hidden transition-all duration-300"
                >
                  {/* Header - Clickable */}
                  <button
                    onClick={() => toggleVersion(versionData.version)}
                    className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <h2 className="text-2xl font-bold text-gray-900">{versionData.version}</h2>
                      <StatusBadge status={versionData.status} />
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-sm text-gray-600">
                        {versionData.releaseDate || versionData.expectedDate}
                      </span>
                      {isExpanded ? (
                        <ChevronUpIcon className="h-6 w-6 text-gray-400" />
                      ) : (
                        <ChevronDownIcon className="h-6 w-6 text-gray-400" />
                      )}
                    </div>
                  </button>

                  {/* Expandable Content */}
                  {isExpanded && (
                    <div className="px-6 pb-6 border-t border-gray-200">
                      {/* Description */}
                      <div className="pt-6 pb-4">
                        <p className="text-gray-700 leading-relaxed">{versionData.description}</p>
                      </div>

                      {/* Features */}
                      <div className="mb-6">
                        <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                          <span className="text-2xl">🎯</span>
                          {language === 'en' ? 'Key Features' : '주요 기능'}
                        </h3>
                        <div className="space-y-4">
                          {versionData.features.map((feature, idx) => (
                            <div
                              key={idx}
                              className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors"
                            >
                              <div className="flex items-start gap-3">
                                <FeatureStatusIcon status={feature.status} />
                                <div className="flex-1">
                                  <h4 className="font-semibold text-gray-900 mb-1">{feature.title}</h4>
                                  <p className="text-gray-600 text-sm">{feature.description}</p>
                                  {feature.implementation && (
                                    <p className="text-gray-500 text-xs mt-2 italic">
                                      💡 {feature.implementation}
                                    </p>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Improvements */}
                      {versionData.improvements && versionData.improvements.length > 0 && (
                        <div className="mb-6">
                          <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                            <span className="text-2xl">✨</span>
                            {language === 'en' ? 'Improvements' : '개선 사항'}
                          </h3>
                          <ul className="space-y-2">
                            {versionData.improvements.map((improvement, idx) => (
                              <li key={idx} className="flex items-start gap-2 text-gray-700">
                                <span className="text-blue-600 mt-1">•</span>
                                <span>{improvement}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Bug Fixes */}
                      {versionData.bugFixes && versionData.bugFixes.length > 0 && (
                        <div>
                          <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                            <span className="text-2xl">🐛</span>
                            {language === 'en' ? 'Bug Fixes' : '버그 수정'}
                          </h3>
                          <ul className="space-y-2">
                            {versionData.bugFixes.map((bugFix, idx) => (
                              <li key={idx} className="flex items-start gap-2 text-gray-700">
                                <span className="text-red-600 mt-1">•</span>
                                <span>{bugFix}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Footer Note */}
          <div className="mt-12 bg-blue-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-900 mb-4">
              📝 {language === 'en' ? 'Notes' : '참고사항'}
            </h3>
            <ul className="space-y-2 text-blue-800 text-sm mb-6">
              {language === 'en' ? (
                <>
                  <li>• Scheduled release dates may change depending on development progress.</li>
                  <li>• Feature additions and improvements may be adjusted to reflect community feedback.</li>
                  <li>• New feature suggestions or feedback are always welcome!</li>
                </>
              ) : (
                <>
                  <li>• 예정된 출시일은 개발 상황에 따라 변경될 수 있습니다.</li>
                  <li>• 기능 추가 및 개선 사항은 커뮤니티 피드백을 반영하여 조정될 수 있습니다.</li>
                  <li>• 새로운 기능 제안이나 피드백은 언제든 환영합니다!</li>
                </>
              )}
            </ul>
            
            {/* GitHub Issue Link */}
            <div className="bg-white rounded-lg p-4 border border-blue-200">
              <h4 className="text-md font-semibold text-gray-900 mb-2">
                💡 {language === 'en' ? 'Feedback and Suggestions' : '피드백 및 제안'}
              </h4>
              <p className="text-gray-600 text-sm mb-4">
                {language === 'en'
                  ? 'If you have new feature suggestions, improvement ideas, or feedback for each version, please register them on GitHub Issue.'
                  : '각 버전에 대한 새로운 기능 제안, 개선 아이디어, 또는 피드백이 있으시다면 GitHub Issue에 등록해주세요.'}
              </p>
              <a
                href="https://github.com/YOUR_REPO/issues/new"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors text-sm font-medium"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 0C4.477 0 0 4.484 0 10.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0110 4.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.203 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.942.359.31.678.921.678 1.856 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0020 10.017C20 4.484 15.522 0 10 0z" clipRule="evenodd" />
                </svg>
                {language === 'en' ? 'Register GitHub Issue' : 'GitHub Issue 등록하기'}
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
