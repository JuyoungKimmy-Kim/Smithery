import { NextResponse } from 'next/server';

export async function GET() {
  console.log('Test AD API endpoint hit!');
  return NextResponse.json({ message: 'Test AD API working!' });
}

export async function POST(request: Request) {
  console.log('Test AD API POST endpoint hit!');
  
  try {
    const body = await request.json();
    console.log('Test AD API - Received body:', body);
    
    return NextResponse.json({ 
      message: 'Test AD API POST working!',
      receivedData: body 
    });
  } catch (error) {
    console.error('Test AD API error:', error);
    return NextResponse.json({ error: 'Failed to parse body' }, { status: 400 });
  }
} 