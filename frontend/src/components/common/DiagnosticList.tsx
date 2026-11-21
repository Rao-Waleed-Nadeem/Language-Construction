import React from 'react';
import { AlertCircle, AlertTriangle, Info, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useUIStore, type SourceSpan } from '../../store/uiStore';

export interface DiagnosticItem {
  code: string;
  severity: string; // 'error' | 'warning' | 'info'
  phase: string;
  message: string;
  span?: {
    start_line: number;
    start_col: number;
    end_line: number;
    end_col: number;
  } | null;
  hint?: string | null;
}

interface DiagnosticListProps {
  diagnostics: DiagnosticItem[];
  className?: string;
}

export const DiagnosticList: React.FC<DiagnosticListProps> = ({
  diagnostics,
  className = '',
}) => {
  const navigate = useNavigate();
  const { setHoverSpan, setPinnedSpan } = useUIStore();

  if (diagnostics.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center text-xs text-text-1">
        <span className="text-ok font-medium mb-1">No Problems Detected</span>
        <span>The compiler verified this phase cleanly without diagnostics.</span>
      </div>
    );
  }

  return (
    <div className={`divide-y divide-border/40 font-mono text-xs overflow-auto ${className}`}>
      {diagnostics.map((diag, idx) => {
        const isError = diag.severity.toLowerCase() === 'error';
        const isWarn = diag.severity.toLowerCase() === 'warning';

        const span: SourceSpan | null = diag.span
          ? {
              start_line: diag.span.start_line,
              start_col: diag.span.start_col,
              end_line: diag.span.end_line,
              end_col: diag.span.end_col,
            }
          : null;

        return (
          <div
            key={idx}
            onMouseEnter={() => span && setHoverSpan(span)}
            onMouseLeave={() => span && setHoverSpan(null)}
            onClick={() => {
              if (span) {
                setPinnedSpan(span);
                navigate('/playground');
              }
            }}
            className="p-3 hover:bg-bg-2/60 transition-colors cursor-pointer group"
          >
            <div className="flex items-start gap-2.5">
              {/* Severity icon */}
              <div className="mt-0.5 flex-shrink-0">
                {isError ? (
                  <AlertCircle className="w-4 h-4 text-err" />
                ) : isWarn ? (
                  <AlertTriangle className="w-4 h-4 text-warn" />
                ) : (
                  <Info className="w-4 h-4 text-accent" />
                )}
              </div>

              {/* Body */}
              <div className="flex-1 space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  {/* Code chip */}
                  <span
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/reference?search=${encodeURIComponent(diag.code)}`);
                    }}
                    title="View in error catalogue"
                    className="inline-flex items-center gap-0.5 px-1.5 py-0.2 rounded font-bold text-[11px] bg-bg-2 border border-border text-accent hover:border-accent"
                  >
                    {diag.code}
                    <ExternalLink className="w-2.5 h-2.5 opacity-60" />
                  </span>

                  {/* Phase chip */}
                  <span className="text-[10px] uppercase tracking-wider text-text-1 px-1 rounded bg-bg-0 border border-border">
                    {diag.phase}
                  </span>

                  {/* Coordinates */}
                  {span && (
                    <span className="text-text-1 text-[11px]">
                      Ln {span.start_line}, Col {span.start_col}
                    </span>
                  )}
                </div>

                {/* Message */}
                <div className="text-text-0 font-sans text-xs">{diag.message}</div>

                {/* Hint */}
                {diag.hint && (
                  <div className="text-text-1 font-sans text-[11px] pl-2 border-l border-accent/40 italic">
                    Hint: {diag.hint}
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
