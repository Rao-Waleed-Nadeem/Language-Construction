import React, { useState } from 'react';
import { Columns, List } from 'lucide-react';

interface DiffViewProps {
  beforeTitle?: string;
  afterTitle?: string;
  beforeLines: string[];
  afterLines: string[];
  className?: string;
}

export const DiffView: React.FC<DiffViewProps> = ({
  beforeTitle = 'Original',
  afterTitle = 'Optimized',
  beforeLines,
  afterLines,
  className = '',
}) => {
  const [mode, setMode] = useState<'split' | 'unified'>('split');

  const maxLines = Math.max(beforeLines.length, afterLines.length);

  return (
    <div className={`flex flex-col bg-bg-1 border border-border rounded-lg overflow-hidden ${className}`}>
      {/* Header bar */}
      <div className="flex items-center justify-between p-2 bg-bg-2 border-b border-border text-xs">
        <div className="flex items-center gap-4">
          <span className="font-semibold text-text-0">Code Diff</span>
          <span className="text-text-1 font-mono">
            {beforeLines.length} lines → {afterLines.length} lines
          </span>
        </div>
        <div className="flex items-center gap-1 border border-border rounded p-0.5 bg-bg-1">
          <button
            onClick={() => setMode('split')}
            className={`flex items-center gap-1 px-2 py-0.5 rounded text-[11px] transition-colors ${
              mode === 'split' ? 'bg-accent/20 text-accent font-medium' : 'text-text-1 hover:text-text-0'
            }`}
          >
            <Columns className="w-3 h-3" />
            Split
          </button>
          <button
            onClick={() => setMode('unified')}
            className={`flex items-center gap-1 px-2 py-0.5 rounded text-[11px] transition-colors ${
              mode === 'unified' ? 'bg-accent/20 text-accent font-medium' : 'text-text-1 hover:text-text-0'
            }`}
          >
            <List className="w-3 h-3" />
            Unified
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-2 font-mono text-xs">
        {mode === 'split' ? (
          <div className="grid grid-cols-2 gap-2 h-full">
            {/* Before column */}
            <div className="flex flex-col border border-border rounded overflow-hidden">
              <div className="p-1.5 bg-bg-2 border-b border-border font-semibold text-text-1 text-[11px]">
                {beforeTitle} ({beforeLines.length})
              </div>
              <div className="p-2 space-y-0.5 overflow-auto">
                {beforeLines.map((line, idx) => {
                  const changed = !afterLines.includes(line);
                  return (
                    <div
                      key={idx}
                      className={`flex gap-3 px-1 py-0.5 rounded ${
                        changed ? 'bg-err/15 text-err border-l-2 border-err' : 'text-text-1'
                      }`}
                    >
                      <span className="w-6 text-right text-text-1/50 select-none">{idx + 1}</span>
                      <span className="flex-1 whitespace-pre">{line}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* After column */}
            <div className="flex flex-col border border-border rounded overflow-hidden">
              <div className="p-1.5 bg-bg-2 border-b border-border font-semibold text-text-1 text-[11px]">
                {afterTitle} ({afterLines.length})
              </div>
              <div className="p-2 space-y-0.5 overflow-auto">
                {afterLines.map((line, idx) => {
                  const changed = !beforeLines.includes(line);
                  return (
                    <div
                      key={idx}
                      className={`flex gap-3 px-1 py-0.5 rounded ${
                        changed ? 'bg-ok/15 text-ok border-l-2 border-ok' : 'text-text-0'
                      }`}
                    >
                      <span className="w-6 text-right text-text-1/50 select-none">{idx + 1}</span>
                      <span className="flex-1 whitespace-pre">{line}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        ) : (
          /* Unified view */
          <div className="space-y-0.5 border border-border rounded p-2">
            {Array.from({ length: maxLines }).map((_, idx) => {
              const bLine = beforeLines[idx];
              const aLine = afterLines[idx];
              if (bLine === aLine) {
                return (
                  <div key={idx} className="flex gap-3 px-1 py-0.5 text-text-1">
                    <span className="w-6 text-right opacity-40">{idx + 1}</span>
                    <span className="w-4 text-center opacity-40"> </span>
                    <span className="whitespace-pre">{bLine}</span>
                  </div>
                );
              }
              return (
                <React.Fragment key={idx}>
                  {bLine !== undefined && (
                    <div className="flex gap-3 px-1 py-0.5 bg-err/15 text-err rounded border-l-2 border-err">
                      <span className="w-6 text-right opacity-60">{idx + 1}</span>
                      <span className="w-4 text-center font-bold">-</span>
                      <span className="whitespace-pre">{bLine}</span>
                    </div>
                  )}
                  {aLine !== undefined && (
                    <div className="flex gap-3 px-1 py-0.5 bg-ok/15 text-ok rounded border-l-2 border-ok">
                      <span className="w-6 text-right opacity-60">{idx + 1}</span>
                      <span className="w-4 text-center font-bold">+</span>
                      <span className="whitespace-pre">{aLine}</span>
                    </div>
                  )}
                </React.Fragment>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
