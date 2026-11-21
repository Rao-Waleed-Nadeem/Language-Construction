import React, { useState } from 'react';
import { X, Copy, Check, Code } from 'lucide-react';
import { useUIStore } from '../../store/uiStore';

export const JsonDrawer: React.FC = () => {
  const { jsonDrawerData, jsonDrawerTitle, closeJsonDrawer } = useUIStore();
  const [copied, setCopied] = useState(false);

  if (!jsonDrawerData) return null;

  const jsonStr = JSON.stringify(jsonDrawerData, null, 2);

  const copyJson = () => {
    navigator.clipboard.writeText(jsonStr);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="w-full max-w-2xl h-full bg-bg-1 border-l border-border flex flex-col shadow-2xl">
        {/* Drawer header */}
        <div className="flex items-center justify-between p-3.5 border-b border-border bg-bg-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-text-0">
            <Code className="w-4 h-4 text-accent" />
            <span>Raw Backend Payload: {jsonDrawerTitle || 'Response Slice'}</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={copyJson}
              className="flex items-center gap-1 px-2.5 py-1 bg-bg-1 hover:bg-bg-0 border border-border rounded text-xs text-text-0 transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-ok" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied' : 'Copy JSON'}</span>
            </button>
            <button
              onClick={closeJsonDrawer}
              className="p-1 rounded hover:bg-bg-0 text-text-1 hover:text-text-0 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Drawer body */}
        <div className="flex-1 p-4 overflow-auto bg-bg-0 font-mono text-xs text-text-0 leading-relaxed selection:bg-accent/30">
          <pre className="whitespace-pre-wrap">{jsonStr}</pre>
        </div>

        {/* Drawer footer */}
        <div className="p-2.5 bg-bg-2 border-t border-border text-[11px] text-text-1 flex justify-between items-center">
          <span>Golden Rule AP-4: 100% computed by backend compilation engine</span>
          <span className="font-mono">{new Blob([jsonStr]).size} bytes</span>
        </div>
      </div>
    </div>
  );
};
