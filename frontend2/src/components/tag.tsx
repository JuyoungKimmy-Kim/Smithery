import React from "react";
import { Typography } from "@material-tailwind/react";

interface TagProps {
  text: string;
  color?: "blue" | "green" | "red" | "yellow" | "purple" | "gray";
  size?: "sm" | "md" | "lg";
}

export function Tag({ text, color = "blue", size = "md" }: TagProps) {
  const colorClasses = {
    blue: "bg-blue-100 text-blue-800 border-blue-200",
    green: "bg-green-100 text-green-800 border-green-200",
    red: "bg-red-100 text-red-800 border-red-200",
    yellow: "bg-yellow-100 text-yellow-800 border-yellow-200",
    purple: "bg-purple-100 text-purple-800 border-purple-200",
    gray: "bg-gray-100 text-gray-800 border-gray-200",
  };

  const sizeClasses = {
    sm: "px-2 py-1 text-xs",
    md: "px-3 py-1.5 text-sm",
    lg: "px-4 py-2 text-base",
  };

  return (
    <span
      className={`
        inline-flex items-center
        ${colorClasses[color]}
        ${sizeClasses[size]}
        rounded-full border
        font-medium
        transition-colors duration-200
        hover:opacity-80
        cursor-default
      `}
    >
      {text}
    </span>
  );
}

export default Tag; 