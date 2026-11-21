import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Play,
  PlayCircle,
  CheckCircle2,
  XCircle,
  RefreshCw,
  ExternalLink,
  ShieldCheck,
  ChevronRight,
  BookOpen,
} from 'lucide-react';
import { api, type ExampleItem, type SelftestResponse } from '../api/client';
import { useCompileStore } from '../store/compileStore';
import { useUIStore } from '../store/uiStore';
import { BadgeUsedByCompiler } from '../components/common/Badge';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { loadExample, run, compileResult } = useCompileStore();
  const { openJsonDrawer } = useUIStore();

  const [examples, setExamples] = useState<ExampleItem[]>([]);
  const [loadingExamples, setLoadingExamples] = useState(true);

  // Self-test state
  const [selftestData, setSelftestData] = useState<SelftestResponse | null>(null);
  const [runningSelftest, setRunningSelftest] = useState(false);

  useEffect(() => {
    api.getExamples()
      .then((data) => {
        setExamples(data);
        setLoadingExamples(false);
      })
      .catch((err) => {
        console.error('Failed to load examples:', err);
        setLoadingExamples(false);
      });
  }, []);

  const handleRunSelfTest = async () => {
    try {
      setRunningSelftest(true);
      const res = await api.selftest();
      setSelftestData(res);
    } catch (err) {
      console.error('Self-test error:', err);
    } finally {
      setRunningSelftest(false);
    }
  };

  const PHASES = [
    { id: 'lexer', name: 'Lexer', route: '/lexer', num: '①', desc: 'DFA Tokenizer & Buffer', color: 'var(--phase-lexer)' },
    { id: 'parser', name: 'Parser', route: '/parser', num: '②', desc: 'LL(1) Recursive Descent', color: 'var(--phase-parser)' },
    { id: 'semantic', name: 'Semantic', route: '/semantic', num: '③', desc: 'Type Checker & Scopes', color: 'var(--phase-semantic)' },
    { id: 'ir', name: 'IR Gen', route: '/ir', num: '④', desc: 'Three-Address Code', color: 'var(--phase-ir)' },
    { id: 'optimizer', name: 'Optimizer', route: '/optimizer', num: '⑤', desc: 'Data-Flow & Loop Opt', color: 'var(--phase-optimizer)' },
    { id: 'codegen', name: 'CodeGen', route: '/codegen', num: '⑥', desc: 'Target ISA & RegAlloc', color: 'var(--phase-codegen)' },
    { id: 'vm', name: 'VM', route: '/vm', num: '⑦', desc: 'Virtual Machine Runtime', color: 'var(--phase-vm)' },
  ];

  const COVERAGE_ITEMS = [
    {
      phase: 'Phase 1 & 2: Lexical Analysis',
      items: ['Specification tables, 26 keywords, operators, delimiters', 'Two-buffer scheme, InputBuffer with refill simulation', 'Explicit DFA state machines with longest-match rule', 'Diagnostics VL-LEX-001..007 with exact source coordinates'],
      route: '/lexer',
    },
    {
      phase: 'Phase 3: Syntax Analysis & Grammar Lab',
      items: ['Authoritative grammar G and LL(1) transformed grammar G\'', 'FIRST and FOLLOW sets with iterative derivation logs', 'Predictive LL(1) table with conflict detection', 'LR family: LR(0), SLR(1), CLR(1), LALR(1) tables and shift-reduce traces', 'Operator precedence relations and dangling-else disambiguation'],
      route: '/grammar-lab',
    },
    {
      phase: 'Phase 4: Semantic Analysis & SDD',
      items: ['Type system with scalar types, arrays, conversions, promotions', 'Hierarchical symbol table with lexical scope tracking and shadowing', 'All-paths return analysis and flow validation', 'Syntax-Directed Definitions: S-attributed and L-attributed evaluation', 'Expression DAG with value numbering and subexpression sharing'],
      route: '/semantic',
    },
    {
      phase: 'Phase 5: Intermediate Code Generation',
      items: ['Three-Address Code quadruples with explicit result, op, args', 'Short-circuit boolean evaluation with conditional jump lowering', 'TAC interpreter serving as an independent behavioral oracle', 'Exact runtime invariants INV-RUN-01..05 checking'],
      route: '/ir',
    },
    {
      phase: 'Phase 6: Code Optimization',
      items: ['Basic block partitioning using Algorithm 8.5 leader rules', 'Control-Flow Graph with dominator tree and natural loops', 'Worklist data-flow framework: reaching defs, liveness, available expressions/copies', 'Fixed-point optimization pipeline: constant folding/propagation, CSE, DCE, LICM'],
      route: '/optimizer',
    },
    {
      phase: 'Phase 7: Target Code Generation & Virtual Machine',
      items: ['Target architecture: 8 registers R0-R7, SP, FP, PC, ZF/SF flags', 'Instruction selection with maximal-munch and cost model', 'Register allocation via Algorithm 8.7 getReg and Ershov DAG ordering', 'Interactive Virtual Machine simulation with step-by-step reversibility'],
      route: '/vm',
    },
  ];

  return (
    <div className="h-full overflow-y-auto p-6 space-y-8 bg-bg-0">
      {/* Hero banner */}
      <div className="bg-bg-1 border border-border rounded-xl p-6 relative overflow-hidden shadow-lg">
        <div className="absolute right-0 top-0 w-96 h-96 bg-accent/5 rounded-full blur-3xl pointer-events-none" />
        <div className="flex items-center justify-between relative z-10 flex-wrap gap-4">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 bg-accent/10 border border-accent/30 rounded text-accent text-xs font-mono font-bold">
                CS 4031 Semester Project
              </span>
              <BadgeUsedByCompiler />
            </div>
            <h1 className="text-2xl font-bold text-text-0 tracking-tight">
              Vela Compiler & Interactive Studio
            </h1>
            <p className="text-sm text-text-1 leading-relaxed">
              An authoritative pedagogical compiler pipeline for the Vela language, featuring an end-to-end
              phase-gated architecture from lexical analysis through syntax parsing, semantic verification,
              three-address code generation, data-flow optimization, target instruction selection, and VM simulation.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/playground')}
              className="flex items-center gap-2 px-4 py-2 bg-accent text-bg-0 font-semibold rounded-lg text-xs hover:bg-accent/90 transition-colors shadow-md"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              Open Playground
            </button>
            <button
              onClick={() => navigate('/reference')}
              className="flex items-center gap-2 px-4 py-2 bg-bg-2 border border-border text-text-0 font-medium rounded-lg text-xs hover:border-text-1 transition-colors"
            >
              <BookOpen className="w-3.5 h-3.5 text-text-1" />
              Language Manual
            </button>
          </div>
        </div>
      </div>

      {/* 3-Column Section: Pipeline, Quickstart, Self-test */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Column 1: Clickable 7-Stage Pipeline Diagram */}
        <div className="bg-bg-1 border border-border rounded-xl p-5 flex flex-col shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold text-text-0 flex items-center gap-2">
              <span>Pipeline Architecture</span>
              <span className="text-[10px] text-text-1 font-mono font-normal">(7 Phases)</span>
            </h2>
            {compileResult && (
              <span className="text-xs font-mono text-ok">
                {(compileResult.timings_ms?.total || 0).toFixed(1)} ms total
              </span>
            )}
          </div>

          <div className="flex-1 flex flex-col gap-2 justify-between">
            {PHASES.map((phase) => {
              const timing = compileResult?.timings_ms?.[phase.id];
              return (
                <div
                  key={phase.id}
                  onClick={() => navigate(phase.route)}
                  className="flex items-center justify-between p-2.5 rounded-lg bg-bg-2/70 border border-border/80 hover:border-accent/60 hover:bg-bg-2 transition-all cursor-pointer group"
                >
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs text-text-1 group-hover:text-text-0">{phase.num}</span>
                    <div>
                      <div className="font-semibold text-xs text-text-0 group-hover:text-accent transition-colors" style={{ color: phase.color }}>
                        {phase.name}
                      </div>
                      <div className="text-[11px] text-text-1">{phase.desc}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {timing !== undefined && (
                      <span className="text-[10px] font-mono text-text-1 bg-bg-1 px-1.5 py-0.5 rounded border border-border">
                        {timing.toFixed(1)} ms
                      </span>
                    )}
                    <ChevronRight className="w-3.5 h-3.5 text-text-1 group-hover:text-accent group-hover:translate-x-0.5 transition-all" />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Column 2: Quick Start Examples */}
        <div className="bg-bg-1 border border-border rounded-xl p-5 flex flex-col shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold text-text-0 flex items-center gap-2">
              <span>Language Examples</span>
              <span className="text-[10px] text-text-1 font-mono font-normal">({examples.length} programs)</span>
            </h2>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2 max-h-[380px] pr-1">
            {loadingExamples ? (
              <div className="p-8 text-center text-xs text-text-1 animate-pulse">
                Loading bundled examples...
              </div>
            ) : (
              examples.map((ex) => (
                <div
                  key={ex.id}
                  className="p-2.5 rounded-lg bg-bg-2/60 border border-border/70 hover:border-border hover:bg-bg-2 transition-colors flex items-center justify-between gap-2"
                >
                  <div className="min-w-0 flex-1">
                    <div className="text-xs font-semibold text-text-0 truncate">{ex.title}</div>
                    <div className="text-[11px] text-text-1 truncate">{ex.description}</div>
                  </div>
                  <div className="flex items-center gap-1.5 flex-shrink-0">
                    <button
                      onClick={async () => {
                        await loadExample(ex.id);
                        navigate('/playground');
                      }}
                      title="Open in Playground"
                      className="px-2 py-1 bg-bg-1 hover:bg-bg-0 text-text-0 border border-border rounded text-[11px] font-medium transition-colors"
                    >
                      Open
                    </button>
                    <button
                      onClick={async () => {
                        await loadExample(ex.id);
                        await run();
                        navigate('/playground');
                      }}
                      title="Compile and Run"
                      className="p-1 bg-accent/15 hover:bg-accent/25 text-accent border border-accent/40 rounded transition-colors"
                    >
                      <Play className="w-3 h-3 fill-current" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Column 3: Self-Test Verification Suite */}
        <div className="bg-bg-1 border border-border rounded-xl p-5 flex flex-col shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold text-text-0 flex items-center gap-2">
              <span>Automated Self-Test</span>
              <ShieldCheck className="w-4 h-4 text-ok" />
            </h2>
            <button
              onClick={handleRunSelfTest}
              disabled={runningSelftest}
              className="flex items-center gap-1.5 px-3 py-1 bg-accent/15 border border-accent/40 hover:bg-accent/25 text-accent rounded text-xs font-medium transition-colors disabled:opacity-50"
            >
              {runningSelftest ? <RefreshCw className="w-3 h-3 animate-spin" /> : <PlayCircle className="w-3 h-3" />}
              <span>{runningSelftest ? 'Testing...' : 'Run Self-Test'}</span>
            </button>
          </div>

          {selftestData ? (
            <div className="flex-1 flex flex-col gap-3">
              {/* Pass rate banner */}
              <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-2">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-text-0">Corpus Pass Rate:</span>
                  <span className={`font-mono font-bold ${selftestData.failed === 0 ? 'text-ok' : 'text-err'}`}>
                    {selftestData.pass_rate.toFixed(1)}% ({selftestData.passed} / {selftestData.total})
                  </span>
                </div>
                {/* Progress bar */}
                <div className="w-full h-2 bg-bg-1 rounded-full overflow-hidden flex border border-border/50">
                  <div
                    className="h-full bg-ok transition-all"
                    style={{ width: `${(selftestData.passed / selftestData.total) * 100}%` }}
                  />
                  {selftestData.failed > 0 && (
                    <div
                      className="h-full bg-err transition-all"
                      style={{ width: `${(selftestData.failed / selftestData.total) * 100}%` }}
                    />
                  )}
                </div>
                <div className="flex justify-between text-[10px] text-text-1">
                  <span>Valid programs + Error detection suites</span>
                  <button
                    onClick={() => openJsonDrawer('Selftest Full Report', selftestData)}
                    className="text-accent hover:underline flex items-center gap-0.5"
                  >
                    View raw JSON
                  </button>
                </div>
              </div>

              {/* Programs list */}
              <div className="flex-1 overflow-y-auto space-y-1 max-h-[240px] pr-1">
                {selftestData.items.map((item, idx) => {
                  const passed = item.passed;
                  return (
                    <div
                      key={idx}
                      onClick={async () => {
                        navigate('/playground');
                      }}
                      className="flex items-center justify-between p-1.5 px-2.5 rounded bg-bg-2/50 border border-border/40 hover:bg-bg-2 text-xs cursor-pointer transition-colors"
                    >
                      <div className="flex items-center gap-2 truncate">
                        {passed ? (
                          <CheckCircle2 className="w-3.5 h-3.5 text-ok flex-shrink-0" />
                        ) : (
                          <XCircle className="w-3.5 h-3.5 text-err flex-shrink-0" />
                        )}
                        <span className="font-mono text-text-0 text-[11px] truncate">{item.name}</span>
                      </div>
                      <span className="font-mono text-[10px] text-text-1 uppercase">{item.category}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center p-6 text-center text-xs text-text-1 bg-bg-2/30 border border-dashed border-border rounded-lg">
              <ShieldCheck className="w-8 h-8 text-accent/60 mb-2" />
              <p className="font-medium text-text-0 mb-1">Selftest Corpus Ready</p>
              <p className="text-[11px] text-text-1 max-w-xs mb-4">
                Execute automated regression test suite covering all 50 valid and invalid test programs across all compiler phases.
              </p>
              <button
                onClick={handleRunSelfTest}
                disabled={runningSelftest}
                className="px-3 py-1.5 bg-accent/15 border border-accent/40 text-accent rounded text-xs font-semibold hover:bg-accent/25 transition-colors"
              >
                Run 50-Program Verification
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Assignment Syllabus Coverage */}
      <div className="bg-bg-1 border border-border rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-text-0">Compiler Course Syllabus Coverage (CS 4031)</h2>
            <p className="text-xs text-text-1">Direct interactive mapping of all lecture topics to verified compiler explorer modules</p>
          </div>
          <span className="px-2.5 py-1 bg-ok/10 text-ok border border-ok/30 rounded text-xs font-medium">
            100% Requirements Satisfied
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {COVERAGE_ITEMS.map((cov, idx) => (
            <div
              key={idx}
              onClick={() => navigate(cov.route)}
              className="p-3.5 bg-bg-2/50 border border-border rounded-lg hover:border-accent/60 hover:bg-bg-2 transition-all cursor-pointer flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-xs text-text-0 group-hover:text-accent transition-colors">
                    {cov.phase}
                  </h3>
                  <ExternalLink className="w-3.5 h-3.5 text-text-1 group-hover:text-accent transition-colors" />
                </div>
                <ul className="space-y-1 text-[11px] text-text-1 list-disc pl-4">
                  {cov.items.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>
              <div className="mt-3 pt-2 border-t border-border/50 text-[10px] text-accent font-medium flex items-center gap-1">
                Explore in Studio →
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
