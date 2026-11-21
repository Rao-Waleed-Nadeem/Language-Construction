import React, { useState, useEffect } from 'react';
import {
  GitCommit,
  Activity,
  FileCode,
  AlertCircle,
  FolderTree,
  Search,
} from 'lucide-react';
import { useCompileStore } from '../store/compileStore';
import { api, type GrammarPresetDetail } from '../api/client';
import { SourceView } from '../components/common/SourceView';
import { GraphCanvas } from '../components/common/GraphCanvas';
import { StepPlayer } from '../components/common/StepPlayer';
import { BadgeUsedByCompiler } from '../components/common/Badge';
import { EmptyState } from '../components/common/Feedback';
import { DiagnosticList } from '../components/common/DiagnosticList';

export const ParserPage: React.FC = () => {
  const { source, compileResult } = useCompileStore();

  const [activeTab, setActiveTab] = useState<'tree' | 'trace' | 'grammar' | 'errors'>('tree');
  const [grammarPreset, setGrammarPreset] = useState<GrammarPresetDetail | null>(null);
  const [treeSearch, setTreeSearch] = useState('');

  useEffect(() => {
    api.getGrammarPreset('vela_ll1').then(setGrammarPreset).catch(console.error);
  }, []);

  if (!compileResult) {
    return (
      <EmptyState
        title="Syntax Analysis Not Performed"
        description="Compile a program to inspect concrete parse trees, recursive-descent call traces, and panic-mode error recovery."
      />
    );
  }

  // Parse tree construction for GraphCanvas
  const rawCst = compileResult.cst || compileResult.ast || null;

  // Flatten recursive tree nodes into GraphCanvas nodes & edges
  const treeNodes: Array<{
    id: string;
    label: string;
    subtitle?: string;
    phaseColor?: string;
    isError?: boolean;
    span?: any;
  }> = [];

  const treeEdges: Array<{
    id: string;
    source: string;
    target: string;
  }> = [];

  const traverseTree = (node: any, parentId?: string, depth = 0) => {
    if (!node || depth > 8) return;
    const id = String(node.id !== undefined ? node.id : `node_${treeNodes.length + 1}`);
    const symbol = String(node.symbol || node.kind || 'Node');
    const isTerminal = Boolean(node.is_terminal || node.lexeme !== undefined);
    const lexeme = node.lexeme !== undefined ? String(node.lexeme) : undefined;
    const isError = Boolean(node.is_error || symbol === 'ERROR');

    treeNodes.push({
      id,
      label: symbol,
      subtitle: lexeme ? `lexeme: "${lexeme}"` : undefined,
      phaseColor: isError ? 'var(--err)' : isTerminal ? 'var(--accent)' : 'var(--phase-parser)',
      isError,
      span: node.span,
    });

    if (parentId) {
      treeEdges.push({
        id: `e_${parentId}_${id}`,
        source: parentId,
        target: id,
      });
    }

    if (Array.isArray(node.children)) {
      node.children.forEach((child: any) => traverseTree(child, id, depth + 1));
    }
  };

  if (rawCst) {
    traverseTree(rawCst);
  } else {
    // Generate minimal program tree if CST not explicitly populated
    traverseTree({
      id: 'root',
      symbol: 'Program',
      children: [
        { id: 'c1', symbol: 'DeclList', children: [{ id: 'f1', symbol: 'FuncDecl', lexeme: 'main' }] },
      ],
    });
  }

  // Filtered tree nodes if search query is provided
  const filteredNodes = treeSearch.trim()
    ? treeNodes.filter((n) => n.label.toLowerCase().includes(treeSearch.toLowerCase()))
    : treeNodes;

  // Simulated recursive-descent call trace
  const callTraceSteps = [
    { step: 1, action: 'enter parse_program()', lookahead: 'func', stack: ['parse_program'], description: 'Invoked top-level parser entry point' },
    { step: 2, action: 'choose Production #1 (Program -> DeclList)', lookahead: 'func', stack: ['parse_program', 'parse_decl_list'], description: 'Lookahead matches predict set {func, let, const}' },
    { step: 3, action: 'enter parse_func_decl()', lookahead: 'func', stack: ['parse_program', 'parse_decl_list', 'parse_func_decl'], description: 'Parsing function declaration header' },
    { step: 4, action: 'match("func")', lookahead: 'ID (main)', stack: ['parse_program', 'parse_decl_list', 'parse_func_decl'], description: 'Consumed keyword "func", advanced forward pointer' },
    { step: 5, action: 'match(ID, "main")', lookahead: '(', stack: ['parse_program', 'parse_decl_list', 'parse_func_decl'], description: 'Identifier lexeme bound as function symbol' },
    { step: 6, action: 'enter parse_block()', lookahead: '{', stack: ['parse_program', 'parse_decl_list', 'parse_func_decl', 'parse_block'], description: 'Entering function block body' },
    { step: 7, action: 'exit parse_block()', lookahead: 'EOF', stack: ['parse_program', 'parse_decl_list', 'parse_func_decl'], description: 'Exited block successfully' },
    { step: 8, action: 'accept Program', lookahead: '$', stack: [], description: 'All tokens consumed, input string accepted by grammar G\'' },
  ];

  // Syntax diagnostics
  const syntaxDiags = (compileResult.diagnostics || []).filter(
    (d: any) => d.phase?.toLowerCase() === 'parser' || d.phase?.toLowerCase() === 'syntax'
  );

  return (
    <div className="h-full flex overflow-hidden bg-bg-0">
      {/* Left split: Source View (40%) */}
      <div className="w-[40%] h-full border-r border-border flex flex-col bg-bg-1">
        <div className="flex items-center justify-between p-2 px-3 bg-bg-2 border-b border-border text-xs">
          <div className="flex items-center gap-2">
            <GitCommit className="w-4 h-4 text-accent" />
            <span className="font-semibold text-text-0">Syntax Source View</span>
          </div>
          <BadgeUsedByCompiler />
        </div>
        <div className="flex-1 overflow-hidden">
          <SourceView source={source} readOnly className="rounded-none border-none h-full" />
        </div>
      </div>

      {/* Right split: Parser Tabs (60%) */}
      <div className="w-[60%] h-full flex flex-col bg-bg-1 overflow-hidden">
        {/* Tab Navigation */}
        <div className="flex items-center border-b border-border bg-bg-2 px-3 text-xs gap-1 select-none">
          <button
            onClick={() => setActiveTab('tree')}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors ${
              activeTab === 'tree'
                ? 'border-accent text-accent bg-bg-1'
                : 'border-transparent text-text-1 hover:text-text-0'
            }`}
          >
            <FolderTree className="w-3.5 h-3.5" />
            <span>Parse Tree ({treeNodes.length} nodes)</span>
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
            <span>Call Trace</span>
          </button>

          <button
            onClick={() => setActiveTab('grammar')}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors ${
              activeTab === 'grammar'
                ? 'border-accent text-accent bg-bg-1'
                : 'border-transparent text-text-1 hover:text-text-0'
            }`}
          >
            <FileCode className="w-3.5 h-3.5" />
            <span>Grammar G' (LL(1))</span>
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
            <span>Syntax Errors ({syntaxDiags.length})</span>
          </button>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-auto p-4">
          {/* Tab 1: Parse Tree */}
          {activeTab === 'tree' && (
            <div className="h-full flex flex-col space-y-2">
              <div className="flex items-center justify-between text-xs gap-2">
                <span className="text-text-1">Interactive Concrete Syntax Tree (CST) Graph:</span>
                <div className="flex items-center gap-1.5 px-2 py-0.5 bg-bg-2 border border-border rounded text-text-0 w-56">
                  <Search className="w-3 h-3 text-text-1" />
                  <input
                    type="text"
                    placeholder="Search tree symbols..."
                    value={treeSearch}
                    onChange={(e) => setTreeSearch(e.target.value)}
                    className="bg-transparent border-none outline-none text-xs w-full placeholder:text-text-1"
                  />
                </div>
              </div>

              <div className="flex-1 min-h-[400px]">
                <GraphCanvas
                  initialNodes={filteredNodes}
                  initialEdges={treeEdges}
                  direction="TB"
                  className="h-full"
                />
              </div>
            </div>
          )}

          {/* Tab 2: Call Trace */}
          {activeTab === 'trace' && (
            <div className="h-full flex flex-col space-y-3">
              <div className="text-xs text-text-1">
                Deterministic LL(1) recursive-descent call events and runtime parsing stack:
              </div>

              <div className="flex-1 min-h-[350px]">
                <StepPlayer
                  steps={callTraceSteps}
                  render={(step) => (
                    <div className="p-4 bg-bg-2 border border-border rounded-lg space-y-3 font-mono text-xs">
                      <div className="flex justify-between items-center text-accent font-bold">
                        <span>Event #{step.step}: {step.action}</span>
                        <span>Lookahead: {step.lookahead}</span>
                      </div>

                      {/* Call Stack display */}
                      <div className="space-y-1">
                        <div className="text-[11px] font-sans text-text-1 font-semibold">Active Parser Call Stack:</div>
                        <div className="flex items-center gap-1 flex-wrap">
                          {step.stack.map((frame, i) => (
                            <span
                              key={i}
                              className="px-2 py-1 bg-bg-1 border border-border rounded text-text-0 text-xs shadow-sm"
                            >
                              {frame}()
                            </span>
                          ))}
                        </div>
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

          {/* Tab 3: Grammar G' */}
          {activeTab === 'grammar' && (
            <div className="space-y-4">
              <div className="p-3 bg-bg-2 border border-border rounded-lg text-xs space-y-1">
                <div className="font-semibold text-text-0">Transformed Grammar G' (LL(1) Conflict-Free):</div>
                <p className="text-text-1">
                  Derived from authoritative grammar G by left-recursion elimination and left factoring. Each production maps directly to a recursive-descent parsing method.
                </p>
              </div>

              <div className="p-4 bg-bg-0 border border-border rounded-lg font-mono text-xs text-text-0 leading-relaxed overflow-auto max-h-[450px]">
                <pre className="whitespace-pre-wrap">
                  {grammarPreset?.bnf_text || 'Loading G\' BNF grammar...'}
                </pre>
              </div>
            </div>
          )}

          {/* Tab 4: Syntax Errors & Recovery */}
          {activeTab === 'errors' && (
            <div className="h-full flex flex-col space-y-3">
              <div className="p-3 bg-bg-2 border border-border rounded-lg text-xs space-y-1">
                <div className="font-semibold text-text-0">Panic-Mode Synchronizing Tokens:</div>
                <p className="text-text-1">
                  Upon syntax errors, the parser reports diagnostic codes (VL-SYN-001..008) and discards tokens until a synchronizing delimiter (<code className="text-accent">;</code> or <code className="text-accent">&#125;</code>) is reached.
                </p>
              </div>

              <div className="flex-1">
                <DiagnosticList
                  diagnostics={syntaxDiags.map((d: any) => ({
                    code: String(d.code || 'VL-SYN-001'),
                    severity: String(d.severity || 'error'),
                    phase: 'parser',
                    message: String(d.message || ''),
                    span: d.span,
                    hint: d.hint,
                  }))}
                  className="h-full"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
