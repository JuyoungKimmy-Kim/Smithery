/**
 * 전역 API 클라이언트
 * - Authorization 헤더 자동 추가
 * - 401 에러 시 자동 로그아웃
 */

type FetchOptions = RequestInit & {
  requiresAuth?: boolean;
};

// 로그아웃 콜백을 저장할 변수
let logoutCallback: (() => void) | null = null;

/**
 * 로그아웃 콜백 설정 (AuthContext에서 호출)
 */
export function setLogoutCallback(callback: () => void) {
  logoutCallback = callback;
}

/**
 * 인증된 API 요청을 보내는 fetch wrapper
 */
export async function apiFetch(url: string, options: FetchOptions = {}): Promise<Response> {
  const { requiresAuth = false, ...fetchOptions } = options;
  
  // Authorization 헤더 추가
  if (requiresAuth) {
    const token = localStorage.getItem('token');
    if (token) {
      fetchOptions.headers = {
        ...fetchOptions.headers,
        'Authorization': `Bearer ${token}`,
      };
    }
  }

  const response = await fetch(url, fetchOptions);
  
  // 401 에러 발생 시 자동 로그아웃
  if (response.status === 401) {
    console.log('Received 401 error, logging out...');
    
    // localStorage 초기화
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    
    // 로그아웃 콜백 실행
    if (logoutCallback) {
      logoutCallback();
    }
    
    // 로그인 페이지로 리다이렉트 (클라이언트 사이드)
    if (typeof window !== 'undefined') {
      alert('인증이 만료되었습니다.\n작성 중이던 내용은 자동 저장되었습니다.\n다시 로그인해주세요.');
      window.location.href = '/login?session_expired=true';
    }
    
    // 에러를 throw하여 호출하는 쪽에서도 처리할 수 있도록 함
    throw new Error('SESSION_EXPIRED');
  }
  
  return response;
}

/**
 * JSON 응답을 기대하는 API 요청
 */
export async function apiFetchJson<T = any>(
  url: string, 
  options: FetchOptions = {}
): Promise<T> {
  const response = await apiFetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API error: ${response.status}, message: ${errorText}`);
  }
  
  return response.json();
}

