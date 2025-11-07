import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const body = await request.json();

    console.log(`Frontend API: Playground chat for MCP server ${id}`);

    // Authorization 헤더에서 토큰 추출
    const authHeader = request.headers.get('authorization');

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (authHeader) {
      headers['Authorization'] = authHeader;
    }

    const response = await fetch(`${BACKEND_URL}/api/v1/mcp-servers/${id}/playground/chat`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });

    console.log(`Backend playground response status: ${response.status}`);

    const result = await response.json();
    return NextResponse.json(result, { status: response.status });
  } catch (error) {
    console.error('Playground chat API error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
