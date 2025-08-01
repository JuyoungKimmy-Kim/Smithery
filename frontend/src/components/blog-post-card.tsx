import React from "react";
import { useRouter } from "next/navigation";
import TagList from "./tag-list";

interface BlogPostCardProps {
  category: string;
  tags: string;
  title: string;
  desc: string;
  author: { name: string; img: string };
  date: string;
  id?: string; // MCP 서버 ID 추가
}

export function BlogPostCard({
  category,
  tags,
  title,
  desc,
  author,
  date,
  id,
}: BlogPostCardProps) {
  const router = useRouter();

  const handleClick = () => {
    console.log("Card clicked! ID:", id); // 디버깅 로그 추가
    console.log("Card title:", title); // 제목도 로깅
    if (id) {
      console.log("Navigating to:", `/mcp/${id}`); // 디버깅 로그 추가
      router.push(`/mcp/${id}`);
    } else {
      console.log("No ID provided, navigating to test page"); // 디버깅 로그 추가
      // ID가 없어도 테스트용으로 첫 번째 MCP로 이동
      // router.push 대신 window.location 사용
      window.location.href = `/mcp/1`;
    }
  };

  return (
    <div 
      className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 cursor-pointer"
      onClick={handleClick}
    >
      <div className="p-6">
        <span className="text-sm font-medium text-blue-600 mb-2 block">
          {category}
        </span>
        <h3 className="text-xl font-semibold text-gray-900 mb-2 normal-case transition-colors hover:text-gray-700 cursor-pointer">
          {title}
        </h3>
        <p className="text-gray-600 mb-6 cursor-pointer">
          {desc}
        </p>
        <div className="mb-4">
          <TagList tags={tags} maxTags={4} />
        </div>
        <div className="flex items-center gap-4">
          <img
            src={author.img}
            alt={author.name}
            className="w-8 h-8 rounded-full"
          />
          <div>
            <p className="text-sm font-medium text-gray-900 mb-0.5">
              {author.name}
            </p>
            <p className="text-xs text-gray-500">
              {date}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default BlogPostCard;