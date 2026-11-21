import React, { useState } from 'react';
import { HelpCircle, ChevronDown, ChevronUp } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ExplainPanelProps {
  title?: string;
  markdown: string;
  defaultOpen?: boolean;
  className?: string;
}

export const ExplainPanel: React.FC<ExplainPanelProps> = ({
  title = 'How This Works (Compiler Viva Guide)',
  markdown,
  defaultOpen = false,
  className = '',
}) => {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className={`border border-border rounded-lg bg-bg-1 overflow-hidden ${className}`}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-3 bg-bg-2/80 hover:bg-bg-2 transition-colors text-left"
      >
        <div className="flex items-center gap-2 text-xs font-semibold text-text-0">
          <HelpCircle className="w-4 h-4 text-accent" />
          <span>{title}</span>
        </div>
        {open ? <ChevronUp className="w-4 h-4 text-text-1" /> : <ChevronDown className="w-4 h-4 text-text-1" />}
      </button>

      {open && (
        <div className="p-4 text-xs text-text-1 leading-relaxed border-t border-border bg-bg-0/60 prose prose-invert prose-xs max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdown}</ReactMarkdown>
        </div>
      )}
    </div>
  );
};
