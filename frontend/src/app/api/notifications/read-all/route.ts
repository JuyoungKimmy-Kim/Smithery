import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(request: Request) {
  try {
    const authHeader = request.headers.get('authorization');

    const response = await fetch(
      `${BACKEND_URL}/api/v1/notifications/read-all`,
      {
        method: 'POST',
        headers: {
          'Authorization': authHeader || '',
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      }
    );

    if (!response.ok) {
      console.error(`Backend API error: ${response.status}`);
      const errorData = await response.json();
      return NextResponse.json(errorData, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error marking all as read:', error);
    return NextResponse.json(
      { error: 'Failed to mark all as read' },
      { status: 500 }
    );
  }
}
