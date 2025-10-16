import { NextResponse } from 'next/server';

const BACKEND_URL = 'http://localhost:8000';

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const limit = searchParams.get('limit') || '3';
    
    const response = await fetch(`${BACKEND_URL}/api/v1/mcp-servers/top?limit=${limit}`, {
      cache: 'no-store',
      headers: {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`);
    }
    
    const mcps = await response.json();
    
    // MCP 서버 데이터를 포스트 형식으로 변환
    const posts = mcps.map((mcp: any) => {
      let formattedDate = "Unknown date";
      try {
        if (mcp.created_at) {
          formattedDate = new Date(mcp.created_at).toLocaleDateString();
        }
      } catch (error) {
        console.error('Date parsing error:', error);
      }

      return {
        id: mcp.id,
        category: mcp.category || "Unknown",
        tags: mcp.tags ? mcp.tags.map((tag: any) => typeof tag === 'string' ? tag : tag.name).join(', ') : "[]",
        title: mcp.name,
        desc: mcp.description || "No description available.",
        date: formattedDate,
        author: {
          img: mcp.owner?.avatar_url || "/image/avatar1.jpg",
          name: mcp.owner ? mcp.owner.username : "Unknown User",
        },
      };
    });
    
    return NextResponse.json(posts);
  } catch (error) {
    console.error('Error fetching top MCP servers:', error);
    return NextResponse.json(
      { error: 'Failed to fetch top MCP servers' },
      { status: 500 }
    );
  }
}

