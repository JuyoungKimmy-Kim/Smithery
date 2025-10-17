import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const token = request.headers.get('authorization')?.replace('Bearer ', '');
    
    console.log('Pending servers API called');
    console.log('Token:', token ? 'exists' : 'not found');
    
    if (!token) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const backendUrl = `${process.env.BACKEND_URL || 'http://localhost:8000'}/api/v1/mcp-servers/?status=pending`;
    console.log('Backend URL:', backendUrl);

    const response = await fetch(backendUrl, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
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
    console.log('Backend response data length:', Array.isArray(data) ? data.length : 'not array');
    
    // 데이터 형식 변환
    const transformedData = Array.isArray(data) ? data.map(server => ({
      id: server.id,
      category: server.category,
      tags: server.tags?.map((tag: any) => tag.name).join(', ') || '',
      title: server.name,
      desc: server.description,
      date: new Date(server.created_at).toLocaleDateString(),
      author: {
        img: server.owner?.avatar_url || '/image/avatar1.jpg',
        nickname: server.owner?.nickname || 'Unknown',
        username: server.owner?.username || 'Unknown'
      }
    })) : [];
    
    console.log('Transformed data:', transformedData);
    return NextResponse.json(transformedData);
  } catch (error) {
    console.error('Error fetching pending MCP servers:', error);
    return NextResponse.json(
      { error: 'Failed to fetch pending MCP servers', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
} 