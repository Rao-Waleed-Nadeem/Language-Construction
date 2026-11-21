import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, FileCode, Compass, X } from 'lucide-react';
import { useUIStore } from '../../store/uiStore';
import { useCompileStore } from '../../store/compileStore';

const ROUTES = [
  { path: '/', label: 'Dashboard', desc: 'Overview, status, quickstart & self-test' },
  { path: '/playground', label: 'Playground', desc: 'Monaco code editor, console & problems' },
  { path: '/lexer', label: 'Lexer Explorer', desc: 'Tokens, regexes, DFAs & input buffering' },
  { path: '/parser', label: 'Parser Explorer', desc: 'LL(1) recursive descent parse tree & trace' },
  { path: '/grammar-lab', label: 'Grammar Lab', desc: 'FIRST/FOLLOW, LL(1), LR family & dangling else' },
  { path: '/semantic', label: 'Semantic Analysis', desc: 'Type checks, symbol tables, scopes & SDD' },
  { path: '/trees', label: 'AST & DAG Visualizer', desc: 'Typed AST, expression DAGs & value numbering' },
  { path: '/ir', label: 'Intermediate Code', desc: 'Three-Address Code, basic blocks & CFG' },
  { path: '/optimizer', label: 'Code Optimization Lab', desc: 'Optimization passes, diffs & equivalence' },
  { path: '/codegen', label: 'Target CodeGen', desc: 'Instruction selection, costs & register allocation' },
  { path: '/vm', label: 'Virtual Machine', desc: 'Interactive VM step simulator & memory viewer' },
  { path: '/reference', label: 'Documentation & Reference', desc: 'Language manual, error catalogue & viva docs' },
];

const EXAMPLES = [
  { id: '01_hello_types', label: '01 Hello Types', desc: 'Base types, expressions, arithmetic' },
  { id: '02_control_flow', label: '02 Control Flow', desc: 'If/else, ternary, switch-case' },
  { id: '03_arrays', label: '03 Arrays', desc: 'Array declaration, indexing, iteration' },
  { id: '04_loops', label: '04 Loops', desc: 'While, for loops, break, continue' },
  { id: '05_functions', label: '05 Functions', desc: 'Recursion, mutual recursion, calls' },
  { id: '06_short_circuit', label: '06 Short Circuit', desc: 'Boolean short-circuit evaluation' },
  { id: '07_io_interactive', label: '07 IO Interactive', desc: 'Read and show statements' },
  { id: '08_optimizer_showcase', label: '08 Optimizer Showcase', desc: 'CSE, constant folding, dead code' },
  { id: '09_strings_and_casts', label: '09 Strings & Casts', desc: 'Type casts, ord/chr, string concat' },
  { id: '10_scopes', label: '10 Scopes', desc: 'Block scopes, shadowing, global vars' },
];

export const CommandPalette: React.FC = () => {
  const { commandPaletteOpen, setCommandPaletteOpen } = useUIStore();
  const { loadExample } = useCompileStore();
  const navigate = useNavigate();

  const [query, setQuery] = useState('');

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setCommandPaletteOpen(!commandPaletteOpen);
      } else if (e.key === 'Escape' && commandPaletteOpen) {
        setCommandPaletteOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [commandPaletteOpen, setCommandPaletteOpen]);

  if (!commandPaletteOpen) return null;

  const q = query.toLowerCase();
  const filteredRoutes = ROUTES.filter(
    (r) => r.label.toLowerCase().includes(q) || r.desc.toLowerCase().includes(q)
  );
  const filteredExamples = EXAMPLES.filter(
    (ex) => ex.label.toLowerCase().includes(q) || ex.desc.toLowerCase().includes(q)
  );

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 bg-black/60 backdrop-blur-sm animate-in fade-in duration-100">
      <div className="w-full max-w-xl bg-bg-1 border border-border rounded-xl shadow-2xl overflow-hidden flex flex-col">
        {/* Search header */}
        <div className="flex items-center gap-2 px-3 py-2.5 border-b border-border bg-bg-2">
          <Search className="w-4 h-4 text-text-1" />
          <input
            type="text"
            autoFocus
            placeholder="Type a page name or example program..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 bg-transparent border-none outline-none text-xs text-text-0 placeholder:text-text-1"
          />
          <button
            onClick={() => setCommandPaletteOpen(false)}
            className="p-1 rounded hover:bg-bg-0 text-text-1 hover:text-text-0"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Results */}
        <div className="max-h-96 overflow-auto p-2 space-y-3 text-xs">
          {/* Navigation group */}
          <div>
            <div className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-text-1">
              Navigate to Page
            </div>
            <div className="space-y-0.5">
              {filteredRoutes.map((r) => (
                <div
                  key={r.path}
                  onClick={() => {
                    navigate(r.path);
                    setCommandPaletteOpen(false);
                  }}
                  className="flex items-center gap-3 px-2 py-1.5 rounded-lg hover:bg-bg-2 text-text-0 hover:text-accent cursor-pointer transition-colors"
                >
                  <Compass className="w-4 h-4 text-text-1 flex-shrink-0" />
                  <div className="flex-1">
                    <div className="font-medium">{r.label}</div>
                    <div className="text-[11px] text-text-1">{r.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Examples group */}
          <div>
            <div className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-text-1">
              Load Language Example
            </div>
            <div className="space-y-0.5">
              {filteredExamples.map((ex) => (
                <div
                  key={ex.id}
                  onClick={async () => {
                    await loadExample(ex.id);
                    navigate('/playground');
                    setCommandPaletteOpen(false);
                  }}
                  className="flex items-center gap-3 px-2 py-1.5 rounded-lg hover:bg-bg-2 text-text-0 hover:text-accent cursor-pointer transition-colors"
                >
                  <FileCode className="w-4 h-4 text-text-1 flex-shrink-0" />
                  <div className="flex-1">
                    <div className="font-medium">{ex.label}</div>
                    <div className="text-[11px] text-text-1">{ex.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-2 border-t border-border bg-bg-2 text-[10px] text-text-1 flex justify-between">
          <span>Tip: Press ESC to close or Ctrl+K anytime</span>
          <span>Vela Studio Navigation</span>
        </div>
      </div>
    </div>
  );
};
