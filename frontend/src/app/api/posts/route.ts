import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET() {
  try {
    console.log('Posts API called');
    console.log('Backend URL:', `${BACKEND_URL}/api/v1/mcp-servers/`);
    
    const response = await fetch(`${BACKEND_URL}/api/v1/mcp-servers/`);
    console.log('Backend response status:', response.status);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend error response:', errorText);
      throw new Error(`Backend API error: ${response.status}, message: ${errorText}`);
    }
    
    const mcps = await response.json();
    console.log('Backend MCPs data length:', Array.isArray(mcps) ? mcps.length : 'not array');
    
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
        favorites_count: mcp.favorites_count || 0,
        author: {
          img: mcp.owner?.avatar_url || "/image/avatar1.jpg",
          name: mcp.owner ? mcp.owner.nickname : "Unknown User",
          username: mcp.owner ? mcp.owner.username : "Unknown",
        },
      };
    });

    console.log('Transformed posts data length:', posts.length);
    console.log('First post:', posts[0]);
    console.log('Posts favorites_count:', posts.map(p => ({ title: p.title, favorites_count: p.favorites_count })));
    return NextResponse.json(posts);
  } catch (error) {
    console.error('Posts API error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
} 