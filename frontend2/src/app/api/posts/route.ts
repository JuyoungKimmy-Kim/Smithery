import { NextResponse } from 'next/server';
import sqlite3 from 'sqlite3';
import path from 'path';

interface DatabaseRow {
  name: string;
  description: string;
  category: string;
  tags: string;
  created_at: string;
}

export async function GET() {
  try {
    // 데이터베이스 파일 경로
    const dbPath = '/home/kimmy/code/ds-smithery/mcp_market.db';
    console.log('Database path:', dbPath);
    console.log('File exists:', require('fs').existsSync(dbPath));
    
    const db = new sqlite3.Database(dbPath);
    
    return new Promise((resolve) => {
      db.all(
        'SELECT name, description, category, tags, created_at FROM mcp_server ORDER BY created_at DESC',
        [],
        (err: Error | null, rows: DatabaseRow[]) => {
          db.close();
          
          if (err) {
            console.error('Database error:', err);
            resolve(NextResponse.json({ error: 'Database error' }, { status: 500 }));
            return;
          }
          
          // 기본 아바타 배열
          const defaultAvatars = [
            '/image/avatar1.jpg',
            '/image/avatar2.jpg',
            '/image/avatar3.jpg',
          ];
          
          // 기본 작성자 배열
          const defaultAuthors = [
            'Ryan Samuel',
            'Nora Hazel',
            'Otto Gonzalez',
          ];
          
          const posts = rows.map((row: DatabaseRow, index: number) => ({
            category: row.category || 'Unknown',
            tags: row.tags || '[]',
            title: row.name,
            desc: row.description || 'No description available.',
            date: row.created_at ? new Date(row.created_at).toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            }) : 'Unknown date',
            author: {
              img: defaultAvatars[index % defaultAvatars.length],
              name: defaultAuthors[index % defaultAuthors.length],
            },
          }));
          
          console.log(`Returning ${posts.length} posts from database`);
          resolve(NextResponse.json(posts));
        }
      );
    });
  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
} 