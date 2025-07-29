"use client";

import React, { useState, useEffect } from "react";
import {
  Button,
  Typography,
  Tabs,
  TabsHeader,
  Tab,
} from "@material-tailwind/react";
import { ArrowSmallDownIcon } from "@heroicons/react/24/solid";
import BlogPostCard from "@/components/blog-post-card";
import { MCPServer } from "@/types/mcp";

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
      <Tabs value="trends" className="mx-auto max-w-7xl w-full mb-8">
        <div className="w-full flex mb-4 flex-col items-center">
          <TabsHeader className="h-10 !w-12/12 md:w-[50rem] border border-white/25 bg-opacity-90">
            <Tab value="Code Tools">Code Tools</Tab>
            <Tab value="Documentation">Documentation</Tab>
            <Tab value="Data & Search">Data & Search</Tab>
            <Tab value="Automation">Automation</Tab>
            <Tab value="DevOps">DevOps</Tab>
            <Tab value="Miscellaneous">Miscellaneous</Tab>
          </TabsHeader>
        </div>
      </Tabs>
      <Typography variant="h6" className="mb-2">
        Latest MCP Lists
      </Typography>
      {loading ? (
        <div className="text-center py-8">
          <Typography variant="h6" color="gray">
            Loading posts...
          </Typography>
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
      <Button
        variant="text"
        size="lg"
        color="gray"
        className="flex items-center gap-2 mt-24"
      >
        <ArrowSmallDownIcon className="h-5 w-5 font-bold text-gray-900" />
        VIEW MORE
      </Button>
    </section>
  );
}

export default Posts;
