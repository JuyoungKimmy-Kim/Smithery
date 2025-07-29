import { NextResponse } from 'next/server';

const BACKEND_URL = 'http://localhost:8080';

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/mcps/${params.id}`);
    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json({ error: 'MCP server not found' }, { status: 404 });
      }
      throw new Error(`Backend API error: ${response.status}`);
    }
    const mcp = await response.json();
    return NextResponse.json(mcp);
  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function PUT(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const body = await request.json();
    const response = await fetch(`${BACKEND_URL}/api/mcps/${params.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    
    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json({ error: 'MCP server not found' }, { status: 404 });
      }
      throw new Error(`Backend API error: ${response.status}`);
    }
    
    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function DELETE(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/mcps/${params.id}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json({ error: 'MCP server not found' }, { status: 404 });
      }
      throw new Error(`Backend API error: ${response.status}`);
    }
    
    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
} 