import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, X, Minus, RefreshCw } from 'lucide-react';
import { useCompileStore } from '../../store/compileStore';

interface PhaseConfig {
  id: string;
  name: string;
  route: string;
  num: string;
  color: string;
}

const PHASES: PhaseConfig[] = [
  { id: 'lexer', name: 'Lexer', route: '/lexer', num: '①', color: 'var(--phase-lexer)' },
  { id: 'parser', name: 'Parser', route: '/parser', num: '②', color: 'var(--phase-parser)' },
  { id: 'semantic', name: 'Semantic', route: '/semantic', num: '③', color: 'var(--phase-semantic)' },
  { id: 'ir', name: 'IR', route: '/ir', num: '④', color: 'var(--phase-ir)' },
  { id: 'optimizer', name: 'Optimizer', route: '/optimizer', num: '⑤', color: 'var(--phase-optimizer)' },
  { id: 'codegen', name: 'CodeGen', route: '/codegen', num: '⑥', color: 'var(--phase-codegen)' },
  { id: 'vm', name: 'VM', route: '/vm', num: '⑦', color: 'var(--phase-vm)' },
];

export const PhaseBar: React.FC = () => {
  const navigate = useNavigate();
  const { compileResult, compiling } = useCompileStore();

  const haltedPhase = compileResult?.halted_at_phase;
  const diagnostics = compileResult?.diagnostics || [];

  return (
    <div className="h-8 bg-bg-1 border-b border-border flex items-center px-3 gap-2 overflow-x-auto select-none text-xs">
      {PHASES.map((phase, idx) => {
        // Determine phase status
        let status: 'idle' | 'running' | 'ok' | 'err' | 'skipped' = 'idle';

        if (compiling) {
          status = 'running';
        } else if (compileResult) {
          const phaseDiags = diagnostics.filter(
            (d) => String(d.phase || '').toLowerCase() === phase.id
          );
          const hasError = phaseDiags.some(
            (d) => String(d.severity || '').toLowerCase() === 'error'
          );

          if (hasError || haltedPhase === phase.id) {
            status = 'err';
          } else if (haltedPhase && PHASES.findIndex((p) => p.id === haltedPhase) < idx) {
            status = 'skipped';
          } else {
            status = 'ok';
          }
        }

        const phaseDiags = diagnostics.filter(
          (d) => String(d.phase || '').toLowerCase() === phase.id
        );
        const errCount = phaseDiags.filter((d) => String(d.severity || '').toLowerCase() === 'error').length;
        const warnCount = phaseDiags.filter((d) => String(d.severity || '').toLowerCase() === 'warning').length;

        return (
          <React.Fragment key={phase.id}>
            <button
              onClick={() => navigate(phase.route)}
              className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-bg-2 border border-border hover:border-text-1 transition-colors group cursor-pointer"
            >
              <span className="font-mono text-text-1 group-hover:text-text-0">{phase.num}</span>
              <span className="font-medium text-text-0" style={{ color: phase.color }}>
                {phase.name}
              </span>

              {/* Status indicator */}
              <span className="ml-0.5">
                {status === 'running' ? (
                  <RefreshCw className="w-3 h-3 text-accent animate-spin" />
                ) : status === 'ok' ? (
                  <Check className="w-3 h-3 text-ok" />
                ) : status === 'err' ? (
                  <X className="w-3 h-3 text-err" />
                ) : status === 'skipped' ? (
                  <Minus className="w-3 h-3 text-text-1/40" />
                ) : (
                  <span className="w-2 h-2 rounded-full border border-text-1/40 inline-block" />
                )}
              </span>

              {/* Badges for errors/warnings */}
              {errCount > 0 && (
                <span className="px-1 rounded bg-err/20 text-err text-[10px] font-bold">
                  {errCount}
                </span>
              )}
              {warnCount > 0 && (
                <span className="px-1 rounded bg-warn/20 text-warn text-[10px] font-bold">
                  {warnCount}
                </span>
              )}
            </button>

            {idx < PHASES.length - 1 && (
              <span className="text-border/60 text-xs">→</span>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};
