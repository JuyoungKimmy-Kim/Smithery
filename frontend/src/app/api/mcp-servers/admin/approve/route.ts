import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const token = request.headers.get('authorization')?.replace('Bearer ', '');
    
    console.log('Approve MCP server API called');
    console.log('Token:', token ? 'exists' : 'not found');
    
    if (!token) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();
    const { mcp_server_id, action } = body;

    console.log('Approve request:', { mcp_server_id, action });

    const backendUrl = `${process.env.BACKEND_URL || 'http://localhost:8000'}/api/v1/mcp-servers/admin/approve`;
    console.log('Backend URL:', backendUrl);

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        mcp_server_id,
        action
      }),
    });

    console.log('Backend response status:', response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend error response:', errorText);
      
      if (response.status === 500) {
        console.error('Backend internal server error');
        return NextResponse.json(
          { error: 'Backend internal server error', details: errorText },
          { status: 500 }
        );
      }
      
      return NextResponse.json(
        { error: 'Backend error', details: errorText },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('Backend response data:', data);
    
    // 성공 응답인지 확인
    if (data && (data.id || data.name)) {
      console.log('Approval successful for server:', data.name || data.id);
      return NextResponse.json({ success: true, data });
    } else {
      console.error('Unexpected response format:', data);
      return NextResponse.json(
        { error: 'Unexpected response format', details: data },
        { status: 500 }
      );
    }
  } catch (error) {
    console.error('Error approving MCP server:', error);
    return NextResponse.json(
      { error: 'Failed to approve MCP server', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
} 