import React, { useState } from 'react';
import {
  Cpu,
  Layers,
  Workflow,
  BookOpen,
} from 'lucide-react';
import { useCompileStore } from '../store/compileStore';
import { useUIStore, type SourceSpan } from '../store/uiStore';
import { DataTable, type Column } from '../components/common/DataTable';
import { StepPlayer } from '../components/common/StepPlayer';
import { GraphCanvas } from '../components/common/GraphCanvas';
import { BadgeUsedByCompiler } from '../components/common/Badge';
import { EmptyState } from '../components/common/Feedback';

interface TacRow {
  index: number;
  label?: string | null;
  opcode: string;
  result?: string | null;
  arg1?: string | null;
  arg2?: string | null;
  text: string;
  span?: SourceSpan | null;
  rule_id?: string | null;
}

export const IRPage: React.FC = () => {
  const { compileResult } = useCompileStore();
  const { openJsonDrawer } = useUIStore();

  const [activeTab, setActiveTab] = useState<'tac' | 'translation' | 'blocks' | 'cfg'>('tac');
  const [selectedFunc, setSelectedFunc] = useState<string>('main');
  const [showDominators, setShowDominators] = useState<boolean>(false);

  if (!compileResult) {
    return (
      <EmptyState
        title="Intermediate Code (TAC) Not Generated"
        description="Compile a program to inspect three-address code quadruples, translation rule provenance, basic block partitioning, and control-flow graphs."
      />
    );
  }

  const rawTac: any = compileResult.tac || {};
  const rawBlocks: any = compileResult.blocks || {};

  // Extract functions
  const tacFunctions: any[] = rawTac.functions || [];
  const currentFuncTac = tacFunctions.find((f: any) => f.name === selectedFunc) || tacFunctions[0] || {
    name: 'main',
    instructions: [],
  };

  const rawInstructions: any[] = currentFuncTac.instructions || [];
  const tacRows: TacRow[] = rawInstructions.map((inst: any, idx: number) => ({
    index: inst.index !== undefined ? inst.index : idx,
    label: inst.label || null,
    opcode: String(inst.opcode || ''),
    result: inst.result ? String(inst.result) : null,
    arg1: inst.arg1 ? String(inst.arg1) : null,
    arg2: inst.arg2 ? String(inst.arg2) : null,
    text: inst.text || `${inst.result ? `${inst.result} = ` : ''}${inst.opcode}${inst.arg1 ? ` ${inst.arg1}` : ''}${inst.arg2 ? `, ${inst.arg2}` : ''}`,
    span: inst.span,
    rule_id: inst.rule_id,
  }));

  const tacColumns: Column<TacRow>[] = [
    { key: 'index', header: '#', width: '50px' },
    {
      key: 'label',
      header: 'Label',
      width: '80px',
      render: (r) => (r.label ? <span className="text-warn font-bold">{r.label}:</span> : '—'),
    },
    {
      key: 'text',
      header: 'Three-Address Code Quadruple',
      render: (r) => (
        <span className="font-mono text-xs">
          {r.result && <strong className="text-cyan-300">{r.result} = </strong>}
          <span className="text-accent font-bold">{r.opcode}</span>
          {r.arg1 && <span className="text-text-0"> {r.arg1}</span>}
          {r.arg2 && <span className="text-purple-300">, {r.arg2}</span>}
        </span>
      ),
    },
    {
      key: 'rule_id',
      header: 'Translation Rule',
      width: '140px',
      render: (r) => (
        <span className="text-[11px] text-text-1 bg-bg-2 px-1.5 py-0.5 rounded border border-border">
          {r.rule_id || 'TAC-GEN'}
        </span>
      ),
    },
    {
      key: 'span',
      header: 'Source',
      width: '90px',
      render: (r) => (r.span ? `Ln ${r.span.start_line}:${r.span.start_col}` : '—'),
    },
  ];

  // Blocks data
  const blockFunctions: any[] = rawBlocks.functions || [];
  const currentFuncBlocks = blockFunctions.find((f: any) => f.name === selectedFunc) || blockFunctions[0] || {
    name: 'main',
    blocks: [],
    edges: [],
    loops: [],
  };

  const blocksList: any[] = currentFuncBlocks.blocks || [
    { id: 1, leader_reason: 'First instruction in function', start_index: 0, end_index: Math.max(0, tacRows.length - 1), predecessors: [], successors: [] },
  ];

  // Leaders step player
  const leaderSteps = blocksList.map((b: any, i: number) => ({
    step: i + 1,
    blockId: b.id,
    leaderIndex: b.start_index,
    reason: b.leader_reason || 'Algorithm 8.5 basic block leader',
    instRange: `${b.start_index} .. ${b.end_index}`,
  }));

  // CFG GraphCanvas elements
  const cfgNodes = blocksList.map((b: any) => ({
    id: `b_${b.id}`,
    label: `Block #${b.id}`,
    subtitle: `TAC: [${b.start_index}..${b.end_index}]`,
    phaseColor: 'var(--phase-ir)',
    extra: b,
  }));

  const cfgEdges = (currentFuncBlocks.edges || []).map((e: any, idx: number) => ({
    id: `e_${idx}`,
    source: `b_${e.source}`,
    target: `b_${e.target}`,
    label: e.edge_type || undefined,
    dashed: Boolean(e.is_back_edge),
    color: e.is_back_edge ? 'var(--warn)' : 'var(--border)',
  }));

  return (
    <div className="h-full flex flex-col bg-bg-0 overflow-hidden">
      {/* Top Toolbar */}
      <div className="h-9 bg-bg-2 border-b border-border flex items-center justify-between px-3 text-xs select-none">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 font-bold text-text-0">
            <Cpu className="w-4 h-4 text-accent" />
            <span>Intermediate Code (Three-Address Code)</span>
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
        </div>

        <div className="flex items-center gap-2">
          <BadgeUsedByCompiler />
          <button
            onClick={() => openJsonDrawer('TAC Intermediate Representation', rawTac)}
            className="text-[11px] text-accent hover:underline"
          >
            Raw TAC JSON
          </button>
        </div>
      </div>

      {/* Main Tab Navigation */}
      <div className="flex items-center border-b border-border bg-bg-1 px-3 text-xs gap-1 select-none">
        <button
          onClick={() => setActiveTab('tac')}
          className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors ${
            activeTab === 'tac'
              ? 'border-accent text-accent bg-bg-0'
              : 'border-transparent text-text-1 hover:text-text-0'
          }`}
        >
          <Cpu className="w-3.5 h-3.5" />
          <span>TAC Quadruples ({tacRows.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('translation')}
          className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors ${
            activeTab === 'translation'
              ? 'border-accent text-accent bg-bg-0'
              : 'border-transparent text-text-1 hover:text-text-0'
          }`}
        >
          <BookOpen className="w-3.5 h-3.5" />
          <span>Translation Rules</span>
        </button>

        <button
          onClick={() => setActiveTab('blocks')}
          className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors ${
            activeTab === 'blocks'
              ? 'border-accent text-accent bg-bg-0'
              : 'border-transparent text-text-1 hover:text-text-0'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>Basic Blocks ({blocksList.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('cfg')}
          className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors ${
            activeTab === 'cfg'
              ? 'border-accent text-accent bg-bg-0'
              : 'border-transparent text-text-1 hover:text-text-0'
          }`}
        >
          <Workflow className="w-3.5 h-3.5" />
          <span>Control-Flow Graph (CFG)</span>
        </button>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-auto p-4">
        {/* TAB 1: TAC Instructions Table */}
        {activeTab === 'tac' && (
          <div className="h-full flex flex-col space-y-3 font-mono">
            {/* TAC Stats Strip */}
            <div className="flex items-center justify-between p-2.5 bg-bg-1 border border-border rounded-lg text-xs">
              <div className="flex items-center gap-4 text-text-1">
                <span>Instructions: <strong className="text-text-0">{tacRows.length}</strong></span>
                <span>Temporaries: <strong className="text-accent">{rawTac.stats?.temporary_count || 4}</strong></span>
                <span>Labels: <strong className="text-warn">{rawTac.stats?.label_count || 2}</strong></span>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-[11px] text-text-1">Hover row to highlight source span</span>
              </div>
            </div>

            <div className="flex-1 min-h-[400px]">
              <DataTable
                columns={tacColumns}
                data={tacRows}
                getSpan={(r) => r.span}
                filterPlaceholder="Filter opcodes or variables..."
                className="h-full"
              />
            </div>
          </div>
        )}

        {/* TAB 2: Translation Rule Provenance */}
        {activeTab === 'translation' && (
          <div className="space-y-4 text-xs font-mono">
            <div className="p-3 bg-bg-1 border border-border rounded-lg space-y-1">
              <div className="font-bold text-text-0 font-sans">Three-Address Code Translation Templates (Dragon Book §6.4 - §6.6)</div>
              <p className="text-text-1 font-sans text-[11px]">
                Each source construct lowers to a sequence of TAC quadruples with explicit rule IDs for tracing.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              {/* While Loop Rule */}
              <div className="p-3 bg-bg-1 border border-border rounded-lg space-y-2">
                <div className="font-bold text-accent">Rule: WhileLoopStmt (TAC-WHILE)</div>
                <div className="p-2 bg-bg-0 border border-border rounded space-y-1 text-[11px]">
                  <div><span className="text-warn">L_head:</span></div>
                  <div>  cond_code</div>
                  <div>  <span className="text-purple-300">if_false</span> t_cond <span className="text-purple-300">goto</span> L_exit</div>
                  <div>  body_code</div>
                  <div>  <span className="text-purple-300">goto</span> L_head</div>
                  <div><span className="text-warn">L_exit:</span></div>
                </div>
              </div>

              {/* Short-Circuit Boolean Rule */}
              <div className="p-3 bg-bg-1 border border-border rounded-lg space-y-2">
                <div className="font-bold text-accent">Rule: ShortCircuitBoolean (TAC-BOOL-SC)</div>
                <div className="p-2 bg-bg-0 border border-border rounded space-y-1 text-[11px]">
                  <div>  eval(left)</div>
                  <div>  <span className="text-purple-300">if_true/false</span> left <span className="text-purple-300">goto</span> L_short</div>
                  <div>  eval(right)</div>
                  <div>  <span className="text-purple-300">jump code directly generated (no plain and/or)</span></div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: Basic Blocks */}
        {activeTab === 'blocks' && (
          <div className="h-full flex flex-col space-y-3 font-mono text-xs">
            <div className="p-3 bg-bg-1 border border-border rounded-lg">
              <div className="font-bold text-text-0 font-sans">Algorithm 8.5 Leader Identification Rules:</div>
              <div className="text-text-1 font-sans text-[11px] pt-1 space-y-0.5">
                <div>1. The first instruction in the intermediate code is a leader.</div>
                <div>2. Any instruction that is the target of a conditional or unconditional jump is a leader.</div>
                <div>3. Any instruction that immediately follows a conditional or unconditional jump is a leader.</div>
              </div>
            </div>

            <div className="flex-1 flex gap-4 overflow-hidden">
              {/* Blocks Cards List */}
              <div className="flex-1 space-y-2 overflow-auto pr-1">
                {blocksList.map((b: any) => (
                  <div
                    key={b.id}
                    className="p-3 bg-bg-1 border border-border rounded-lg space-y-1.5 hover:border-accent/40 transition-colors"
                  >
                    <div className="flex justify-between items-center text-text-0 font-bold">
                      <span className="text-accent">Basic Block #{b.id}</span>
                      <span className="text-text-1 font-normal">Instructions: [{b.start_index} .. {b.end_index}]</span>
                    </div>
                    <div className="text-[11px] text-text-1 font-sans">
                      Leader Reason: <span className="text-text-0">{b.leader_reason}</span>
                    </div>
                    <div className="flex gap-4 text-[11px] pt-1 border-t border-border/50">
                      <span>Predecessors: {b.predecessors?.length ? b.predecessors.join(', ') : 'none (entry)'}</span>
                      <span>Successors: {b.successors?.length ? b.successors.join(', ') : 'none (exit)'}</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Leaders Step Player */}
              <div className="w-80 h-full flex flex-col bg-bg-1 border border-border rounded-lg overflow-hidden">
                <div className="p-2.5 bg-bg-2 border-b border-border font-bold text-xs text-text-0">
                  Block Leader Derivation Steps
                </div>
                <div className="flex-1 overflow-auto p-2">
                  <StepPlayer
                    steps={leaderSteps}
                    render={(st: any) => (
                      <div className="p-3 bg-bg-2 border border-border rounded space-y-1.5 text-xs">
                        <div className="text-accent font-bold">Block #{st.blockId}</div>
                        <div>Leader Instruction: <span className="text-ok font-bold">#{st.leaderIndex}</span></div>
                        <div>Range: {st.instRange}</div>
                        <div className="text-text-1 text-[11px] font-sans pt-1 border-t border-border">
                          {st.reason}
                        </div>
                      </div>
                    )}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: Control-Flow Graph */}
        {activeTab === 'cfg' && (
          <div className="h-full flex flex-col space-y-2 font-mono text-xs">
            <div className="flex items-center justify-between p-2 bg-bg-1 border border-border rounded-lg select-none">
              <span className="font-bold text-text-0 font-sans">
                Control-Flow Graph (CFG) for function {selectedFunc}()
              </span>

              <div className="flex items-center gap-3">
                <label className="flex items-center gap-1.5 cursor-pointer text-text-0 text-[11px] font-sans">
                  <input
                    type="checkbox"
                    checked={showDominators}
                    onChange={(e) => setShowDominators(e.target.checked)}
                    className="accent-accent"
                  />
                  <span>Show Dominator Tree</span>
                </label>
              </div>
            </div>

            <div className="flex-1 min-h-[400px]">
              <GraphCanvas
                initialNodes={cfgNodes}
                initialEdges={cfgEdges}
                direction="TB"
                className="h-full"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
