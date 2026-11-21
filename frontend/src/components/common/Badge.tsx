import React from 'react';
import { Cpu, GraduationCap } from 'lucide-react';

export const BadgeUsedByCompiler: React.FC<{ className?: string }> = ({ className = '' }) => (
  <span
    title="This analysis or artifact is used directly in the active compilation pipeline"
    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-teal-950/60 text-teal-300 border border-teal-700/50 ${className}`}
  >
    <Cpu className="w-3 h-3 text-teal-400" />
    Used by compiler
  </span>
);

export const BadgeEducational: React.FC<{ className?: string; label?: string }> = ({
  className = '',
  label = 'Educational module',
}) => (
  <span
    title="Pedagogical demonstration powered by the Vela analysis engine"
    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-amber-950/60 text-amber-300 border border-amber-700/50 ${className}`}
  >
    <GraduationCap className="w-3 h-3 text-amber-400" />
    {label}
  </span>
);

export const PhaseBadge: React.FC<{ phase: string; status?: 'ok' | 'err' | 'warn' | 'skipped' }> = ({
  phase,
  status = 'ok',
}) => {
  const statusColor =
    status === 'ok'
      ? 'text-ok border-ok/40 bg-ok/10'
      : status === 'err'
      ? 'text-err border-err/40 bg-err/10'
      : status === 'warn'
      ? 'text-warn border-warn/40 bg-warn/10'
      : 'text-text-1 border-border bg-bg-2';

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-medium border ${statusColor}`}>
      {phase}
    </span>
  );
};
