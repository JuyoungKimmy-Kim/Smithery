import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    
    // 백엔드의 preview-tools API 호출
    const response = await fetch(`${BACKEND_URL}/api/v1/mcp-servers/preview-tools`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend API error:', response.status, errorText);
      return NextResponse.json(
        { success: false, tools: [], message: `Backend API error: ${response.status}` },
        { status: response.status }
      );
    }
    
    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error('Preview tools API error:', error);
    return NextResponse.json(
      { success: false, tools: [], message: `Internal server error: ${error}` },
      { status: 500 }
    );
  }
}

