import { NextResponse } from 'next/server';

const BACKEND_URL = 'http://localhost:8000';

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    console.log(`Frontend API: Fetching MCP server with ID: ${id}`);  // 디버깅 로그
    
    const response = await fetch(`${BACKEND_URL}/api/v1/mcp-servers/${id}`, {
      cache: 'no-store',  // 캐시 방지
      headers: {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
    });
    console.log(`Backend response status: ${response.status}`);  // 디버깅 로그
    
    if (!response.ok) {
      console.error(`Backend API error: ${response.status}`);  // 디버깅 로그
      throw new Error(`Backend API error: ${response.status}`);
    }
    
    const mcp = await response.json();
    console.log('Backend response data:', mcp);  // 디버깅 로그
    return NextResponse.json(mcp);
  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function PUT(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const body = await request.json();
    
    console.log(`Frontend API: PUT request for MCP server ${id}`);  // 디버깅 로그
    console.log(`Request body:`, body);  // 디버깅 로그
    
    // Authorization 헤더에서 토큰 추출
    const authHeader = request.headers.get('authorization');
    console.log(`Authorization header: ${authHeader ? 'Present' : 'Missing'}`);  // 디버깅 로그
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (authHeader) {
      headers['Authorization'] = authHeader;
    }
    
    console.log(`Sending request to backend: ${BACKEND_URL}/api/v1/mcp-servers/${id}`);  // 디버깅 로그
    
    const response = await fetch(`${BACKEND_URL}/api/v1/mcp-servers/${id}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(body),
    });
    
    console.log(`Backend response status: ${response.status}`);  // 디버깅 로그
    
    // 백엔드의 실제 응답을 그대로 전달 (401 포함)
    const result = await response.json();
    console.log(`Backend response data:`, result);  // 디버깅 로그
    return NextResponse.json(result, { status: response.status });
  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function DELETE(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    console.log(`Frontend API: DELETE request for MCP server ${id}`);  // 디버깅 로그
    
    // Authorization 헤더에서 토큰 추출
    const authHeader = request.headers.get('authorization');
    console.log(`Authorization header: ${authHeader ? 'Present' : 'Missing'}`);  // 디버깅 로그
    
    const headers: Record<string, string> = {};
    
    if (authHeader) {
      headers['Authorization'] = authHeader;
    }
    
    console.log(`Sending DELETE request to backend: ${BACKEND_URL}/api/v1/mcp-servers/admin/${id}`);  // 디버깅 로그
    
    const response = await fetch(`${BACKEND_URL}/api/v1/mcp-servers/admin/${id}`, {
      method: 'DELETE',
      headers,
    });
    
    console.log(`Backend DELETE response status: ${response.status}`);  // 디버깅 로그
    
    // 백엔드의 실제 응답을 그대로 전달 (401 포함)
    const result = await response.json();
    console.log(`Backend DELETE response data:`, result);  // 디버깅 로그
    return NextResponse.json(result, { status: response.status });
  } catch (error) {
    console.error('DELETE API error:', error);
    return NextResponse.json({ error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' }, { status: 500 });
  }
} 