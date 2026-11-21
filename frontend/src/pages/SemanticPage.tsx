import React, { useState, useEffect } from 'react';
import {
  CheckCircle2,
  FolderTree,
  ArrowRightLeft,
  GraduationCap,
  Play,
} from 'lucide-react';
import { useCompileStore } from '../store/compileStore';
import { useLabStore } from '../store/labStore';
import { SourceView } from '../components/common/SourceView';
import { DataTable, type Column } from '../components/common/DataTable';
import { StepPlayer } from '../components/common/StepPlayer';
import { BadgeUsedByCompiler, BadgeEducational } from '../components/common/Badge';
import { EmptyState } from '../components/common/Feedback';
import { DiagnosticList } from '../components/common/DiagnosticList';

export const SemanticPage: React.FC = () => {
  const { source, compileResult } = useCompileStore();
  const { sddResult, runSDD, loading: sddLoading } = useLabStore();

  const [activeTab, setActiveTab] = useState<'checks' | 'symbols' | 'conversions' | 'sdd'>('checks');
  const [selectedScopeId, setSelectedScopeId] = useState<number>(1);
  const [sddPreset, setSddPreset] = useState<string>('desk_calculator');
  const [sddInput] = useState<string>('3 + 4 * 5');

  useEffect(() => {
    runSDD('desk_calculator');
  }, [runSDD]);

  if (!compileResult) {
    return (
      <EmptyState
        title="Semantic Analysis Not Performed"
        description="Compile a program to inspect type checking rules, hierarchical scope symbol tables, implicit casts, and SDD/SDT attribute grammar evaluation."
      />
    );
  }

  const rawSemantic: any = compileResult.semantic || {};
  const semanticDiags = (compileResult.diagnostics || []).filter(
    (d: any) => d.phase?.toLowerCase() === 'semantic'
  );

  // Scope tree and symbols
  const rawScopes: any[] = Array.isArray(rawSemantic.scopes)
    ? rawSemantic.scopes
    : [
        { id: 1, name: 'global', parent_id: null, level: 0 },
        { id: 2, name: 'main', parent_id: 1, level: 1 },
      ];

  const rawSymbols: any[] = Array.isArray(rawSemantic.symbols) ? rawSemantic.symbols : [];
  const filteredSymbols = rawSymbols.filter((s: any) => s.scope_id === selectedScopeId);

  const symbolColumns: Column<any>[] = [
    { key: 'name', header: 'Symbol Name', render: (r) => <strong className="text-accent">{r.name}</strong> },
    {
      key: 'kind',
      header: 'Kind',
      render: (r) => (
        <span className="px-1.5 py-0.5 rounded text-[10px] uppercase font-bold bg-bg-2 border border-border text-purple-300">
          {r.kind}
        </span>
      ),
    },
    { key: 'type', header: 'Declared Type', render: (r) => <span className="text-cyan-300 font-bold">{r.type}</span> },
    { key: 'scope_level', header: 'Level', width: '60px' },
    {
      key: 'declared_at',
      header: 'Declared',
      render: (r) => (r.span ? `Ln ${r.span.start_line}, Col ${r.span.start_col}` : '—'),
    },
    { key: 'uses_count', header: 'Uses', width: '50px' },
  ];

  // Scope event log
  const scopeEvents: any[] = Array.isArray(rawSemantic.scope_events)
    ? rawSemantic.scope_events
    : [
        { step: 1, action: 'enter_scope', scope_id: 1, name: 'global', desc: 'Initialized global symbol scope #1' },
        { step: 2, action: 'insert_symbol', symbol: 'main', type: '() -> void', desc: 'Registered function main in global scope' },
        { step: 3, action: 'enter_scope', scope_id: 2, name: 'main', desc: 'Entered function main lexical scope #2' },
        { step: 4, action: 'exit_scope', scope_id: 2, name: 'main', desc: 'Exited scope #2, checked for unused variables' },
      ];

  // Implicit and explicit conversions
  const conversions: any[] = Array.isArray(rawSemantic.conversions) ? rawSemantic.conversions : [];
  const operatorResolutions: any[] = Array.isArray(rawSemantic.operator_resolutions) ? rawSemantic.operator_resolutions : [];

  return (
    <div className="h-full flex overflow-hidden bg-bg-0">
      {/* Left Column: Source View (38%) */}
      <div className="w-[38%] h-full border-r border-border flex flex-col bg-bg-1">
        <div className="flex items-center justify-between p-2 px-3 bg-bg-2 border-b border-border text-xs">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-accent" />
            <span className="font-semibold text-text-0">Semantic Source View</span>
          </div>
          <BadgeUsedByCompiler />
        </div>
        <div className="flex-1 overflow-hidden">
          <SourceView source={source} readOnly className="rounded-none border-none h-full" />
        </div>
      </div>

      {/* Right Column: Semantic Analysis Tabs (62%) */}
      <div className="w-[62%] h-full flex flex-col bg-bg-1 overflow-hidden">
        {/* Tab Navigation */}
        <div className="flex items-center border-b border-border bg-bg-2 px-3 text-xs gap-1 select-none overflow-x-auto">
          <button
            onClick={() => setActiveTab('checks')}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors whitespace-nowrap ${
              activeTab === 'checks'
                ? 'border-accent text-accent bg-bg-1'
                : 'border-transparent text-text-1 hover:text-text-0'
            }`}
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Type Checks & Rules</span>
          </button>

          <button
            onClick={() => setActiveTab('symbols')}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors whitespace-nowrap ${
              activeTab === 'symbols'
                ? 'border-accent text-accent bg-bg-1'
                : 'border-transparent text-text-1 hover:text-text-0'
            }`}
          >
            <FolderTree className="w-3.5 h-3.5" />
            <span>Symbol Tables & Scopes</span>
          </button>

          <button
            onClick={() => setActiveTab('conversions')}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors whitespace-nowrap ${
              activeTab === 'conversions'
                ? 'border-accent text-accent bg-bg-1'
                : 'border-transparent text-text-1 hover:text-text-0'
            }`}
          >
            <ArrowRightLeft className="w-3.5 h-3.5" />
            <span>Casts & Overloading</span>
          </button>

          <button
            onClick={() => setActiveTab('sdd')}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors whitespace-nowrap ${
              activeTab === 'sdd'
                ? 'border-accent text-accent bg-bg-1'
                : 'border-transparent text-text-1 hover:text-text-0'
            }`}
          >
            <GraduationCap className="w-3.5 h-3.5" />
            <span>SDD / SDT Evaluator</span>
          </button>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-auto p-4">
          {/* TAB 1: Type Checks & Rules */}
          {activeTab === 'checks' && (
            <div className="space-y-4 text-xs font-mono">
              <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-1">
                <div className="font-bold text-text-0">Semantic Invariants (INV-SEM-01..19) Verification</div>
                <p className="text-text-1 font-sans text-[11px]">
                  Verifies declarations before use, assignment compatibility, operator operand types, return coverage, and array bounds.
                </p>
              </div>

              {/* Semantic Diagnostics List */}
              <div className="space-y-2">
                <div className="font-bold text-text-0 font-sans text-xs">
                  Semantic Diagnostics ({semanticDiags.length} detected)
                </div>
                <DiagnosticList
                  diagnostics={semanticDiags.map((d: any) => ({
                    code: String(d.code || 'VL-SEM-001'),
                    severity: String(d.severity || 'error'),
                    phase: 'semantic',
                    message: String(d.message || ''),
                    span: d.span,
                    hint: d.hint,
                  }))}
                />
              </div>
            </div>
          )}

          {/* TAB 2: Symbol Tables & Scopes */}
          {activeTab === 'symbols' && (
            <div className="space-y-4 text-xs font-mono">
              {/* Scope selector */}
              <div className="flex items-center gap-2 p-2.5 bg-bg-2 border border-border rounded-lg">
                <span className="font-bold text-text-0 font-sans">Active Scope:</span>
                <div className="flex items-center gap-1.5">
                  {rawScopes.map((sc: any) => (
                    <button
                      key={sc.id}
                      onClick={() => setSelectedScopeId(sc.id)}
                      className={`px-2.5 py-1 rounded text-xs transition-colors ${
                        selectedScopeId === sc.id
                          ? 'bg-accent/20 text-accent font-bold border border-accent/40'
                          : 'bg-bg-1 border border-border text-text-1 hover:text-text-0'
                      }`}
                    >
                      Scope #{sc.id} ({sc.name}, Level {sc.level})
                    </button>
                  ))}
                </div>
              </div>

              {/* Symbol Table */}
              <div className="h-64">
                <DataTable
                  columns={symbolColumns}
                  data={filteredSymbols}
                  getSpan={(r) => r.span}
                  filterPlaceholder="Search symbols in current scope..."
                  className="h-full"
                />
              </div>

              {/* Scope Event Log Step Player */}
              <div className="space-y-2">
                <div className="font-bold text-text-0 font-sans text-xs">
                  Scope Management Event Log (Dragon Book §7.6)
                </div>
                <StepPlayer
                  steps={scopeEvents}
                  render={(ev: any) => (
                    <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-1 text-xs">
                      <div className="flex justify-between items-center text-accent font-bold">
                        <span>Event #{ev.step}: {ev.action}</span>
                        {ev.scope_id && <span>Scope #{ev.scope_id}</span>}
                      </div>
                      <div className="text-text-0 pt-1">{ev.desc}</div>
                    </div>
                  )}
                />
              </div>
            </div>
          )}

          {/* TAB 3: Conversions & Overloading */}
          {activeTab === 'conversions' && (
            <div className="space-y-4 text-xs font-mono">
              <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-1">
                <div className="font-bold text-text-0">Type Promotion & Operator Overloading</div>
                <p className="text-text-1 font-sans text-[11px]">
                  Automatic widening (e.g. <code className="text-accent">int → float</code>) and operator polymorphism (e.g. <code className="text-accent">+</code> as int add, float add, or string concat).
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Implicit / Explicit Casts */}
                <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-2">
                  <div className="font-bold text-accent">Type Casts Inserted</div>
                  <div className="space-y-1 max-h-48 overflow-auto">
                    {conversions.length > 0 ? (
                      conversions.map((c: any, i: number) => (
                        <div key={i} className="p-1.5 bg-bg-1 border border-border/50 rounded flex justify-between">
                          <span className="font-bold text-purple-300">{c.kind}</span>
                          <span className="text-text-0">{c.from_type} → {c.to_type}</span>
                          <span className="text-text-1 text-[10px]">Ln {c.line}</span>
                        </div>
                      ))
                    ) : (
                      <div className="p-4 text-center text-text-1 italic font-sans text-[11px]">
                        No implicit or explicit casts in this program.
                      </div>
                    )}
                  </div>
                </div>

                {/* Operator Resolution Table */}
                <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-2">
                  <div className="font-bold text-ok">Operator + Resolutions</div>
                  <div className="space-y-1 max-h-48 overflow-auto">
                    {operatorResolutions.length > 0 ? (
                      operatorResolutions.map((r: any, i: number) => (
                        <div key={i} className="p-1.5 bg-bg-1 border border-border/50 rounded flex justify-between">
                          <span className="font-bold text-text-0">{r.left} + {r.right}</span>
                          <span className="text-ok font-bold">→ {r.resolved_operation}</span>
                        </div>
                      ))
                    ) : (
                      <div className="p-4 text-center text-text-1 italic font-sans text-[11px]">
                        Standard operator dispatch applied.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: SDD / SDT Evaluator */}
          {activeTab === 'sdd' && (
            <div className="space-y-4 text-xs font-mono">
              <div className="p-3 bg-bg-2 border border-border rounded-lg flex items-center justify-between flex-wrap gap-2">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-text-0 text-sm">Syntax-Directed Definition (SDD) Engine</span>
                    <BadgeEducational />
                  </div>
                  <div className="text-[11px] text-text-1 font-sans">
                    Dragon Book §5.1 - §5.3: Evaluates synthesized and inherited attributes and classifies S-attributed vs L-attributed grammars.
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <select
                    value={sddPreset}
                    onChange={(e) => {
                      setSddPreset(e.target.value);
                      runSDD(e.target.value, sddInput);
                    }}
                    className="bg-bg-1 border border-border text-text-0 px-2 py-1 rounded text-xs outline-none"
                  >
                    <option value="desk_calculator">Desk Calculator (S-attributed)</option>
                    <option value="type_declarations">Type Declarations (L-attributed)</option>
                    <option value="boolean_labels">Boolean Expression Labels</option>
                  </select>

                  <button
                    onClick={() => runSDD(sddPreset, sddInput)}
                    disabled={sddLoading}
                    className="flex items-center gap-1 px-3 py-1 bg-accent/15 border border-accent/40 text-accent rounded font-medium hover:bg-accent/25 transition-colors text-xs"
                  >
                    <Play className="w-3 h-3 fill-current" />
                    Evaluate
                  </button>
                </div>
              </div>

              {sddResult ? (
                <div className="space-y-4">
                  {/* Classification Badges */}
                  <div className="p-3 bg-bg-2 border border-border rounded-lg flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span
                        className={`px-2.5 py-1 rounded font-bold text-xs ${
                          sddResult.classification.is_s_attributed
                            ? 'bg-ok/15 text-ok border border-ok/30'
                            : 'bg-err/15 text-err border border-err/30'
                        }`}
                      >
                        S-Attributed: {sddResult.classification.is_s_attributed ? 'YES ✓' : 'NO ✕'}
                      </span>

                      <span
                        className={`px-2.5 py-1 rounded font-bold text-xs ${
                          sddResult.classification.is_l_attributed
                            ? 'bg-ok/15 text-ok border border-ok/30'
                            : 'bg-err/15 text-err border border-err/30'
                        }`}
                      >
                        L-Attributed: {sddResult.classification.is_l_attributed ? 'YES ✓' : 'NO ✕'}
                      </span>
                    </div>

                    <span className="text-text-1 font-sans text-[11px]">
                      Evaluation Order: {sddResult.evaluation_order.join(' → ')}
                    </span>
                  </div>

                  {/* Annotated Parse Tree & Attributes */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-2">
                      <div className="font-bold text-text-0">Annotated Parse Tree (with evaluated attributes)</div>
                      <pre className="p-3 bg-bg-0 border border-border rounded text-xs text-accent max-h-56 overflow-auto whitespace-pre-wrap">
                        {JSON.stringify(sddResult.annotated_tree, null, 2)}
                      </pre>
                    </div>

                    <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-2">
                      <div className="font-bold text-text-0">Attribute Dependency Graph</div>
                      <pre className="p-3 bg-bg-0 border border-border rounded text-xs text-text-0 max-h-56 overflow-auto whitespace-pre-wrap">
                        {JSON.stringify(sddResult.dependency_graph, null, 2)}
                      </pre>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-8 text-center text-text-1 animate-pulse">Evaluating SDD attribute grammar...</div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
