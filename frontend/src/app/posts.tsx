"use client";

import React, { useState, useEffect } from "react";
import { ArrowSmallDownIcon } from "@heroicons/react/24/solid";
import BlogPostCard from "@/components/blog-post-card";
import { MCPServer } from "@/types/mcp";
import { MCP_CATEGORIES } from "@/constants/categories";

interface Post {
  category: string;
  tags: string;
  title: string;
  desc: string;
  date: string;
  author: {
    img: string;
    name: string;
  };
  id?: string;
}

export function Posts() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("Code Tools");

  useEffect(() => {
    const fetchPosts = async () => {
      try {
        const response = await fetch('/api/posts');
        if (response.ok) {
          const data = await response.json();
          console.log('Frontend received posts:', data); // 디버깅 로그 추가
          console.log('First post ID:', data[0]?.id); // 첫 번째 포스트의 ID 확인
          setPosts(data);
        } else {
          console.error('Failed to fetch posts');
        }
      } catch (error) {
        console.error('Error fetching posts:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPosts();
  }, []);

  return (
    <section className="grid min-h-screen place-items-center p-8">
      <div className="mx-auto max-w-7xl w-full mb-8">
        <div className="w-full flex mb-4 flex-col items-center">
          <div className="h-10 w-full md:w-[50rem] border border-gray-300 rounded-lg bg-white bg-opacity-90 flex">
            {MCP_CATEGORIES.map((category) => (
              <button
                key={category}
                onClick={() => setActiveTab(category)}
                className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
                  activeTab === category
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-700 hover:bg-gray-100'
                } ${category === MCP_CATEGORIES[0] ? 'rounded-l-lg' : ''} ${
                  category === MCP_CATEGORIES[MCP_CATEGORIES.length - 1] ? 'rounded-r-lg' : ''
                }`}
              >
                {category}
              </button>
            ))}
          </div>
        </div>
      </div>
      <h2 className="text-xl font-semibold text-gray-900 mb-2">
        Latest MCP Lists
      </h2>
      {loading ? (
        <div className="text-center py-8">
          <h3 className="text-lg text-gray-600">
            Loading posts...
          </h3>
        </div>
      ) : (
        <div className="container my-auto grid grid-cols-1 gap-x-8 gap-y-16 items-start lg:grid-cols-3">
          {posts.map(({ category, tags, title, desc, date, author, id }) => (
            <BlogPostCard
              key={title}
              category={category}
              tags={tags}
              title={title}
              desc={desc}
              date={date}
              author={{
                img: author.img,
                name: author.name,
              }}
              id={id}
            />
          ))}
        </div>
      )}
      <button className="flex items-center gap-2 mt-24 text-gray-700 hover:text-gray-900 transition-colors">
        <ArrowSmallDownIcon className="h-5 w-5 font-bold text-gray-900" />
        VIEW MORE
      </button>
    </section>
  );
}

export default Posts;
