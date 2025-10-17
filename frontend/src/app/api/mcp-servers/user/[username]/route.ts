import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: { username: string } }
) {
  try {
    const { username } = params;
    
    console.log('User MCP servers API called for username:', username);
    
    const backendUrl = `${process.env.BACKEND_URL || 'http://localhost:8000'}/api/v1/mcp-servers/user/${username}`;
    console.log('Backend URL:', backendUrl);

    const response = await fetch(backendUrl, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    console.log('Backend response status:', response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend error response:', errorText);
      
      if (response.status === 404) {
        return NextResponse.json(
          { error: 'User not found' },
          { status: 404 }
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
        name: server.owner?.nickname || 'Unknown',
        username: server.owner?.username || 'Unknown'
      }
    })) : [];
    
    console.log('Transformed data:', transformedData);
    return NextResponse.json(transformedData);
  } catch (error) {
    console.error('Error fetching user MCP servers:', error);
    return NextResponse.json(
      { error: 'Failed to fetch user MCP servers', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
} 