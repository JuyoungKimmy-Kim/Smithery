import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;

    console.log(`Health check request for MCP server ${id}`);
    console.log(`Backend URL: ${BACKEND_URL}/api/v1/mcp-servers/${id}/health-check`);

    const response = await fetch(`${BACKEND_URL}/api/v1/mcp-servers/${id}/health-check`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    console.log(`Backend response status: ${response.status}`);

    // Try to get response text first
    const responseText = await response.text();
    console.log(`Backend response text: ${responseText.substring(0, 200)}`);

    if (!response.ok) {
      // Try to parse as JSON, if fails return text error
      try {
        const errorData = JSON.parse(responseText);
        return NextResponse.json(errorData, { status: response.status });
      } catch (parseError) {
        console.error('Failed to parse error response as JSON:', parseError);
        return NextResponse.json(
          { error: 'Backend error', details: responseText },
          { status: response.status }
        );
      }
    }

    // Try to parse successful response as JSON
    try {
      const result = JSON.parse(responseText);
      return NextResponse.json(result);
    } catch (parseError) {
      console.error('Failed to parse success response as JSON:', parseError);
      return NextResponse.json(
        { error: 'Invalid JSON response from backend', details: responseText },
        { status: 500 }
      );
    }
  } catch (error) {
    console.error('Health check API error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
