import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const token = request.headers.get('authorization')?.replace('Bearer ', '');
    
    console.log('Approve all pending servers API called');
    console.log('Token:', token ? 'exists' : 'not found');
    
    if (!token) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const backendUrl = `${process.env.BACKEND_URL || 'http://localhost:8000'}/api/v1/mcp-servers/admin/approve-all`;
    console.log('Backend URL:', backendUrl);

    const response = await fetch(backendUrl, {
      method: 'POST',
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
    console.log('Backend response data:', data);
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error approving all pending servers:', error);
    return NextResponse.json(
      { error: 'Failed to approve all pending servers', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
} 