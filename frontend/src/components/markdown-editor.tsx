"use client";

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize';
import { EyeIcon, PencilIcon } from '@heroicons/react/24/outline';
import type { Components } from 'react-markdown';

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  required?: boolean;
  error?: string;
  rows?: number;
}

export default function MarkdownEditor({
  value,
  onChange,
  placeholder = "Enter description (Markdown supported)",
  required = false,
  error,
  rows = 10
}: MarkdownEditorProps) {
  const [activeTab, setActiveTab] = useState<'edit' | 'preview'>('edit');

  // Extended sanitize schema to support more Markdown features
  const sanitizeSchema = {
    ...defaultSchema,
    attributes: {
      ...defaultSchema.attributes,
      code: [...(defaultSchema.attributes?.code || []), 'className'],
      div: [...(defaultSchema.attributes?.div || []), 'className'],
      span: [...(defaultSchema.attributes?.span || []), 'className'],
      pre: [...(defaultSchema.attributes?.pre || []), 'className'],
      img: [...(defaultSchema.attributes?.img || []), 'alt', 'src', 'title', 'width', 'height'],
      a: [...(defaultSchema.attributes?.a || []), 'href', 'title', 'target', 'rel'],
      input: [...(defaultSchema.attributes?.input || []), 'type', 'checked', 'disabled'],
    },
    tagNames: [
      ...(defaultSchema.tagNames || []),
      'input', // for task lists
    ],
  };

  // Custom components for better styling
  const components: Components = {
    code({ node, inline, className, children, ...props }: any) {
      const match = /language-(\w+)/.exec(className || '');
      return !inline ? (
        <pre
          className="rounded p-4 overflow-x-auto my-4"
          style={{
            backgroundColor: '#1e293b',
          }}
        >
          <code
            className={className}
            style={{
              color: '#e2e8f0'
            }}
            {...props}
          >
            {children}
          </code>
        </pre>
      ) : (
        <code
          style={{
            backgroundColor: '#f1f5f9',
            color: '#1e293b',
            padding: '2px 6px',
            borderRadius: '4px',
            fontFamily: 'monospace',
            fontSize: '0.9em'
          }}
          {...props}
        >
          {children}
        </code>
      );
    },
    img({ node, ...props }: any) {
      return (
        <img
          {...props}
          className="max-w-full h-auto rounded-lg my-4"
          loading="lazy"
        />
      );
    },
    a({ node, ...props }: any) {
      return (
        <a
          {...props}
          className="text-blue-600 hover:text-blue-800 underline"
          target="_blank"
          rel="noopener noreferrer"
        />
      );
    },
    table({ node, ...props }: any) {
      return (
        <div className="overflow-x-auto my-4">
          <table className="min-w-full divide-y divide-gray-300 border border-gray-300" {...props} />
        </div>
      );
    },
    thead({ node, ...props }: any) {
      return <thead className="bg-gray-50" {...props} />;
    },
    th({ node, ...props }: any) {
      return <th className="px-4 py-2 text-left text-sm font-semibold text-gray-900 border border-gray-300" {...props} />;
    },
    td({ node, ...props }: any) {
      return <td className="px-4 py-2 text-sm text-gray-700 border border-gray-300" {...props} />;
    },
    blockquote({ node, ...props }: any) {
      return <blockquote className="border-l-4 border-gray-300 pl-4 italic my-4 text-gray-700" {...props} />;
    },
    ul({ node, ...props }: any) {
      return <ul className="list-disc list-inside my-2 space-y-1" {...props} />;
    },
    ol({ node, ...props }: any) {
      return <ol className="list-decimal list-inside my-2 space-y-1" {...props} />;
    },
    li({ node, children, ...props }: any) {
      // Check if this is a task list item
      const childStr = String(children);
      if (childStr.includes('type="checkbox"')) {
        return <li className="flex items-start gap-2" {...props}>{children}</li>;
      }
      return <li className="ml-4" {...props}>{children}</li>;
    },
    hr({ node, ...props }: any) {
      return <hr className="my-6 border-t border-gray-300" {...props} />;
    },
  };

  return (
    <div className="w-full">
      {/* Tab Navigation */}
      <div className="flex border-b border-gray-300 mb-2">
        <button
          type="button"
          onClick={() => setActiveTab('edit')}
          className={`px-4 py-2 text-sm font-medium flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'edit'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-800'
          }`}
        >
          <PencilIcon className="h-4 w-4" />
          Edit
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('preview')}
          className={`px-4 py-2 text-sm font-medium flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'preview'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-800'
          }`}
        >
          <EyeIcon className="h-4 w-4" />
          Preview
        </button>
      </div>

      {/* Editor / Preview Content */}
      <div className="relative">
        {activeTab === 'edit' ? (
          <textarea
            required={required}
            rows={rows}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm ${
              error ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder={placeholder}
          />
        ) : (
          <div className={`w-full px-3 py-2 border rounded-md min-h-[${rows * 24}px] bg-gray-50 ${
            error ? 'border-red-500' : 'border-gray-300'
          }`}>
            {value ? (
              <div className="max-w-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeRaw, [rehypeSanitize, sanitizeSchema]]}
                  components={components}
                >
                  {value}
                </ReactMarkdown>
              </div>
            ) : (
              <p className="text-gray-400 text-sm">Nothing to preview</p>
            )}
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
}
