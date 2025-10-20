"use client";

import { useState } from 'react';
import { ChevronDownIcon, ChevronUpIcon, CheckCircleIcon, ClockIcon, SparklesIcon } from '@heroicons/react/24/solid';

interface Feature {
  title: string;
  description: string;
  implementation?: string;
  status?: 'completed' | 'in-progress' | 'planned';
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

const roadmapData: Version[] = [
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
    releaseDate: '2025년 10월 23일 (예정)',
    status: 'in-progress',
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
        status: 'in-progress'
      },
      {
        title: '다국어 지원 (한국어/영어)',
        description: '한국어와 영어를 지원하여 글로벌 사용자들이 편리하게 이용할 수 있습니다. 언어는 navbar에서 쉽게 전환할 수 있습니다.',
        status: 'in-progress'
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
    releaseDate: '2025년 11월 7일 (예정)',
    status: 'planned',
    description: 'MCP 서버 등록 시 tools 자동 수집 기능을 모든 프로토콜에 적용 가능하도록 개선하는 업데이트입니다.',
    features: [
      {
        title: '범용 Tools 자동 수집 시스템',
        description: '현재 JSON-RPC를 이용한 tools 자동 수집이 모든 MCP 프로토콜에 적용되지 않는 문제를 해결합니다. 다양한 MCP 프로토콜과 서버 구현 방식에 맞춰 tools 정보를 자동으로 가져올 수 있도록 범용적으로 개선합니다.',
        implementation: '다양한 MCP 프로토콜 지원, 서버별 맞춤형 연결 방식 구현, 에러 처리 및 폴백 메커니즘 강화',
        status: 'planned'
      }
    ],
    improvements: [
      'Tools 수집 성공률 향상',
      '지원 프로토콜 확장',
    ],
    bugFixes: [
      '특정 MCP 서버에서 tools 수집 실패 문제 해결',
      '프로토콜별 연결 방식 차이로 인한 오류 수정'
    ]
  },
  {
    version: 'v2.0',
    expectedDate: '2025년 11월 14일 (예정)',
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
    description: 'AI 기반 추천 시스템과 mcp hub 자체의 MCP 서버를 도입하는 업데이트입니다.',
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
        title: 'mcp hub MCP 서버',
        description: 'mcp hub 자체를 MCP 서버로 제공하여 외부 AI 클라이언트에서 직접 MCP 서버 정보를 조회하고 검색할 수 있습니다. roocode 등에서 mcp hub의 데이터를 활용할 수 있습니다.',
        implementation: 'MCP 서버 프로토콜 구현, 서버 검색/조회 API 제공, MCP 클라이언트 연동 가이드 제공',
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

function FeatureStatusIcon({ status }: { status?: 'completed' | 'in-progress' | 'planned' }) {
  if (!status) return null;
  
  const icons = {
    completed: <CheckCircleIcon className="h-5 w-5 text-green-600" />,
    'in-progress': <SparklesIcon className="h-5 w-5 text-blue-600" />,
    planned: <ClockIcon className="h-5 w-5 text-gray-400" />
  };

  return icons[status];
}

export default function RoadmapPage() {
  const [expandedVersion, setExpandedVersion] = useState<string | null>('v1.5');

  const toggleVersion = (version: string) => {
    setExpandedVersion(expandedVersion === version ? null : version);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-5xl mx-auto">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Roadmap</h1>
          <p className="text-lg text-gray-600 mb-12">
            MCP Server Hub의 개발 계획과 버전별 변경 사항을 확인하세요.
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
                          주요 기능
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
                            개선 사항
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
                            버그 수정
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
            <h3 className="text-lg font-semibold text-blue-900 mb-4">📝 참고사항</h3>
            <ul className="space-y-2 text-blue-800 text-sm mb-6">
              <li>• 예정된 출시일은 개발 상황에 따라 변경될 수 있습니다.</li>
              <li>• 기능 추가 및 개선 사항은 커뮤니티 피드백을 반영하여 조정될 수 있습니다.</li>
              <li>• 새로운 기능 제안이나 피드백은 언제든 환영합니다!</li>
            </ul>
            
            {/* GitHub Issue Link */}
            <div className="bg-white rounded-lg p-4 border border-blue-200">
              <h4 className="text-md font-semibold text-gray-900 mb-2">💡 피드백 및 제안</h4>
              <p className="text-gray-600 text-sm mb-4">
                각 버전에 대한 새로운 기능 제안, 개선 아이디어, 또는 피드백이 있으시다면 GitHub Issue에 등록해주세요.
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
                GitHub Issue 등록하기
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
