import React from "react";
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
}

export function BlogPostCard({
  category,
  tags,
  title,
  desc,
  author,
  date,
}: BlogPostCardProps) {
  return (
    <Card shadow={true}>
      <CardBody className="p-6">
        <Typography variant="small" color="blue" className="mb-2 !font-medium">
          {category}
        </Typography>
        <Typography
          as="a"
          href="#"
          variant="h5"
          color="blue-gray"
          className="mb-2 normal-case transition-colors hover:text-gray-900"
        >
          {title}
        </Typography>
        <Typography className="mb-6 font-normal !text-gray-500">
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