// 백엔드 URL 설정
export const BACKEND_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:10001' 
  : 'http://backend:10001';

// API 기본 URL 설정
export const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:10001/api/v1' 
  : 'http://backend:10001/api/v1';

// 프론트엔드 접근 URL (사용자에게 보이는 URL)
export const FRONTEND_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:3000' 
  : 'https://ssai.samsungds.net:10002'; 