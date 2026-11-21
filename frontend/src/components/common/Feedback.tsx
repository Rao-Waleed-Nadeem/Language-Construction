import React from 'react';
import { AlertCircle, RefreshCw, Terminal } from 'lucide-react';
import { useCompileStore } from '../../store/compileStore';

export const EmptyState: React.FC<{
  title?: string;
  description?: string;
  showCompileButton?: boolean;
}> = ({
  title = 'No Data Available',
  description = 'Compile the current program or load an example to view compiler phase output.',
  showCompileButton = true,
}) => {
  const { compile, compiling } = useCompileStore();

  return (
    <div className="flex flex-col items-center justify-center h-full p-8 text-center bg-bg-1 border border-border rounded-lg m-4">
      <div className="p-4 rounded-full bg-bg-2 border border-border mb-4 text-accent">
        <Terminal className="w-8 h-8" />
      </div>
      <h3 className="text-lg font-semibold text-text-0 mb-1">{title}</h3>
      <p className="text-sm text-text-1 max-w-md mb-6">{description}</p>
      {showCompileButton && (
        <button
          onClick={() => compile()}
          disabled={compiling}
          className="flex items-center gap-2 px-4 py-2 bg-accent/10 border border-accent/40 hover:bg-accent/20 text-accent font-medium rounded text-sm transition-colors disabled:opacity-50"
        >
          {compiling && <RefreshCw className="w-4 h-4 animate-spin" />}
          Compile current program
        </button>
      )}
    </div>
  );
};

export const ErrorPanel: React.FC<{
  title?: string;
  message: string;
  onRetry?: () => void;
}> = ({ title = 'Execution Error', message, onRetry }) => {
  return (
    <div className="p-4 bg-err/10 border border-err/30 rounded-lg text-left m-4">
      <div className="flex items-center gap-2 text-err font-medium mb-1">
        <AlertCircle className="w-5 h-5 flex-shrink-0" />
        <span>{title}</span>
      </div>
      <p className="text-sm text-text-0 font-mono whitespace-pre-wrap pl-7">{message}</p>
      {onRetry && (
        <div className="mt-3 pl-7">
          <button
            onClick={onRetry}
            className="px-3 py-1 bg-err/20 hover:bg-err/30 text-err border border-err/40 rounded text-xs font-medium"
          >
            Retry
          </button>
        </div>
      )}
    </div>
  );
};

export const Skeleton: React.FC<{
  rows?: number;
  className?: string;
}> = ({ rows = 4, className = '' }) => {
  return (
    <div className={`p-4 space-y-3 animate-pulse ${className}`}>
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="h-4 bg-bg-2 rounded"
          style={{ width: `${Math.max(40, 100 - i * 15)}%` }}
        />
      ))}
    </div>
  );
};
