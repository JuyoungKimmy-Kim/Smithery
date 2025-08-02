import { NextResponse } from 'next/server';

const BACKEND_URL = 'http://localhost:8000';

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/mcps`);
    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`);
    }
    const mcps = await response.json();
    return NextResponse.json(mcps);
  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    
    // 미리보기 요청인지 확인
    if (body.github_link && Object.keys(body).length === 1) {
      // 미리보기 API 호출
      const response = await fetch(`${BACKEND_URL}/api/mcps/preview`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });
      
      if (!response.ok) {
        throw new Error(`Backend API error: ${response.status}`);
      }
      
      const result = await response.json();
      return NextResponse.json(result);
    } else {
      // 일반 MCP 서버 생성 API 호출
      const response = await fetch(`${BACKEND_URL}/api/mcps`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });
      
      if (!response.ok) {
        throw new Error(`Backend API error: ${response.status}`);
      }
      
      const result = await response.json();
      return NextResponse.json(result);
    }
  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
} 