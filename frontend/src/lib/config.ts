// 환경변수로 백엔드 URL을 설정할 수 있도록 하되, 기본값 제공
export const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 
  (process.env.NODE_ENV === 'development' ? 'http://localhost:10001' : 'http://backend:10001');

// 백엔드 API 기본 경로
export const API_BASE_PATH = '/api'; 