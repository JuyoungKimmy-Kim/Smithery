import { NextResponse } from 'next/server';

const BACKEND_URL = 'http://127.0.0.1:8000';

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/mcp-servers/`);
    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`);
    }
    const mcps = await response.json();
    
    // 각 MCP 서버에 사용자 정보와 통일된 아바타 추가
    const mcpsWithUserInfo = mcps.map((mcp: any) => ({
      ...mcp,
      author: mcp.owner ? mcp.owner.username : 'Unknown User',
      avatar: '/images/avatar1.jpg' // 통일된 아바타 이미지
    }));
    
    return NextResponse.json(mcpsWithUserInfo);
  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    
    // Authorization 헤더에서 토큰 추출
    const authHeader = request.headers.get('authorization');
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (authHeader) {
      headers['Authorization'] = authHeader;
    }
    
    // 미리보기 요청인지 확인
    if (body.github_link && Object.keys(body).length === 1) {
      // 미리보기 API 호출
      const response = await fetch(`${BACKEND_URL}/api/v1/mcp-servers/preview`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
      });
      
      // 백엔드의 실제 응답을 그대로 전달 (401 포함)
      const result = await response.json();
      return NextResponse.json(result, { status: response.status });
    } else {
      // 일반 MCP 서버 생성 API 호출
      const response = await fetch(`${BACKEND_URL}/api/v1/mcp-servers/`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
      });
      
      // 백엔드의 실제 응답을 그대로 전달 (401 포함)
      const result = await response.json();
      return NextResponse.json(result, { status: response.status });
    }
  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
} 