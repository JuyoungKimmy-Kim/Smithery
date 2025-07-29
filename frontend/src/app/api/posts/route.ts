import { NextResponse } from 'next/server';

const BACKEND_URL = 'http://localhost:8080';

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/posts`);
    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`);
    }
    const posts = await response.json();
    return NextResponse.json(posts);
  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
} 