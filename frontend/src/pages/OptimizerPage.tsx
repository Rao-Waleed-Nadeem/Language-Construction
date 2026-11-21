import React, { useState } from 'react';
import {
  Zap,
  CheckCircle2,
  XCircle,
  Layers,
  Info,
} from 'lucide-react';
import { useCompileStore } from '../store/compileStore';
import { useUIStore } from '../store/uiStore';
import { DiffView } from '../components/common/DiffView';
import { DataTable, type Column } from '../components/common/DataTable';
import { BadgeUsedByCompiler } from '../components/common/Badge';
import { EmptyState } from '../components/common/Feedback';

interface ChangeRow {
  index: number;
  pass_name: string;
  function_name: string;
  kind: string;
  description: string;
  original: string;
  replacement: string;
}

const PASS_METADATA: Record<string, { category: 'Local' | 'Global' | 'Loop' | 'Machine'; desc: string }> = {
  'Constant Folding': {
    category: 'Local',
    desc: 'Evaluates compile-time constant arithmetic and boolean expressions',
  },
  'Algebraic Simplification': {
    category: 'Local',
    desc: 'Applies algebraic identities (x + 0 -> x, x * 1 -> x, x * 0 -> 0)',
  },
  'Copy Propagation': {
    category: 'Global',
    desc: 'Replaces uses of copy targets with original variables (x = y)',
  },
  'Common Subexpression Elimination': {
    category: 'Global',
    desc: 'Reuses previously computed expression values across basic blocks',
  },
  'Dead Code Elimination': {
    category: 'Global',
    desc: 'Removes unused variable assignments and unreachable instructions',
  },
  'Loop Invariant Code Motion': {
    category: 'Loop',
    desc: 'Hoists loop-invariant computations out of loop bodies into preheaders',
  },
  'Strength Reduction': {
    category: 'Loop',
    desc: 'Replaces expensive induction operations (e.g. multiplication) with additions',
  },
  'Peephole Optimization': {
    category: 'Machine',
    desc: 'Eliminates redundant target instructions, jumps to next, and load/store sequences',
  },
};

export const OptimizerPage: React.FC = () => {
  const {
    compileResult,
    optimize,
    setOptimize,
    compile,
    verify,
    verifying,
    lastVerifyResult,
  } = useCompileStore();
  const { openJsonDrawer } = useUIStore();

  const [selectedFunc, setSelectedFunc] = useState<string>('main');
  const [selectedPass, setSelectedPass] = useState<string>('all');
  const [activeBottomTab, setActiveBottomTab] = useState<'changes' | 'equivalence'>('changes');

  if (!compileResult) {
    return (
      <EmptyState
        title="Optimization Pipeline Not Run"
        description="Compile a program to inspect optimization passes, intermediate code diffs, reduction metrics, and semantic equivalence."
      />
    );
  }

  const rawTac: any = compileResult.tac || {};
  const rawOptTac: any = compileResult.optimized_tac || {};
  const optPasses: any[] = compileResult.opt_passes || [];

  // Functions in TAC
  const tacFunctions: any[] = rawTac.functions || [];
  const optFunctions: any[] = rawOptTac.functions || [];

  const currentUnoptFunc = tacFunctions.find((f: any) => f.name === selectedFunc) || tacFunctions[0] || {
    name: 'main',
    instructions: [],
  };
  const currentOptFunc = optFunctions.find((f: any) => f.name === selectedFunc) || optFunctions[0] || {
    name: 'main',
    instructions: [],
  };

  // Convert instructions to formatted strings for DiffView
  const unoptLines: string[] = (currentUnoptFunc.instructions || []).map((inst: any) => {
    const lbl = inst.label ? `${inst.label}: ` : '';
    const res = inst.result ? `${inst.result} = ` : '';
    const args = [inst.arg1, inst.arg2].filter(Boolean).join(', ');
    return `${lbl}${res}${inst.opcode}${args ? ` ${args}` : ''}`;
  });

  const optLines: string[] = (currentOptFunc.instructions || []).map((inst: any) => {
    const lbl = inst.label ? `${inst.label}: ` : '';
    const res = inst.result ? `${inst.result} = ` : '';
    const args = [inst.arg1, inst.arg2].filter(Boolean).join(', ');
    return `${lbl}${res}${inst.opcode}${args ? ` ${args}` : ''}`;
  });

  // Collect all changes across passes
  const allChanges: ChangeRow[] = [];
  let changeIdx = 0;
  for (const p of optPasses) {
    const changes: any[] = p.changes || [];
    for (const c of changes) {
      allChanges.push({
        index: ++changeIdx,
        pass_name: p.name,
        function_name: c.function_name || 'main',
        kind: c.kind || 'OPTIMIZATION',
        description: c.description || '',
        original: typeof c.original === 'string' ? c.original : JSON.stringify(c.original || ''),
        replacement: typeof c.replacement === 'string' ? c.replacement : JSON.stringify(c.replacement || ''),
      });
    }
  }

  // Filter changes by selected pass
  const displayedChanges =
    selectedPass === 'all'
      ? allChanges
      : allChanges.filter((c) => c.pass_name.toLowerCase() === selectedPass.toLowerCase());

  // Metrics
  const beforeCount = unoptLines.length;
  const afterCount = optLines.length;
  const delta = beforeCount - afterCount;
  const reductionPct = beforeCount > 0 ? ((delta / beforeCount) * 100).toFixed(1) : '0.0';

  const changeColumns: Column<ChangeRow>[] = [
    { key: 'index', header: '#', width: '50px' },
    {
      key: 'pass_name',
      header: 'Optimization Pass',
      width: '180px',
      render: (r) => <span className="font-bold text-accent">{r.pass_name}</span>,
    },
    {
      key: 'function_name',
      header: 'Function',
      width: '90px',
      render: (r) => <span className="font-mono text-xs text-text-1">{r.function_name}()</span>,
    },
    {
      key: 'description',
      header: 'Description',
      render: (r) => <span className="text-xs text-text-0">{r.description}</span>,
    },
    {
      key: 'original',
      header: 'Original TAC',
      width: '170px',
      render: (r) => (
        <span className="font-mono text-[11px] text-err bg-err/10 px-1 py-0.5 rounded border border-err/20">
          {r.original || '—'}
        </span>
      ),
    },
    {
      key: 'replacement',
      header: 'Replacement TAC',
      width: '170px',
      render: (r) => (
        <span className="font-mono text-[11px] text-ok bg-ok/10 px-1 py-0.5 rounded border border-ok/20">
          {r.replacement || '(deleted)'}
        </span>
      ),
    },
  ];

  return (
    <div className="h-full flex flex-col bg-bg-0 overflow-hidden font-sans">
      {/* Top Bar */}
      <div className="h-9 bg-bg-2 border-b border-border flex items-center justify-between px-3 text-xs select-none">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 font-bold text-text-0">
            <Zap className="w-4 h-4 text-accent" />
            <span>Code Optimization Lab</span>
          </div>

          <span className="text-border">|</span>

          {/* Function Selector */}
          <div className="flex items-center gap-1.5">
            <span className="text-text-1">Function:</span>
            <select
              value={selectedFunc}
              onChange={(e) => setSelectedFunc(e.target.value)}
              className="px-2 py-0.5 bg-bg-1 border border-border text-text-0 rounded outline-none font-mono"
            >
              {tacFunctions.length > 0 ? (
                tacFunctions.map((f: any) => (
                  <option key={f.name} value={f.name}>
                    {f.name}()
                  </option>
                ))
              ) : (
                <option value="main">main()</option>
              )}
            </select>
          </div>

          <span className="text-border">|</span>

          {/* Toggle Optimization Pipeline */}
          <label className="flex items-center gap-1.5 cursor-pointer text-text-0">
            <input
              type="checkbox"
              checked={optimize}
              onChange={async (e) => {
                setOptimize(e.target.checked);
                await compile();
              }}
              className="accent-accent"
            />
            <span className="text-xs">Enable Pipeline (O1)</span>
          </label>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => verify()}
            disabled={verifying}
            className={`flex items-center gap-1 px-2.5 py-1 rounded text-xs font-semibold transition-colors ${
              verifying
                ? 'bg-bg-1 text-text-1 cursor-wait'
                : 'bg-accent/20 hover:bg-accent/30 text-accent border border-accent/40'
            }`}
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>{verifying ? 'Verifying...' : 'Verify Equivalence'}</span>
          </button>

          <BadgeUsedByCompiler />
          <button
            onClick={() =>
              openJsonDrawer('Optimization Results', {
                passes: optPasses,
                optimized_tac: rawOptTac,
              })
            }
            className="text-[11px] text-accent hover:underline"
          >
            Raw JSON
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* LEFT COLUMN: Optimization Passes Checklist */}
        <div className="w-80 border-r border-border bg-bg-1 flex flex-col overflow-hidden">
          <div className="p-2.5 bg-bg-2 border-b border-border flex items-center justify-between text-xs">
            <span className="font-bold text-text-0">Optimization Passes</span>
            <span className="text-text-1 font-mono text-[11px]">{optPasses.length} configured</span>
          </div>

          {/* Summary Metric Card */}
          <div className="p-3 border-b border-border bg-bg-0/60 space-y-2 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-text-1">Instruction Count:</span>
              <span className="font-mono font-bold text-text-0">
                {beforeCount} → {afterCount}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-text-1">Instructions Saved:</span>
              <span className={`font-mono font-bold ${delta > 0 ? 'text-ok' : 'text-text-1'}`}>
                {delta > 0 ? `-${delta} (-${reductionPct}%)` : '0 (0.0%)'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-text-1">Total Transformations:</span>
              <span className="font-mono font-bold text-accent">{allChanges.length}</span>
            </div>
          </div>

          {/* Pass Selector / Filter */}
          <div className="flex-1 overflow-auto p-2 space-y-1.5">
            {/* All Passes cumulative option */}
            <div
              onClick={() => setSelectedPass('all')}
              className={`p-2.5 rounded-lg border text-xs cursor-pointer transition-colors ${
                selectedPass === 'all'
                  ? 'border-accent bg-accent/10 text-accent font-semibold'
                  : 'border-border bg-bg-2 text-text-1 hover:text-text-0 hover:border-accent/40'
              }`}
            >
              <div className="flex justify-between items-center">
                <span>All Passes (Cumulative)</span>
                <span className="px-1.5 py-0.2 rounded text-[10px] bg-bg-1 border border-border text-text-0">
                  {allChanges.length} edits
                </span>
              </div>
              <div className="text-[11px] text-text-1 font-normal pt-1">
                Fixed-point pipeline until convergence
              </div>
            </div>

            {/* Individual Passes */}
            {optPasses.map((p: any) => {
              const meta = PASS_METADATA[p.name] || { category: 'Local', desc: 'Custom optimization' };
              const isSelected = selectedPass.toLowerCase() === p.name.toLowerCase();
              const categoryColor =
                meta.category === 'Local'
                  ? 'bg-blue-900/30 text-blue-400 border-blue-800'
                  : meta.category === 'Global'
                  ? 'bg-purple-900/30 text-purple-400 border-purple-800'
                  : meta.category === 'Loop'
                  ? 'bg-amber-900/30 text-amber-400 border-amber-800'
                  : 'bg-emerald-900/30 text-emerald-400 border-emerald-800';

              return (
                <div
                  key={p.name}
                  onClick={() => setSelectedPass(p.name)}
                  className={`p-2.5 rounded-lg border text-xs cursor-pointer transition-colors ${
                    isSelected
                      ? 'border-accent bg-accent/10 font-semibold text-text-0'
                      : 'border-border bg-bg-2 text-text-1 hover:text-text-0 hover:border-accent/40'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-text-0">{p.name}</span>
                    <span className={`text-[10px] px-1.5 py-0.2 rounded border ${categoryColor}`}>
                      {meta.category}
                    </span>
                  </div>
                  <div className="text-[11px] text-text-1 font-normal pt-1">{meta.desc}</div>
                  <div className="flex justify-between items-center pt-2 text-[11px] text-text-1 border-t border-border/40 mt-1">
                    <span>Changes: <strong className={p.change_count > 0 ? 'text-ok' : 'text-text-1'}>{p.change_count}</strong></span>
                    <span>Inst: {p.before_instruction_count} → {p.after_instruction_count}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* RIGHT COLUMN: Code Diff & Bottom Panels */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Top Half: DiffView */}
          <div className="flex-1 flex flex-col p-3 overflow-hidden border-b border-border">
            {allChanges.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center p-6 bg-bg-1 border border-border rounded-lg text-center space-y-2">
                <Info className="w-8 h-8 text-text-1" />
                <div className="font-bold text-text-0 text-sm">No Optimization Opportunities Found</div>
                <div className="text-xs text-text-1 max-w-md">
                  All {optPasses.length} optimization passes executed, but the input code was already in optimal form.
                  Try writing algebraic identities like <code>x * 1</code> or loops with invariant calculations!
                </div>
              </div>
            ) : (
              <DiffView
                beforeTitle={`Unoptimized TAC (${currentUnoptFunc.name})`}
                afterTitle={`Optimized TAC (${currentOptFunc.name})`}
                beforeLines={unoptLines}
                afterLines={optLines}
                className="h-full"
              />
            )}
          </div>

          {/* Bottom Half: Tabs for Changes vs Equivalence Check */}
          <div className="h-64 flex flex-col bg-bg-1 overflow-hidden">
            {/* Tab Header */}
            <div className="flex items-center justify-between border-b border-border bg-bg-2 px-3 text-xs select-none">
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setActiveBottomTab('changes')}
                  className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors ${
                    activeBottomTab === 'changes'
                      ? 'border-accent text-accent bg-bg-1'
                      : 'border-transparent text-text-1 hover:text-text-0'
                  }`}
                >
                  <Layers className="w-3.5 h-3.5" />
                  <span>Transformations Log ({displayedChanges.length})</span>
                </button>

                <button
                  onClick={() => setActiveBottomTab('equivalence')}
                  className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors ${
                    activeBottomTab === 'equivalence'
                      ? 'border-accent text-accent bg-bg-1'
                      : 'border-transparent text-text-1 hover:text-text-0'
                  }`}
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Semantic Equivalence Proof</span>
                </button>
              </div>

              {activeBottomTab === 'changes' && (
                <span className="text-[11px] text-text-1">
                  Filtering by: <strong className="text-text-0">{selectedPass}</strong>
                </span>
              )}
            </div>

            {/* Tab 1: Changes Log */}
            {activeBottomTab === 'changes' && (
              <div className="flex-1 overflow-auto p-2">
                {displayedChanges.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-xs text-text-1">
                    No change records for the selected pass filter.
                  </div>
                ) : (
                  <DataTable
                    columns={changeColumns}
                    data={displayedChanges}
                    filterPlaceholder="Filter transformations..."
                    className="h-full"
                  />
                )}
              </div>
            )}

            {/* Tab 2: Semantic Equivalence Check */}
            {activeBottomTab === 'equivalence' && (
              <div className="flex-1 overflow-auto p-4 space-y-3 text-xs">
                {lastVerifyResult ? (
                  <div className="space-y-3">
                    <div
                      className={`p-3 rounded-lg border flex items-center justify-between ${
                        lastVerifyResult.match
                          ? 'bg-ok/10 border-ok text-ok'
                          : 'bg-err/10 border-err text-err'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        {lastVerifyResult.match ? (
                          <CheckCircle2 className="w-5 h-5" />
                        ) : (
                          <XCircle className="w-5 h-5" />
                        )}
                        <span className="font-bold">
                          {lastVerifyResult.match
                            ? 'Semantic Equivalence Verified: O0 Oracle, O1 Oracle, and Target VM produce identical output.'
                            : 'Semantic Divergence Detected: Outputs or exit codes differ.'}
                        </span>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-3">
                      {/* Oracle Unoptimized */}
                      <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-1">
                        <div className="font-bold text-text-0">1. Unoptimized TAC Oracle</div>
                        <div className="text-text-1 text-[11px]">
                          Exit code: {String(lastVerifyResult.oracle_unopt.exit_code ?? '0')}
                        </div>
                        <div className="text-text-1 text-[11px]">
                          Instructions: {String(lastVerifyResult.oracle_unopt.instructions ?? '—')}
                        </div>
                        <pre className="p-2 bg-bg-0 border border-border rounded text-[11px] font-mono mt-1 overflow-auto max-h-20">
                          {String(lastVerifyResult.oracle_unopt.stdout || '(no stdout)')}
                        </pre>
                      </div>

                      {/* Oracle Optimized */}
                      <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-1">
                        <div className="font-bold text-text-0">2. Optimized TAC Oracle</div>
                        <div className="text-text-1 text-[11px]">
                          Exit code: {String(lastVerifyResult.oracle_opt.exit_code ?? '0')}
                        </div>
                        <div className="text-text-1 text-[11px]">
                          Instructions: {String(lastVerifyResult.oracle_opt.instructions ?? '—')}
                        </div>
                        <pre className="p-2 bg-bg-0 border border-border rounded text-[11px] font-mono mt-1 overflow-auto max-h-20">
                          {String(lastVerifyResult.oracle_opt.stdout || '(no stdout)')}
                        </pre>
                      </div>

                      {/* Target VM */}
                      <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-1">
                        <div className="font-bold text-text-0">3. Target ISA Virtual Machine</div>
                        <div className="text-text-1 text-[11px]">
                          Exit code: {String(lastVerifyResult.vm?.exit_code ?? '0')}
                        </div>
                        <div className="text-text-1 text-[11px]">
                          Steps: {String(lastVerifyResult.vm?.steps ?? '—')}
                        </div>
                        <pre className="p-2 bg-bg-0 border border-border rounded text-[11px] font-mono mt-1 overflow-auto max-h-20">
                          {String(lastVerifyResult.vm?.stdout || '(no stdout)')}
                        </pre>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-center space-y-2">
                    <CheckCircle2 className="w-8 h-8 text-text-1" />
                    <div className="font-bold text-text-0">Tri-Way Semantic Equivalence Not Verified</div>
                    <p className="text-text-1 max-w-md">
                      Click the "Verify Equivalence" button in the top bar to run the program across the unoptimized TAC
                      oracle, the optimized TAC oracle, and the Target ISA VM to verify identical outputs and exit codes.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
