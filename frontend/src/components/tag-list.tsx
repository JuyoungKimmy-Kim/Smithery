import React from "react";
import Tag from "./tag";

interface TagListProps {
  tags: string | undefined | null;
  maxTags?: number;
}

export function TagList({ tags, maxTags = 5 }: TagListProps) {
  // tags가 undefined, null, 또는 빈 문자열인 경우 빈 배열 반환
  if (!tags || (typeof tags === 'string' && tags.trim() === '')) {
    return <div className="flex flex-wrap gap-2"></div>;
  }

  // tags가 JSON 문자열인 경우 파싱, 아니면 쉼표로 분리
  let tagArray: string[] = [];
  
  try {
    // JSON 형태인지 확인
    const parsed = JSON.parse(tags);
    tagArray = Array.isArray(parsed) ? parsed : [parsed];
  } catch {
    // JSON이 아니면 쉼표로 분리 (string 타입 확인 후)
    if (typeof tags === 'string') {
      tagArray = tags.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0);
    } else {
      tagArray = [];
    }
  }

  // 최대 태그 수 제한
  const displayTags = tagArray.slice(0, maxTags);
  const remainingCount = tagArray.length - maxTags;

  const tagColors = [
    "blue", "green", "red", "yellow", "purple", "gray"
  ];

  return (
    <div className="flex flex-wrap gap-2">
      {displayTags.map((tag, index) => (
        <Tag
          key={index}
          text={tag}
          color={tagColors[index % tagColors.length] as any}
          size="sm"
        />
      ))}
      {remainingCount > 0 && (
        <span className="text-xs text-gray-500 self-center">
          +{remainingCount} more
        </span>
      )}
    </div>
  );
}

export default TagList; 