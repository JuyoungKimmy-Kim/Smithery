import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { CheckIcon, XMarkIcon } from "@heroicons/react/24/outline";
import TagList from "./tag-list";

interface AdminServerCardProps {
  category: string;
  tags: string;
  title: string;
  desc: string;
  author: { name: string; img: string };
  date: string;
  id?: string;
  onApprove?: (id: string) => void;
  onReject?: (id: string) => void;
}

export function AdminServerCard({
  category,
  tags,
  title,
  desc,
  author,
  date,
  id,
  onApprove,
  onReject,
}: AdminServerCardProps) {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const handleClick = () => {
    if (id) {
      router.push(`/mcp/${id}`);
    }
  };

  const handleApprove = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!id || isLoading) return;

    setIsLoading(true);
    try {
      const response = await fetch('/api/mcp-servers/admin/approve', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          mcp_server_id: parseInt(id),
          action: 'approve'
        })
      });

      if (response.ok) {
        const responseData = await response.json();
        console.log('Server approved successfully:', responseData);
        if (onApprove) {
          onApprove(id);
        }
      } else {
        const errorData = await response.json();
        console.error('Failed to approve server:', errorData);
        alert('승인에 실패했습니다.');
      }
    } catch (error) {
      console.error('Error approving server:', error);
      alert('승인 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReject = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!id || isLoading) return;

    if (!confirm('정말로 이 서버를 거부하시겠습니까?')) {
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('/api/mcp-servers/admin/approve', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          mcp_server_id: parseInt(id),
          action: 'reject'
        })
      });

      if (response.ok) {
        const responseData = await response.json();
        console.log('Server rejected successfully:', responseData);
        if (onReject) {
          onReject(id);
        }
      } else {
        const errorData = await response.json();
        console.error('Failed to reject server:', errorData);
        alert('거부에 실패했습니다.');
      }
    } catch (error) {
      console.error('Error rejecting server:', error);
      alert('거부 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div 
      className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 cursor-pointer relative border-l-4 border-yellow-500"
      onClick={handleClick}
    >
      {/* 승인/거부 버튼 */}
      <div className="absolute top-4 right-4 z-10 flex gap-2">
        <button
          onClick={handleApprove}
          disabled={isLoading}
          className={`p-2 rounded-full transition-all duration-200 bg-green-500 text-white hover:bg-green-600 ${
            isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:scale-110'
          }`}
          title="승인"
        >
          <CheckIcon className="h-4 w-4" />
        </button>
        <button
          onClick={handleReject}
          disabled={isLoading}
          className={`p-2 rounded-full transition-all duration-200 bg-red-500 text-white hover:bg-red-600 ${
            isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:scale-110'
          }`}
          title="거부"
        >
          <XMarkIcon className="h-4 w-4" />
        </button>
      </div>

      <div className="p-6">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-sm font-medium text-blue-600">
            {category}
          </span>
          <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full">
            승인 대기중
          </span>
        </div>
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
            src={author?.img || '/image/avatar1.jpg'}
            alt={author?.name || 'Unknown'}
            className="w-8 h-8 rounded-full"
          />
          <div>
            <p className="text-sm font-medium text-gray-900 mb-0.5">
              {author?.name || 'Unknown'}
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

export default AdminServerCard; 