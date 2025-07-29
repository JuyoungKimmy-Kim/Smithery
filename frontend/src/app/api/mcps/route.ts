import { NextResponse } from 'next/server';

const BACKEND_URL = 'http://localhost:8080';

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
  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
} 