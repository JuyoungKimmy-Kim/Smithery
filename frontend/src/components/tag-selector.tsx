import React, { useState, useEffect } from "react";
import { CheckIcon, PlusIcon } from "@heroicons/react/24/solid";

interface TagSelectorProps {
  selectedTags: string[];
  onTagsChange: (tags: string[]) => void;
  allTags: string[];
  tagCounts: {[key: string]: number};
  onNewTagAdded?: (newTag: string) => void;
}

export function TagSelector({ selectedTags, onTagsChange, allTags, tagCounts, onNewTagAdded }: TagSelectorProps) {
  const [newTag, setNewTag] = useState("");
  const [showAddTag, setShowAddTag] = useState(false);

  const handleTagToggle = (tag: string) => {
    const newSelectedTags = selectedTags.includes(tag)
      ? selectedTags.filter(t => t !== tag)
      : [...selectedTags, tag];
    onTagsChange(newSelectedTags);
  };

  const handleAddNewTag = () => {
    const trimmedTag = newTag.trim();
    if (trimmedTag && !selectedTags.includes(trimmedTag)) {
      onTagsChange([...selectedTags, trimmedTag]);
      if (onNewTagAdded) {
        onNewTagAdded(trimmedTag);
      }
      setNewTag("");
      setShowAddTag(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddNewTag();
    } else if (e.key === 'Escape') {
      setNewTag("");
      setShowAddTag(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* 기존 태그들 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          태그 선택
        </label>
        <div className="flex flex-wrap gap-2">
          {allTags.map((tag) => (
            <button
              key={tag}
              type="button"
              onClick={() => handleTagToggle(tag)}
              className={`px-4 py-2 text-sm font-medium transition-all duration-200 rounded-full flex items-center gap-2 ${
                selectedTags.includes(tag)
                  ? 'bg-blue-500 text-white shadow-md scale-105'
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }`}
            >
              <span>{tag}</span>
              <span className="text-xs opacity-75">({tagCounts[tag]})</span>
              {selectedTags.includes(tag) ? (
                <CheckIcon className="h-4 w-4" />
              ) : (
                <PlusIcon className="h-4 w-4" />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* 새 태그 추가 */}
      <div>
        {!showAddTag ? (
          <button
            type="button"
            onClick={() => setShowAddTag(true)}
            className="px-4 py-2 text-sm font-medium text-blue-600 border border-blue-600 rounded-full hover:bg-blue-50 transition-colors"
          >
            + 새 태그 추가
          </button>
        ) : (
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="새 태그 입력"
              className="px-3 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              autoFocus
            />
            <button
              type="button"
              onClick={handleAddNewTag}
              disabled={!newTag.trim() || selectedTags.includes(newTag.trim())}
              className="px-3 py-2 bg-blue-500 text-white rounded-full hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors text-sm"
            >
              추가
            </button>
            <button
              type="button"
              onClick={() => {
                setNewTag("");
                setShowAddTag(false);
              }}
              className="px-3 py-2 bg-gray-200 text-gray-700 rounded-full hover:bg-gray-300 transition-colors text-sm"
            >
              취소
            </button>
          </div>
        )}
      </div>

      {/* 선택된 태그 표시 */}
      {selectedTags.length > 0 && (
        <div>
          <p className="text-sm text-gray-600 mb-2">
            선택된 태그: {selectedTags.join(', ')}
          </p>
        </div>
      )}
    </div>
  );
}

export default TagSelector;
