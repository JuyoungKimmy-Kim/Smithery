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
    
    // /submit 또는 /edit 페이지에서만 리다이렉트 URL 저장 및 이벤트 발생 (모달 처리)
    if (typeof window !== 'undefined') {
      const currentPath = window.location.pathname;
      
      // submit 페이지 또는 edit 페이지인지 확인
      if (currentPath === '/submit' || currentPath.includes('/edit')) {
        // 원래 페이지로 돌아올 수 있도록 URL 저장
        sessionStorage.setItem('redirectAfterLogin', currentPath);
        // 세션 만료를 알리는 custom event 발생
        window.dispatchEvent(new CustomEvent('session-expired'));
        // SESSION_EXPIRED 에러를 throw하여 handleSubmit에서 catch할 수 있도록 함
        throw new Error('SESSION_EXPIRED');
      }
    }
    // 다른 페이지에서는 조용히 로그아웃만 하고 401 응답 반환
    return response;
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

