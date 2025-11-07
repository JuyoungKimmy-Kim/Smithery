"use client";

import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { LanguageIcon } from '@heroicons/react/24/solid';

export default function GettingStartedPage() {
  const [markdown, setMarkdown] = useState('');
  const [language, setLanguage] = useState<'en' | 'ko'>('en');

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const storedLanguage = localStorage.getItem('wiki-language');
    if (storedLanguage === 'ko' || storedLanguage === 'en') {
      setLanguage(storedLanguage);
    }
  }, []);

  const handleLanguageToggle = () => {
    const nextLanguage = language === 'ko' ? 'en' : 'ko';
    setLanguage(nextLanguage);
    if (typeof window !== 'undefined') {
      localStorage.setItem('wiki-language', nextLanguage);
    }
  };

  useEffect(() => {
    const fileName = language === 'en' ? 'getting-started.en.md' : 'getting-started.md';
    fetch(`/content/wiki/${fileName}`)
      .then((res) => res.text())
      .then((text) => setMarkdown(text))
      .catch((err) => console.error('Failed to load markdown:', err));
  }, [language]);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-12">
        <div className="bg-white rounded-lg shadow-md p-8 max-w-4xl mx-auto">
          {/* Language Toggle Button */}
          <div className="flex justify-end mb-6">
            <button
              onClick={handleLanguageToggle}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              <LanguageIcon className="h-5 w-5" />
              {language === 'ko' ? '한국어 (KO)' : 'English (EN)'}
            </button>
          </div>
          <article className="prose prose-lg max-w-none">
            <ReactMarkdown 
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({ node, ...props }) => <h1 className="text-4xl font-bold text-gray-900 mb-6" {...props} />,
                h2: ({ node, ...props }) => <h2 className="text-3xl font-bold text-gray-900 mt-8 mb-4" {...props} />,
                h3: ({ node, ...props }) => <h3 className="text-2xl font-semibold text-gray-800 mt-6 mb-3" {...props} />,
                p: ({ node, ...props }) => <p className="text-gray-700 mb-4 leading-relaxed" {...props} />,
                ul: ({ node, ...props }) => <ul className="list-disc list-inside mb-4 space-y-2 text-gray-700" {...props} />,
                ol: ({ node, ...props }) => <ol className="list-decimal list-inside mb-4 space-y-2 text-gray-700" {...props} />,
                li: ({ node, ...props }) => <li className="ml-4" {...props} />,
                a: ({ node, ...props }) => <a className="text-blue-600 hover:text-blue-800 underline" {...props} />,
                code: ({ node, inline, ...props }: any) => 
                  inline 
                    ? <code className="bg-gray-100 px-2 py-1 rounded text-sm font-mono text-gray-800" {...props} />
                    : <code className="block bg-gray-100 p-4 rounded-lg text-sm font-mono text-gray-800 overflow-x-auto" {...props} />,
                blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-blue-500 pl-4 italic text-gray-600 my-4" {...props} />,
              }}
            >
              {markdown}
            </ReactMarkdown>
          </article>
        </div>
      </div>
    </div>
  );
}
