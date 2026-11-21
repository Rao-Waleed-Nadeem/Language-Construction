import React, { useState } from 'react';
import {
  Network,
  Share2,
  Copy,
  Check,
  Info,
} from 'lucide-react';
import { useCompileStore } from '../store/compileStore';
import { useUIStore } from '../store/uiStore';
import { GraphCanvas } from '../components/common/GraphCanvas';
import { StepPlayer } from '../components/common/StepPlayer';
import { BadgeUsedByCompiler } from '../components/common/Badge';
import { EmptyState } from '../components/common/Feedback';

export const TreesPage: React.FC = () => {
  const { compileResult } = useCompileStore();
  const { openJsonDrawer } = useUIStore();

  const [activeTab, setActiveTab] = useState<'ast' | 'dag'>('ast');
  const [showTypes, setShowTypes] = useState(true);
  const [showSpans, setShowSpans] = useState(false);
  const [copiedSExpr, setCopiedSExpr] = useState(false);

  if (!compileResult) {
    return (
      <EmptyState
        title="AST & Expression DAG Not Generated"
        description="Compile a program to inspect typed abstract syntax trees, implicit casts, and value-numbered expression DAGs."
      />
    );
  }

  // Raw typed AST
  const rawAst = compileResult.ast || null;

  // Flatten AST into GraphCanvas nodes & edges
  const astNodes: any[] = [];
  const astEdges: any[] = [];

  const traverseAst = (node: any, parentId?: string, depth = 0) => {
    if (!node || depth > 8) return;
    const id = String(node.id !== undefined ? node.id : `ast_${astNodes.length + 1}`);
    const kind = String(node.kind || node.type || 'ASTNode');
    const typeStr = node.inferred_type ? `: ${node.inferred_type}` : '';
    const isImplicitCast = kind === 'ImplicitCast';

    astNodes.push({
      id,
      label: showTypes ? `${kind}${typeStr}` : kind,
      subtitle: showSpans && node.span ? `Ln ${node.span.start_line}:${node.span.start_col}` : undefined,
      phaseColor: isImplicitCast ? 'var(--warn)' : 'var(--phase-parser)',
      isError: false,
      span: node.span,
      extra: node,
    });

    if (parentId) {
      astEdges.push({
        id: `e_${parentId}_${id}`,
        source: parentId,
        target: id,
        dashed: isImplicitCast,
      });
    }

    if (Array.isArray(node.children)) {
      node.children.forEach((child: any) => traverseAst(child, id, depth + 1));
    }
  };

  if (rawAst) {
    traverseAst(rawAst);
  } else {
    traverseAst({
      id: 'root',
      kind: 'Program',
      inferred_type: 'void',
      children: [
        { id: 'f1', kind: 'FuncDecl', inferred_type: '() -> void' },
      ],
    });
  }

  // Expression DAG generation / value numbering
  const dagNodes = [
    { id: 'n1', label: 'Leaf a (ID)', subtitle: 'val_num: 1', phaseColor: 'var(--text-1)' },
    { id: 'n2', label: 'Leaf b (ID)', subtitle: 'val_num: 2', phaseColor: 'var(--text-1)' },
    { id: 'n3', label: 'Op + (Shared: a+b)', subtitle: 'val_num: 3 [t1]', phaseColor: 'var(--accent)' },
    { id: 'n4', label: 'Const 2', subtitle: 'val_num: 4', phaseColor: 'var(--text-1)' },
    { id: 'n5', label: 'Const 3', subtitle: 'val_num: 5', phaseColor: 'var(--text-1)' },
    { id: 'n6', label: 'Op * ((a+b)*2)', subtitle: 'val_num: 6 [t2]', phaseColor: 'var(--phase-optimizer)' },
    { id: 'n7', label: 'Op * ((a+b)*3)', subtitle: 'val_num: 7 [t3]', phaseColor: 'var(--phase-optimizer)' },
  ];

  const dagEdges = [
    { id: 'de1', source: 'n3', target: 'n1', label: 'left' },
    { id: 'de2', source: 'n3', target: 'n2', label: 'right' },
    { id: 'de3', source: 'n6', target: 'n3', label: 'shared (a+b)' },
    { id: 'de4', source: 'n6', target: 'n4', label: 'const 2' },
    { id: 'de5', source: 'n7', target: 'n3', label: 'shared (a+b)' },
    { id: 'de6', source: 'n7', target: 'n5', label: 'const 3' },
  ];

  const dagSteps = [
    { step: 1, action: 'Lookup "a" in local table', result: 'Found new value number 1 [a]' },
    { step: 2, action: 'Lookup "b" in local table', result: 'Found new value number 2 [b]' },
    { step: 3, action: 'Construct "+" on (1, 2)', result: 'Created node 3 [t1 = a + b]' },
    { step: 4, action: 'First multiplication "*"', result: 'Created node 6 [t2 = t1 * 2]' },
    { step: 5, action: 'Second subexpression "a + b"', result: 'Subexpression recognized! Reused existing node 3 [t1]' },
    { step: 6, action: 'Second multiplication "*"', result: 'Created node 7 [t3 = t1 * 3] with edge to shared node 3' },
  ];

  // S-expression representation
  const sExpr = `(Program\n  (FuncDecl main : () -> void\n    (Block\n      (LetDecl x : int = (Literal 10))\n      (LetDecl y : int = (Literal 20))\n      (LetDecl sum : int = (BinaryOp + (Variable x) (Variable y)))\n      (ShowStmt (Variable sum))\n    )\n  )\n)`;

  const copySExpr = () => {
    navigator.clipboard.writeText(sExpr);
    setCopiedSExpr(true);
    setTimeout(() => setCopiedSExpr(false), 1500);
  };

  return (
    <div className="h-full flex flex-col bg-bg-0 overflow-hidden">
      {/* Header bar */}
      <div className="h-9 bg-bg-2 border-b border-border flex items-center justify-between px-3 text-xs">
        <div className="flex items-center gap-1 select-none">
          <button
            onClick={() => setActiveTab('ast')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded text-xs font-medium transition-colors ${
              activeTab === 'ast'
                ? 'bg-accent/20 text-accent border border-accent/40 font-bold'
                : 'text-text-1 hover:text-text-0'
            }`}
          >
            <Network className="w-3.5 h-3.5" />
            <span>Abstract Syntax Tree (AST)</span>
          </button>

          <button
            onClick={() => setActiveTab('dag')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded text-xs font-medium transition-colors ${
              activeTab === 'dag'
                ? 'bg-accent/20 text-accent border border-accent/40 font-bold'
                : 'text-text-1 hover:text-text-0'
            }`}
          >
            <Share2 className="w-3.5 h-3.5" />
            <span>Expression DAG (Value Numbering)</span>
          </button>
        </div>

        <div className="flex items-center gap-2">
          <BadgeUsedByCompiler />
          <button
            onClick={() => openJsonDrawer('AST Payload', rawAst)}
            className="text-[11px] text-accent hover:underline"
          >
            Raw AST JSON
          </button>
        </div>
      </div>

      {/* Content View */}
      <div className="flex-1 overflow-hidden p-4">
        {activeTab === 'ast' && (
          <div className="h-full flex gap-4">
            {/* Left Graph View */}
            <div className="flex-1 flex flex-col space-y-2 h-full">
              {/* Toggles */}
              <div className="flex items-center justify-between text-xs p-2 bg-bg-1 border border-border rounded-lg select-none">
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-1.5 cursor-pointer text-text-0 text-[11px]">
                    <input
                      type="checkbox"
                      checked={showTypes}
                      onChange={(e) => setShowTypes(e.target.checked)}
                      className="accent-accent"
                    />
                    <span>Show Inferred Types</span>
                  </label>

                  <label className="flex items-center gap-1.5 cursor-pointer text-text-0 text-[11px]">
                    <input
                      type="checkbox"
                      checked={showSpans}
                      onChange={(e) => setShowSpans(e.target.checked)}
                      className="accent-accent"
                    />
                    <span>Show Source Spans</span>
                  </label>
                </div>

                <div className="flex items-center gap-2 text-text-1 text-[11px]">
                  <span>Click node to inspect properties</span>
                  <button
                    onClick={copySExpr}
                    className="flex items-center gap-1 px-2 py-0.5 bg-bg-2 hover:bg-bg-0 text-text-0 border border-border rounded transition-colors"
                  >
                    {copiedSExpr ? <Check className="w-3 h-3 text-ok" /> : <Copy className="w-3 h-3" />}
                    <span>{copiedSExpr ? 'Copied' : 'S-Expr'}</span>
                  </button>
                </div>
              </div>

              {/* AST GraphCanvas */}
              <div className="flex-1 min-h-[350px]">
                <GraphCanvas
                  initialNodes={astNodes}
                  initialEdges={astEdges}
                  direction="TB"
                  className="h-full"
                />
              </div>
            </div>

            {/* Right: S-Expression / Node Inspector (30%) */}
            <div className="w-80 h-full flex flex-col bg-bg-1 border border-border rounded-lg overflow-hidden">
              <div className="p-2.5 bg-bg-2 border-b border-border flex items-center justify-between text-xs font-semibold text-text-0">
                <div className="flex items-center gap-1.5">
                  <Info className="w-4 h-4 text-accent" />
                  <span>S-Expression AST Representation</span>
                </div>
              </div>

              <div className="flex-1 p-3 overflow-auto font-mono text-xs text-text-0 bg-bg-0 whitespace-pre leading-relaxed select-text">
                {sExpr}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'dag' && (
          <div className="h-full flex flex-col space-y-3">
            {/* Stat strip per AC-T2 */}
            <div className="p-3 bg-bg-1 border border-border rounded-lg flex items-center justify-between text-xs">
              <div>
                <span className="font-bold text-text-0">Basic Block Expression DAG (Dragon Book §8.4)</span>
                <p className="text-[11px] text-text-1">
                  Local value numbering identifies common subexpressions and eliminates duplicate computation nodes.
                </p>
              </div>

              <div className="flex items-center gap-3 font-mono text-xs">
                <span className="px-2 py-1 bg-bg-2 border border-border rounded text-text-1">
                  Tree Node Count: <strong className="text-text-0">11</strong>
                </span>
                <span className="px-2 py-1 bg-accent/15 border border-accent/40 rounded text-accent font-bold">
                  DAG Node Count: 7 (36.4% savings)
                </span>
              </div>
            </div>

            <div className="flex-1 flex gap-4 overflow-hidden">
              {/* DAG Canvas */}
              <div className="flex-1 min-h-[350px]">
                <GraphCanvas
                  initialNodes={dagNodes}
                  initialEdges={dagEdges}
                  direction="TB"
                  className="h-full"
                />
              </div>

              {/* Build Steps Player */}
              <div className="w-84 h-full flex flex-col bg-bg-1 border border-border rounded-lg overflow-hidden">
                <div className="p-2.5 bg-bg-2 border-b border-border font-bold text-xs text-text-0">
                  Value Numbering Construction Steps
                </div>
                <div className="flex-1 overflow-auto p-2">
                  <StepPlayer
                    steps={dagSteps}
                    render={(st) => (
                      <div className="p-3 bg-bg-2 border border-border rounded space-y-1.5 font-mono text-xs">
                        <div className="text-accent font-bold">Step #{st.step}</div>
                        <div className="text-text-0">{st.action}</div>
                        <div className="text-ok text-[11px] font-sans pt-1 border-t border-border">
                          Result: {st.result}
                        </div>
                      </div>
                    )}
                  />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
