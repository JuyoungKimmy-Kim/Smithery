import React from "react";
import { useRouter } from "next/navigation";
import {
  Typography,
  Card,
  CardBody,
  Avatar,
} from "@material-tailwind/react";
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
    <Card 
      shadow={true} 
      className="cursor-pointer hover:shadow-lg transition-shadow duration-200"
      onClick={handleClick}
    >
      <CardBody className="p-6">
        <Typography variant="small" color="blue" className="mb-2 !font-medium">
          {category}
        </Typography>
        <Typography
          variant="h5"
          color="blue-gray"
          className="mb-2 normal-case transition-colors hover:text-gray-900 cursor-pointer"
        >
          {title}
        </Typography>
        <Typography className="mb-6 font-normal !text-gray-500 cursor-pointer">
          {desc}
        </Typography>
        <div className="mb-4">
          <TagList tags={tags} maxTags={4} />
        </div>
        <div className="flex items-center gap-4">
          <Avatar
            size="sm"
            variant="circular"
            src={author.img}
            alt={author.name}
          />
          <div>
            <Typography
              variant="small"
              color="blue-gray"
              className="mb-0.5 !font-medium"
            >
              {author.name}
            </Typography>
            <Typography
              variant="small"
              color="gray"
              className="text-xs !text-gray-500 font-normal"
            >
              {date}
            </Typography>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}

export default BlogPostCard;