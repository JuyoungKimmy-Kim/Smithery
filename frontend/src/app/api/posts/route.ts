import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/posts`);
    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`);
    }
    const posts = await response.json();
    console.log('Backend posts data:', posts); // 디버깅 로그 추가
    console.log('First post ID:', posts[0]?.id); // 첫 번째 포스트의 ID 확인
    return NextResponse.json(posts);
  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
} 