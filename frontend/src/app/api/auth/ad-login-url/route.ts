import { NextResponse } from 'next/server';

// Docker 환경에서는 백엔드 컨테이너 이름으로 접근
// 로컬 개발 환경에서는 localhost 사용
const BACKEND_URL = process.env.NODE_ENV === 'production' 
  ? 'http://backend:10001'  // Docker 컨테이너 간 통신
  : 'http://127.0.0.1:8000'; // 로컬 개발 환경

export async function GET() {
  try {
    console.log('Frontend AD Login URL API - Request received');
    console.log('Frontend AD Login URL API - Backend URL:', BACKEND_URL);
    
    const response = await fetch(`${BACKEND_URL}/api/v1/auth/ad-login-url`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    console.log('Frontend AD Login URL API - Backend response status:', response.status);

    if (!response.ok) {
      const errorData = await response.json();
      console.error('Backend AD Login URL failed:', errorData);
      return NextResponse.json(
        { detail: errorData.detail || 'AD 로그인 URL을 가져오는데 실패했습니다.' },
        { status: response.status }
      );
    }

    const result = await response.json();
    console.log('Frontend AD Login URL API - Backend response success:', result);
    return NextResponse.json(result);
  } catch (error) {
    console.error('AD Login URL API error:', error);
    return NextResponse.json(
      { detail: 'Internal server error' },
      { status: 500 }
    );
  }
} 