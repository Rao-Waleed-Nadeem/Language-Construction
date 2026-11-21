import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle2, AlertCircle, AlertTriangle, Radio } from 'lucide-react';
import { useCompileStore } from '../../store/compileStore';
import { useUIStore } from '../../store/uiStore';
import { api } from '../../api/client';

export const StatusBar: React.FC = () => {
  const navigate = useNavigate();
  const { compileResult, stale } = useCompileStore();
  const { backendConnected, setBackendConnected, hoverSpan } = useUIStore();

  // Health poll every 10 seconds
  useEffect(() => {
    const check = () => {
      api.checkHealth()
        .then(() => setBackendConnected(true))
        .catch(() => setBackendConnected(false));
    };
    check();
    const interval = setInterval(check, 10000);
    return () => clearInterval(interval);
  }, [setBackendConnected]);

  const totalTimeMs = compileResult?.timings_ms?.total || 0;
  const diagnostics = compileResult?.diagnostics || [];
  const errors = diagnostics.filter((d) => String(d.severity || '').toLowerCase() === 'error').length;
  const warnings = diagnostics.filter((d) => String(d.severity || '').toLowerCase() === 'warning').length;

  return (
    <footer
      aria-live="polite"
      className="h-6 bg-bg-2 border-t border-border flex items-center justify-between px-3 text-[11px] font-mono select-none text-text-1 z-10"
    >
      {/* Left: Compile status & timings */}
      <div className="flex items-center gap-3">
        {compileResult && !stale ? (
          compileResult.success ? (
            <span className="flex items-center gap-1 text-ok">
              <CheckCircle2 className="w-3 h-3" />
              <span>Compiled in {totalTimeMs.toFixed(1)} ms</span>
            </span>
          ) : (
            <span className="flex items-center gap-1 text-err">
              <AlertCircle className="w-3 h-3" />
              <span>Halted at {compileResult.halted_at_phase}</span>
            </span>
          )
        ) : (
          <span>Ready</span>
        )}

        {/* Errors & warnings */}
        <button
          onClick={() => navigate('/playground')}
          className="flex items-center gap-2 hover:text-text-0 transition-colors"
        >
          <span className="flex items-center gap-0.5 text-err">
            <AlertCircle className="w-3 h-3" />
            <span>{errors}</span>
          </span>
          <span className="flex items-center gap-0.5 text-warn">
            <AlertTriangle className="w-3 h-3" />
            <span>{warnings}</span>
          </span>
        </button>
      </div>

      {/* Right: Coordinates & Backend health */}
      <div className="flex items-center gap-4">
        {hoverSpan && (
          <span className="text-text-0">
            Ln {hoverSpan.start_line}, Col {hoverSpan.start_col}
          </span>
        )}

        <div className="flex items-center gap-1.5">
          <Radio
            className={`w-3 h-3 ${backendConnected ? 'text-ok animate-pulse' : 'text-err'}`}
          />
          <span className={backendConnected ? 'text-text-1' : 'text-err font-bold'}>
            {backendConnected ? '127.0.0.1:8000' : 'Disconnected'}
          </span>
        </div>
      </div>
    </footer>
  );
};
