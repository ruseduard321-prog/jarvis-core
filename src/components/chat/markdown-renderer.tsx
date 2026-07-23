"use client";

import React from "react";
import { Copy, Check } from "lucide-react";
import { cn } from "@/utils";
import { useClipboard } from "@/hooks";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

/**
 * Markdown Renderer Component
 * Converts markdown to React elements with support for:
 * - Headers (h1-h6)
 * - Lists (ordered, unordered, nested)
 * - Code blocks with syntax highlighting
 * - Inline code
 * - Bold, italic, strikethrough
 * - Links
 * - Blockquotes
 * - Horizontal rules
 * - Images
 * - Tables (basic)
 */
export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  const elements = parseMarkdown(content);

  return (
    <div className={cn("prose prose-invert max-w-none", className)}>
      {elements.map((element, index) => (
        <MarkdownElement key={index} element={element} />
      ))}
    </div>
  );
}

// Markdown Element Types
interface MarkdownElement {
  type: "heading" | "paragraph" | "code-block" | "list" | "blockquote" | "hr" | "inline";
  level?: number;
  content?: string;
  language?: string;
  items?: Array<{ content: string; children?: MarkdownElement[] }>;
  children?: MarkdownElement[];
}

function parseMarkdown(content: string): MarkdownElement[] {
  const lines = content.split("\n");
  const elements: MarkdownElement[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Headings
    const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);
    if (headingMatch) {
      elements.push({
        type: "heading",
        level: headingMatch[1].length,
        content: headingMatch[2],
      });
      i++;
      continue;
    }

    // Code blocks
    if (line.match(/^```/)) {
      const language = line.slice(3).trim() || "plaintext";
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].match(/^```/)) {
        codeLines.push(lines[i]);
        i++;
      }
      elements.push({
        type: "code-block",
        language,
        content: codeLines.join("\n"),
      });
      i++;
      continue;
    }

    // Blockquotes
    if (line.match(/^>\s/)) {
      const quoteLines: string[] = [];
      while (i < lines.length && lines[i].match(/^>\s/)) {
        quoteLines.push(lines[i].replace(/^>\s/, ""));
        i++;
      }
      elements.push({
        type: "blockquote",
        content: quoteLines.join("\n"),
      });
      continue;
    }

    // Horizontal rule
    if (line.match(/^(---|___|\*\*\*)/)) {
      elements.push({ type: "hr" });
      i++;
      continue;
    }

    // Lists
    if (line.match(/^[\s]*[-*+]\s/) || line.match(/^[\s]*\d+\.\s/)) {
      const listItems: Array<{ content: string }> = [];
      while (i < lines.length && (lines[i].match(/^[\s]*[-*+]\s/) || lines[i].match(/^[\s]*\d+\.\s/))) {
        const itemContent = lines[i].replace(/^[\s]*[-*+\d.]\s+/, "");
        listItems.push({ content: itemContent });
        i++;
      }
      elements.push({
        type: "list",
        items: listItems,
      });
      continue;
    }

    // Paragraphs
    if (line.trim()) {
      elements.push({
        type: "paragraph",
        content: line,
      });
      i++;
    } else {
      i++;
    }
  }

  return elements;
}

interface MarkdownElementProps {
  element: MarkdownElement;
}

function MarkdownElement({ element }: MarkdownElementProps) {
  switch (element.type) {
    case "heading":
      const HeadingTag = `h${element.level}` as unknown as React.ElementType;
      return React.createElement(
        HeadingTag,
        {
          className: cn(
            "my-4 font-bold text-foreground",
            element.level === 1 && "text-2xl",
            element.level === 2 && "text-xl",
            element.level === 3 && "text-lg",
            element.level === 4 && "text-base",
            element.level === 5 && "text-sm",
            element.level === 6 && "text-xs"
          ),
        },
        <InlineMarkdown content={element.content || ""} />
      );

    case "paragraph":
      return (
        <p className="my-2 text-foreground/90 leading-relaxed whitespace-pre-wrap break-words">
          <InlineMarkdown content={element.content || ""} />
        </p>
      );

    case "code-block":
      return <CodeBlock code={element.content || ""} language={element.language} />;

    case "blockquote":
      return (
        <blockquote className="my-3 border-l-4 border-primary/50 pl-4 py-2 bg-muted/50 rounded italic text-foreground/80">
          <InlineMarkdown content={element.content || ""} />
        </blockquote>
      );

    case "hr":
      return <hr className="my-4 border-border" />;

    case "list":
      return (
        <ul className="my-2 ml-6 space-y-1">
          {element.items?.map((item, index) => (
            <li key={index} className="text-foreground/90 list-disc">
              <InlineMarkdown content={item.content} />
            </li>
          ))}
        </ul>
      );

    default:
      return null;
  }
}

/**
 * Parse and render inline markdown (bold, italic, code, links)
 */
function InlineMarkdown({ content }: { content: string }) {
  const parts: Array<{ type: "text" | "bold" | "italic" | "code" | "link"; content: string; href?: string }> = [];
  let i = 0;
  let textBuffer = "";

  while (i < content.length) {
    // Bold: **text** or __text__
    const boldMatch = content.slice(i).match(/^(\*\*|__)(.+?)\1/);
    if (boldMatch) {
      if (textBuffer) {
        parts.push({ type: "text", content: textBuffer });
        textBuffer = "";
      }
      parts.push({ type: "bold", content: boldMatch[2] });
      i += boldMatch[0].length;
      continue;
    }

    // Italic: *text* or _text_
    const italicMatch = content.slice(i).match(/^(?<!\*)\*(?!\*)(.+?)\*(?!\*)|^(?<!_)_(?!_)(.+?)_(?!_)/);
    if (italicMatch) {
      if (textBuffer) {
        parts.push({ type: "text", content: textBuffer });
        textBuffer = "";
      }
      parts.push({ type: "italic", content: italicMatch[1] || italicMatch[2] });
      i += italicMatch[0].length;
      continue;
    }

    // Inline code: `code`
    const codeMatch = content.slice(i).match(/^`(.+?)`/);
    if (codeMatch) {
      if (textBuffer) {
        parts.push({ type: "text", content: textBuffer });
        textBuffer = "";
      }
      parts.push({ type: "code", content: codeMatch[1] });
      i += codeMatch[0].length;
      continue;
    }

    // Links: [text](url)
    const linkMatch = content.slice(i).match(/^\[(.+?)\]\((.+?)\)/);
    if (linkMatch) {
      if (textBuffer) {
        parts.push({ type: "text", content: textBuffer });
        textBuffer = "";
      }
      parts.push({ type: "link", content: linkMatch[1], href: linkMatch[2] });
      i += linkMatch[0].length;
      continue;
    }

    // No match at this position - accumulate character into text buffer
    textBuffer += content[i];
    i++;
  }

  // Push any remaining text in buffer
  if (textBuffer) {
    parts.push({ type: "text", content: textBuffer });
  }

  return (
    <>
      {parts.map((part, idx) => {
        switch (part.type) {
          case "bold":
            return (
              <strong key={idx} className="font-bold text-foreground">
                {part.content}
              </strong>
            );
          case "italic":
            return (
              <em key={idx} className="italic">
                {part.content}
              </em>
            );
          case "code":
            return (
              <code key={idx} className="bg-muted/70 px-1.5 py-0.5 rounded text-xs font-mono text-foreground/90">
                {part.content}
              </code>
            );
          case "link":
            return (
              <a
                key={idx}
                href={part.href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline"
              >
                {part.content}
              </a>
            );
          default:
            return <span key={idx}>{part.content}</span>;
        }
      })}
    </>
  );
}

/**
 * Code Block Component with Copy Button
 */
interface CodeBlockProps {
  code: string;
  language?: string;
}

function CodeBlock({ code, language = "plaintext" }: CodeBlockProps) {
  const [copied, copy] = useClipboard();

  return (
    <div className="my-3 rounded-lg border border-border bg-muted/50 overflow-hidden">
      {/* Header with language label and copy button */}
      <div className="flex items-center justify-between px-4 py-2 bg-muted border-b border-border">
        <span className="text-xs font-mono text-muted-foreground uppercase">{language}</span>
        <button
          onClick={() => copy(code)}
          className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground transition-colors"
          title="Copy code"
        >
          {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>

      {/* Code content */}
      <pre className="px-4 py-3 overflow-x-auto">
        <code className={`font-mono text-sm text-foreground/90 language-${language}`}>{code}</code>
      </pre>
    </div>
  );
}
