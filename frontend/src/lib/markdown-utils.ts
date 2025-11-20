/**
 * Markdown 텍스트에서 Markdown 문법을 제거하고 plain text만 반환
 */
export function stripMarkdown(markdown: string): string {
  if (!markdown) return '';

  let text = markdown;

  // Remove code blocks (keep content)
  text = text.replace(/```[\s\S]*?```/g, '[code block]');

  // Remove inline code backticks (keep content)
  text = text.replace(/`([^`]+)`/g, '$1');

  // Remove headers
  text = text.replace(/#{1,6}\s+/g, '');

  // Remove bold
  text = text.replace(/\*\*(.+?)\*\*/g, '$1');
  text = text.replace(/__(.+?)__/g, '$1');

  // Remove italic
  text = text.replace(/\*(.+?)\*/g, '$1');
  text = text.replace(/_(.+?)_/g, '$1');

  // Remove strikethrough
  text = text.replace(/~~(.+?)~~/g, '$1');

  // Remove links
  text = text.replace(/\[(.+?)\]\(.+?\)/g, '$1');

  // Remove images
  text = text.replace(/!\[.*?\]\(.+?\)/g, '');

  // Remove blockquotes
  text = text.replace(/^>\s+/gm, '');

  // Remove horizontal rules
  text = text.replace(/^(-{3,}|\*{3,}|_{3,})$/gm, '');

  // Remove list markers
  text = text.replace(/^[\s]*[-*+]\s+/gm, '');
  text = text.replace(/^[\s]*\d+\.\s+/gm, '');

  // Remove extra whitespace
  text = text.replace(/\n{3,}/g, '\n\n');
  text = text.trim();

  return text;
}

/**
 * Markdown 텍스트를 요약하여 반환 (plain text로 변환 후 truncate)
 */
export function summarizeMarkdown(markdown: string, maxLength: number = 150): string {
  const plainText = stripMarkdown(markdown);

  if (plainText.length <= maxLength) {
    return plainText;
  }

  return plainText.substring(0, maxLength).trim() + '...';
}
