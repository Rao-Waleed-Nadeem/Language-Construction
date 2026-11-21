import React, { useState, useEffect } from 'react';
import {
  Binary,
  Layers,
  Activity,
  Workflow,
  AlertCircle,
  FileCode,
} from 'lucide-react';
import { useCompileStore } from '../store/compileStore';
import { useUIStore, type SourceSpan } from '../store/uiStore';
import { api, type LanguageResponse } from '../api/client';
import { SourceView } from '../components/common/SourceView';
import { DataTable, type Column } from '../components/common/DataTable';
import { StepPlayer } from '../components/common/StepPlayer';
import { GraphCanvas } from '../components/common/GraphCanvas';
import { BadgeUsedByCompiler } from '../components/common/Badge';
import { EmptyState } from '../components/common/Feedback';
import { DiagnosticList } from '../components/common/DiagnosticList';

interface TokenRow {
  index: number;
  category: string;
  type: string;
  lexeme: string;
  value: string;
  lineCol: string;
  length: number;
  span: SourceSpan;
}

export const LexerPage: React.FC = () => {
  const { source, compileResult } = useCompileStore();
  const { openJsonDrawer } = useUIStore();

  const [activeTab, setActiveTab] = useState<'tokens' | 'spec' | 'dfa' | 'trace' | 'buffer' | 'errors'>('tokens');
  const [selectedTokenIdx, setSelectedTokenIdx] = useState<number>(0);
  const [bufferSize, setBufferSize] = useState<number>(64);
  const [languageSpec, setLanguageSpec] = useState<LanguageResponse | null>(null);

  useEffect(() => {
    api.getLanguage().then(setLanguageSpec).catch(console.error);
  }, []);

  if (!compileResult) {
    return (
      <EmptyState
        title="Lexical Analysis Not Performed"
        description="Compile a program to inspect token streams, DFA state transitions, and two-buffer scanner refill simulation."
      />
    );
  }

  // Tokens table data
  const rawTokens = compileResult.tokens || [];
  const tokensData: TokenRow[] = rawTokens.map((t: any, idx: number) => {
    const span: SourceSpan = {
      start_line: t.span?.start_line || 1,
      start_col: t.span?.start_col || 1,
      end_line: t.span?.end_line || 1,
      end_col: t.span?.end_col || 1,
    };
    return {
      index: t.index !== undefined ? t.index : idx,
      category: String(t.category || (t.type?.startsWith('KEYWORD') ? 'KEYWORD' : 'TOKEN')),
      type: String(t.type || ''),
      lexeme: String(t.lexeme || ''),
      value: t.value !== undefined && t.value !== null ? JSON.stringify(t.value) : '—',
      lineCol: `${span.start_line}:${span.start_col}`,
      length: String(t.lexeme || '').length,
      span,
    };
  });

  const selectedToken = tokensData[selectedTokenIdx] || tokensData[0];

  // Token categories breakdown
  const categoryCounts: Record<string, number> = {};
  tokensData.forEach((t) => {
    categoryCounts[t.category] = (categoryCounts[t.category] || 0) + 1;
  });

  const tokenColumns: Column<TokenRow>[] = [
    { key: 'index', header: '#', width: '50px' },
    {
      key: 'category',
      header: 'Category',
      width: '110px',
      render: (r) => (
        <span
          className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
            r.category === 'KEYWORD'
              ? 'bg-purple-950/60 text-purple-300 border border-purple-700/50'
              : r.category === 'IDENTIFIER'
              ? 'bg-blue-950/60 text-blue-300 border border-blue-700/50'
              : r.category === 'NUMBER' || r.category === 'LITERAL'
              ? 'bg-orange-950/60 text-orange-300 border border-orange-700/50'
              : r.category === 'OPERATOR'
              ? 'bg-cyan-950/60 text-cyan-300 border border-cyan-700/50'
              : 'bg-bg-2 text-text-1 border border-border'
          }`}
        >
          {r.category}
        </span>
      ),
    },
    { key: 'type', header: 'Token Type', width: '130px' },
    {
      key: 'lexeme',
      header: 'Lexeme',
      render: (r) => <code className="text-accent font-bold">{r.lexeme}</code>,
    },
    { key: 'value', header: 'Value' },
    { key: 'lineCol', header: 'Line:Col', width: '80px' },
    { key: 'length', header: 'Len', width: '50px' },
  ];

  // DFA visualization nodes & edges for Identifier/Keyword or Operator
  const dfaNodes = [
    { id: 'start', label: 'State 0 (Start)', subtitle: 'Looking for letter/_', phaseColor: 'var(--text-1)' },
    { id: 'id_body', label: 'State 1 (ID / Keyword)', subtitle: 'Accumulating letter/digit/_', phaseColor: 'var(--phase-lexer)' },
    { id: 'accept_id', label: 'State 2 (Accept ID)', subtitle: 'Identifier match', phaseColor: 'var(--ok)' },
    { id: 'lookup_kw', label: 'State 3 (Keyword Check)', subtitle: 'Table lookup (show vs shown)', phaseColor: 'var(--warn)' },
  ];

  const dfaEdges = [
    { id: 'e1', source: 'start', target: 'id_body', label: '[a-zA-Z_]' },
    { id: 'e2', source: 'id_body', target: 'id_body', label: '[a-zA-Z0-9_]', dashed: true },
    { id: 'e3', source: 'id_body', target: 'lookup_kw', label: 'delimiter / other' },
    { id: 'e4', source: 'lookup_kw', target: 'accept_id', label: 'not in keyword table' },
  ];

  // Scan character trace for the selected token
  const tokenChars = (selectedToken?.lexeme || '').split('');
  const charTraceSteps = tokenChars.map((ch, idx) => ({
    step: idx + 1,
    char: ch,
    accumulated: tokenChars.slice(0, idx + 1).join(''),
    state: idx === 0 ? 'State 0 → 1' : 'State 1 → 1',
    description: `Consumed character '${ch}', transitioned state`,
  }));

  // Two-buffer simulation steps
  const totalChars = source.length;
  const buffer1 = source.slice(0, bufferSize);
  const buffer2 = source.slice(bufferSize, bufferSize * 2);
  const refillsCount = Math.max(1, Math.ceil(totalChars / bufferSize));

  const bufferTraceSteps = Array.from({ length: refillsCount }).map((_, i) => ({
    event: `Refill Event #${i + 1}`,
    activeBuffer: i % 2 === 0 ? 'Buffer 1' : 'Buffer 2',
    range: `${i * bufferSize} .. ${Math.min((i + 1) * bufferSize, totalChars)}`,
    sentinel: 'EOF (\\0) placed at buffer boundary',
    lexemeBegin: (i * bufferSize) % (bufferSize * 2),
    forward: Math.min((i + 1) * bufferSize, totalChars) % (bufferSize * 2),
  }));

  // Lexer diagnostics
  const lexerDiags = (compileResult.diagnostics || []).filter(
    (d: any) => d.phase?.toLowerCase() === 'lexer'
  );

  return (
    <div className="h-full flex flex-col bg-bg-0 overflow-hidden">
      {/* Top split: Source View (38%) */}
      <div className="h-[38%] border-b border-border flex flex-col bg-bg-1">
        <div className="flex items-center justify-between p-2 px-3 bg-bg-2 border-b border-border text-xs">
          <div className="flex items-center gap-2">
            <Binary className="w-4 h-4 text-accent" />
            <span className="font-semibold text-text-0">Lexical Source View</span>
            <span className="text-text-1 font-mono">({tokensData.length} tokens generated)</span>
          </div>
          <div className="flex items-center gap-2">
            <BadgeUsedByCompiler />
            <button
              onClick={() => openJsonDrawer('Tokens Payload', rawTokens)}
              className="text-[11px] text-accent hover:underline"
            >
              Raw Tokens JSON
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-hidden">
          <SourceView source={source} readOnly className="rounded-none border-none h-full" />
        </div>
      </div>

      {/* Bottom split: Lexer Analysis Tabs (62%) */}
      <div className="flex-1 flex flex-col bg-bg-1 overflow-hidden">
        {/* Tab navigation */}
        <div className="flex items-center border-b border-border bg-bg-2 px-3 text-xs gap-1 select-none">
          <button
            onClick={() => setActiveTab('tokens')}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors ${
              activeTab === 'tokens'
                ? 'border-accent text-accent bg-bg-1'
                : 'border-transparent text-text-1 hover:text-text-0'
            }`}
          >
            <Binary className="w-3.5 h-3.5" />
            <span>Tokens ({tokensData.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('spec')}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors ${
              activeTab === 'spec'
                ? 'border-accent text-accent bg-bg-1'
                : 'border-transparent text-text-1 hover:text-text-0'
            }`}
          >
            <FileCode className="w-3.5 h-3.5" />
            <span>Token Specification</span>
          </button>

          <button
            onClick={() => setActiveTab('dfa')}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors ${
              activeTab === 'dfa'
                ? 'border-accent text-accent bg-bg-1'
                : 'border-transparent text-text-1 hover:text-text-0'
            }`}
          >
            <Workflow className="w-3.5 h-3.5" />
            <span>DFA State Machine</span>
          </button>

          <button
            onClick={() => setActiveTab('trace')}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors ${
              activeTab === 'trace'
                ? 'border-accent text-accent bg-bg-1'
                : 'border-transparent text-text-1 hover:text-text-0'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Char Scan Trace</span>
          </button>

          <button
            onClick={() => setActiveTab('buffer')}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors ${
              activeTab === 'buffer'
                ? 'border-accent text-accent bg-bg-1'
                : 'border-transparent text-text-1 hover:text-text-0'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Two-Buffer Scheme</span>
          </button>

          <button
            onClick={() => setActiveTab('errors')}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors ${
              activeTab === 'errors'
                ? 'border-accent text-accent bg-bg-1'
                : 'border-transparent text-text-1 hover:text-text-0'
            }`}
          >
            <AlertCircle className="w-3.5 h-3.5" />
            <span>Lexical Diagnostics ({lexerDiags.length})</span>
          </button>
        </div>

        {/* Tab content area */}
        <div className="flex-1 overflow-auto p-4">
          {/* Tab 1: Tokens Table */}
          {activeTab === 'tokens' && (
            <div className="h-full flex flex-col space-y-3">
              {/* Category stats chips */}
              <div className="flex items-center gap-2 flex-wrap text-xs select-none">
                {Object.entries(categoryCounts).map(([cat, count]) => (
                  <div
                    key={cat}
                    className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-bg-2 border border-border text-text-1 font-mono text-[11px]"
                  >
                    <span>{cat}:</span>
                    <span className="font-bold text-text-0">{count}</span>
                  </div>
                ))}
              </div>

              <div className="flex-1 min-h-[300px]">
                <DataTable
                  columns={tokenColumns}
                  data={tokensData}
                  getSpan={(r) => r.span}
                  filterPlaceholder="Search lexemes or categories..."
                  className="h-full"
                />
              </div>
            </div>
          )}

          {/* Tab 2: Token Specification */}
          {activeTab === 'spec' && (
            <div className="space-y-4">
              <div className="p-3 bg-bg-2 border border-border rounded-lg text-xs space-y-1">
                <div className="font-semibold text-text-0">Dragon Book §3.3 Token Recognition Rules:</div>
                <p className="text-text-1">
                  1. Longest match (Maximal Munch): Always take the longest sequence accepted by a token DFA.
                </p>
                <p className="text-text-1">
                  2. Rule Priority: If an identifier DFA matches a lexeme, lookup the 26 reserved keywords (e.g.{' '}
                  <code className="text-accent">show</code> is KEYWORD, while <code className="text-accent">shown</code> is IDENTIFIER).
                </p>
              </div>

              {languageSpec ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                  {/* Keywords table */}
                  <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-2">
                    <div className="font-bold text-text-0 text-sm">Reserved Keywords ({languageSpec.keywords.length})</div>
                    <div className="flex flex-wrap gap-1.5">
                      {languageSpec.keywords.map((kw) => (
                        <span key={kw} className="px-1.5 py-0.5 rounded bg-bg-1 border border-border text-purple-300">
                          {kw}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Types */}
                  <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-2">
                    <div className="font-bold text-text-0 text-sm">Primitive & Array Types ({languageSpec.types.length})</div>
                    <div className="flex flex-wrap gap-1.5">
                      {languageSpec.types.map((tp) => (
                        <span key={tp} className="px-1.5 py-0.5 rounded bg-bg-1 border border-border text-blue-300">
                          {tp}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Operators */}
                  <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-2 md:col-span-2">
                    <div className="font-bold text-text-0 text-sm">Operators & Delimiters</div>
                    <div className="flex flex-wrap gap-1.5">
                      {languageSpec.operators.map((op) => (
                        <span key={op} className="px-2 py-0.5 rounded bg-bg-1 border border-border text-cyan-300">
                          {op}
                        </span>
                      ))}
                      {languageSpec.delimiters.map((del) => (
                        <span key={del} className="px-2 py-0.5 rounded bg-bg-1 border border-border text-text-1">
                          {del}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-8 text-center text-xs text-text-1 animate-pulse">Loading language specification...</div>
              )}
            </div>
          )}

          {/* Tab 3: DFA State Machine */}
          {activeTab === 'dfa' && (
            <div className="h-full flex flex-col space-y-2">
              <div className="text-xs text-text-1 flex items-center justify-between">
                <span>Deterministic Finite Automaton for Token Recognition (Dragon Book §3.6)</span>
                <span className="font-mono text-accent">Active Token: {selectedToken?.lexeme || '—'}</span>
              </div>
              <div className="flex-1 min-h-[350px]">
                <GraphCanvas
                  initialNodes={dfaNodes}
                  initialEdges={dfaEdges}
                  direction="LR"
                  className="h-full"
                />
              </div>
            </div>
          )}

          {/* Tab 4: Character Scan Trace */}
          {activeTab === 'trace' && (
            <div className="h-full flex flex-col space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-text-1">Select token in Tokens tab to inspect character-by-character scan steps:</span>
                <select
                  value={selectedTokenIdx}
                  onChange={(e) => setSelectedTokenIdx(Number(e.target.value))}
                  className="px-2 py-1 bg-bg-2 border border-border text-text-0 rounded font-mono text-xs outline-none"
                >
                  {tokensData.slice(0, 100).map((t, idx) => (
                    <option key={idx} value={idx}>
                      #{t.index}: {t.category} ({t.lexeme})
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex-1 min-h-[300px]">
                <StepPlayer
                  steps={charTraceSteps}
                  render={(step) => (
                    <div className="p-4 bg-bg-2 border border-border rounded-lg space-y-2 font-mono text-xs">
                      <div className="flex justify-between items-center text-accent font-bold">
                        <span>Step #{step.step}</span>
                        <span>{step.state}</span>
                      </div>
                      <div>
                        Input Character: <span className="px-1.5 py-0.5 bg-bg-0 border border-border rounded text-ok font-bold">{step.char}</span>
                      </div>
                      <div>
                        Accumulated Lexeme: <span className="text-text-0 font-bold">{step.accumulated}</span>
                      </div>
                      <div className="text-text-1 text-[11px] font-sans pt-2 border-t border-border">
                        {step.description}
                      </div>
                    </div>
                  )}
                />
              </div>
            </div>
          )}

          {/* Tab 5: Two-Buffer Scheme */}
          {activeTab === 'buffer' && (
            <div className="space-y-4 text-xs font-mono">
              <div className="p-3 bg-bg-2 border border-border rounded-lg flex items-center justify-between">
                <div>
                  <div className="font-bold text-text-0">Two-Buffer Input Scheme (Dragon Book §3.2)</div>
                  <div className="text-text-1 font-sans text-[11px]">
                    Two N-character buffers reloaded alternately; boundary sentinels eliminate end-of-buffer checks on each character.
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-text-1 text-[11px]">Buffer Size N:</span>
                  <input
                    type="number"
                    min={16}
                    max={256}
                    step={16}
                    value={bufferSize}
                    onChange={(e) => setBufferSize(Number(e.target.value))}
                    className="w-16 px-2 py-1 bg-bg-1 border border-border text-text-0 rounded text-center outline-none"
                  />
                  <span className="text-text-1 text-[11px]">chars</span>
                </div>
              </div>

              {/* Buffer diagram */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-1">
                  <div className="font-bold text-accent text-xs">Buffer 1 (Size: {bufferSize})</div>
                  <div className="p-2 bg-bg-0 border border-border rounded text-[11px] whitespace-pre-wrap truncate">
                    {buffer1 || '(empty)'}
                  </div>
                  <div className="text-[10px] text-text-1">Sentinel EOF appended at offset {bufferSize}</div>
                </div>

                <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-1">
                  <div className="font-bold text-accent text-xs">Buffer 2 (Size: {bufferSize})</div>
                  <div className="p-2 bg-bg-0 border border-border rounded text-[11px] whitespace-pre-wrap truncate">
                    {buffer2 || '(empty)'}
                  </div>
                  <div className="text-[10px] text-text-1">Sentinel EOF appended at offset {bufferSize * 2}</div>
                </div>
              </div>

              {/* Refills Table */}
              <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-2">
                <div className="font-bold text-text-0 text-xs">
                  Buffer Refill Simulation Log ({refillsCount} refills across {totalChars} characters)
                </div>
                <div className="space-y-1">
                  {bufferTraceSteps.map((b, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between p-1.5 px-2.5 bg-bg-1 border border-border/50 rounded text-[11px]"
                    >
                      <span className="font-bold text-text-0">{b.event}</span>
                      <span className="text-accent">{b.activeBuffer}</span>
                      <span className="text-text-1">Source offsets: {b.range}</span>
                      <span className="text-ok text-[10px]">{b.sentinel}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Tab 6: Lexical Diagnostics */}
          {activeTab === 'errors' && (
            <div className="h-full flex flex-col">
              <DiagnosticList
                diagnostics={lexerDiags.map((d: any) => ({
                  code: String(d.code || 'VL-LEX-001'),
                  severity: String(d.severity || 'error'),
                  phase: 'lexer',
                  message: String(d.message || ''),
                  span: d.span,
                  hint: d.hint,
                }))}
                className="h-full"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
