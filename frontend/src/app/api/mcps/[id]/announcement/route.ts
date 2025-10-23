import { NextResponse } from 'next/server';

const BACKEND_URL = 'http://localhost:8000';

export async function PUT(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const body = await request.json();
    
    // Authorization 헤더에서 토큰 추출
    const authHeader = request.headers.get('authorization');
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (authHeader) {
      headers['Authorization'] = authHeader;
    }
    
    console.log(`Frontend API: Updating announcement for MCP server ${id}`);
    console.log('Request body:', body);
    
    const response = await fetch(`${BACKEND_URL}/api/v1/mcp-servers/${id}/announcement`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(body),
    });
    
    console.log(`Backend response status: ${response.status}`);
    
    if (!response.ok) {
      const errorData = await response.json();
      console.error('Backend API error:', errorData);
      return NextResponse.json(errorData, { status: response.status });
    }
    
    const result = await response.json();
    console.log('Backend response data:', result);
    return NextResponse.json(result);
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
    
    // Authorization 헤더에서 토큰 추출
    const authHeader = request.headers.get('authorization');
    const headers: Record<string, string> = {};
    
    if (authHeader) {
      headers['Authorization'] = authHeader;
    }
    
    console.log(`Frontend API: Deleting announcement for MCP server ${id}`);
    
    const response = await fetch(`${BACKEND_URL}/api/v1/mcp-servers/${id}/announcement`, {
      method: 'DELETE',
      headers,
    });
    
    console.log(`Backend response status: ${response.status}`);
    
    if (!response.ok) {
      const errorData = await response.json();
      console.error('Backend API error:', errorData);
      return NextResponse.json(errorData, { status: response.status });
    }
    
    const result = await response.json();
    console.log('Backend response data:', result);
    return NextResponse.json(result);
  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
