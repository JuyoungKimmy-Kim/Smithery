import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;

    console.log(`Frontend API: Rate limit check for MCP server ${id}`);

    // Authorization 헤더에서 토큰 추출
    const authHeader = request.headers.get('authorization');

    const headers: Record<string, string> = {};

    if (authHeader) {
      headers['Authorization'] = authHeader;
    }

    const response = await fetch(`${BACKEND_URL}/api/v1/mcp-servers/${id}/playground/rate-limit`, {
      method: 'GET',
      headers,
      cache: 'no-store',
    });

    console.log(`Backend rate limit response status: ${response.status}`);

    const result = await response.json();
    return NextResponse.json(result, { status: response.status });
  } catch (error) {
    console.error('Rate limit API error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
