import React, { useState, useEffect } from 'react';
import {
  FlaskConical,
  Play,
  ArrowRight,
  Layers,
  Sparkles,
  GitBranch,
  Split,
  FileCode2,
  Workflow,
} from 'lucide-react';
import { useLabStore } from '../store/labStore';
import { useUIStore } from '../store/uiStore';
import { BadgeEducational } from '../components/common/Badge';
import { StepPlayer } from '../components/common/StepPlayer';

export const GrammarLabPage: React.FC = () => {
  const {
    grammarText,
    startSymbol,
    currentPresetId,
    presets,
    analyzeResult,
    transformResult,
    ll1Result,
    lrResult,
    opResult,
    rdResult,
    loading,
    error,
    setGrammarText,
    setStartSymbol,
    loadPresets,
    selectPreset,
    runAnalyze,
    runTransform,
    runLL1,
    runLR,
    runOpPrecedence,
    runRDPseudocode,
  } = useLabStore();

  const { openJsonDrawer } = useUIStore();

  const [activeTab, setActiveTab] = useState<'analysis' | 'transform' | 'll1' | 'lr' | 'op' | 'dangling'>('analysis');
  const [lrVariant, setLrVariant] = useState<string>('slr1');
  const [testInput, setTestInput] = useState<string>('id + id * id');

  useEffect(() => {
    loadPresets();
    runAnalyze();
  }, [loadPresets, runAnalyze]);

  const handleUseTransformed = () => {
    if (transformResult?.transformed_bnf) {
      setGrammarText(transformResult.transformed_bnf);
      runAnalyze();
      setActiveTab('analysis');
    }
  };

  return (
    <div className="h-full flex overflow-hidden bg-bg-0">
      {/* Left Column: Grammar Editor (38%) */}
      <div className="w-[38%] h-full border-r border-border flex flex-col bg-bg-1">
        {/* Editor Toolbar */}
        <div className="p-2.5 bg-bg-2 border-b border-border flex items-center justify-between text-xs gap-2">
          <div className="flex items-center gap-2 flex-1">
            <FlaskConical className="w-4 h-4 text-accent flex-shrink-0" />
            <select
              value={currentPresetId}
              onChange={(e) => selectPreset(e.target.value)}
              className="bg-bg-1 border border-border text-text-0 px-2 py-0.5 rounded text-xs outline-none w-44 truncate"
            >
              <option value="vela">Vela Authoritative G</option>
              <option value="vela_ll1">Vela Transformed G'</option>
              {presets.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-[11px] text-text-1">Start:</span>
            <input
              type="text"
              value={startSymbol}
              onChange={(e) => setStartSymbol(e.target.value)}
              className="w-12 px-1.5 py-0.5 bg-bg-1 border border-border text-text-0 rounded text-center font-mono text-xs outline-none"
            />
            <button
              onClick={() => runAnalyze()}
              disabled={loading}
              className="flex items-center gap-1 px-2.5 py-1 bg-accent/15 border border-accent/40 text-accent rounded font-medium text-xs hover:bg-accent/25 transition-colors disabled:opacity-50"
            >
              <Play className="w-3 h-3 fill-current" />
              Analyze
            </button>
          </div>
        </div>

        {/* Monospace BNF Grammar Editor */}
        <div className="flex-1 p-3 flex flex-col overflow-hidden">
          <div className="text-[11px] text-text-1 mb-1 flex justify-between">
            <span>BNF Grammar Rules (Use <code className="text-accent">-&gt;</code>, <code className="text-accent">|</code>, <code className="text-accent">ε</code>):</span>
            <BadgeEducational />
          </div>
          <textarea
            value={grammarText}
            onChange={(e) => setGrammarText(e.target.value)}
            placeholder="E -> E + T | T&#10;T -> T * F | F&#10;F -> ( E ) | id"
            className="flex-1 p-3 bg-bg-0 border border-border rounded-lg font-mono text-xs text-text-0 outline-none resize-none leading-relaxed focus:border-accent selection:bg-accent/30"
          />
          {error && (
            <div className="mt-2 p-2 bg-err/10 border border-err/30 rounded text-err text-xs font-mono">
              {error}
            </div>
          )}
        </div>
      </div>

      {/* Right Column: Interactive Parsing Theory Tabs (62%) */}
      <div className="w-[62%] h-full flex flex-col bg-bg-1 overflow-hidden">
        {/* Tab Navigation */}
        <div className="flex items-center border-b border-border bg-bg-2 px-3 text-xs gap-1 select-none overflow-x-auto">
          <button
            onClick={() => {
              setActiveTab('analysis');
              runAnalyze();
            }}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors whitespace-nowrap ${
              activeTab === 'analysis'
                ? 'border-accent text-accent bg-bg-1'
                : 'border-transparent text-text-1 hover:text-text-0'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Analysis (FIRST/FOLLOW)</span>
          </button>

          <button
            onClick={() => setActiveTab('transform')}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors whitespace-nowrap ${
              activeTab === 'transform'
                ? 'border-accent text-accent bg-bg-1'
                : 'border-transparent text-text-1 hover:text-text-0'
            }`}
          >
            <GitBranch className="w-3.5 h-3.5" />
            <span>Transform (Left Recursion)</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('ll1');
              runLL1(testInput);
            }}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors whitespace-nowrap ${
              activeTab === 'll1'
                ? 'border-accent text-accent bg-bg-1'
                : 'border-transparent text-text-1 hover:text-text-0'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>LL(1) Table & Parse</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('lr');
              runLR(lrVariant, testInput);
            }}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors whitespace-nowrap ${
              activeTab === 'lr'
                ? 'border-accent text-accent bg-bg-1'
                : 'border-transparent text-text-1 hover:text-text-0'
            }`}
          >
            <Workflow className="w-3.5 h-3.5" />
            <span>LR Family (SLR/CLR/LALR)</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('op');
              runOpPrecedence(testInput);
            }}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors whitespace-nowrap ${
              activeTab === 'op'
                ? 'border-accent text-accent bg-bg-1'
                : 'border-transparent text-text-1 hover:text-text-0'
            }`}
          >
            <Split className="w-3.5 h-3.5" />
            <span>Operator Precedence</span>
          </button>

          <button
            onClick={() => setActiveTab('dangling')}
            className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors whitespace-nowrap ${
              activeTab === 'dangling'
                ? 'border-accent text-accent bg-bg-1'
                : 'border-transparent text-text-1 hover:text-text-0'
            }`}
          >
            <FileCode2 className="w-3.5 h-3.5" />
            <span>Dangling Else</span>
          </button>
        </div>

        {/* Tab Content Area */}
        <div className="flex-1 overflow-auto p-4">
          {/* TAB 1: Analysis (FIRST/FOLLOW Explorer) */}
          {activeTab === 'analysis' && (
            <div className="space-y-4 text-xs font-mono">
              {analyzeResult ? (
                <>
                  {/* Chomsky Classification Banner */}
                  <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-text-0 text-sm">
                        Chomsky Classification: {String(analyzeResult.classification.chomsky_type || '')}
                      </span>
                      <button
                        onClick={() => openJsonDrawer('Grammar Analysis', analyzeResult)}
                        className="text-accent hover:underline text-[11px]"
                      >
                        View Raw JSON
                      </button>
                    </div>
                    <p className="text-text-1 font-sans text-[11px]">
                      {String(analyzeResult.classification.reason || '')}
                    </p>
                    <div className="flex items-center gap-2 pt-1 font-sans">
                      <span className="text-[11px] text-text-1">Nullable symbols:</span>
                      {analyzeResult.nullable.length > 0 ? (
                        analyzeResult.nullable.map((sym) => (
                          <span key={sym} className="px-1.5 py-0.5 rounded bg-bg-1 border border-border text-accent font-mono">
                            {sym}
                          </span>
                        ))
                      ) : (
                        <span className="text-text-1 italic text-[11px]">None</span>
                      )}
                    </div>
                  </div>

                  {/* FIRST & FOLLOW Sets Tables */}
                  <div className="grid grid-cols-2 gap-4">
                    {/* FIRST Sets */}
                    <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-2">
                      <div className="font-bold text-text-0">FIRST Sets (Dragon Book §4.4)</div>
                      <div className="space-y-1 max-h-[220px] overflow-auto">
                        {Object.entries(analyzeResult.first).map(([nt, syms]) => (
                          <div key={nt} className="flex items-center justify-between p-1.5 bg-bg-1 border border-border/50 rounded">
                            <span className="font-bold text-accent">FIRST({nt})</span>
                            <span className="text-text-0">{`{ ${syms.join(', ')} }`}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* FOLLOW Sets */}
                    <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-2">
                      <div className="font-bold text-text-0">FOLLOW Sets (Dragon Book §4.4)</div>
                      <div className="space-y-1 max-h-[220px] overflow-auto">
                        {Object.entries(analyzeResult.follow).map(([nt, syms]) => (
                          <div key={nt} className="flex items-center justify-between p-1.5 bg-bg-1 border border-border/50 rounded">
                            <span className="font-bold text-accent">FOLLOW({nt})</span>
                            <span className="text-text-0">{`{ ${syms.join(', ')} }`}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Derivation Steps Player */}
                  {analyzeResult.steps && analyzeResult.steps.length > 0 && (
                    <div className="space-y-2">
                      <div className="font-bold text-text-0 font-sans text-xs">
                        Fixed-Point Set Derivation Steps ({analyzeResult.steps.length} iterations)
                      </div>
                      <StepPlayer
                        steps={analyzeResult.steps}
                        render={(step: any) => {
                          const setType = String(step.set_type || '').toUpperCase();
                          const addedStr = Array.isArray(step.added) ? step.added.join(', ') : String(step.added || '');
                          const reasonStr = String(step.reason || '');
                          return (
                            <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-1 text-xs">
                              <div className="flex justify-between items-center text-accent font-bold">
                                <span>Iteration #{step.iteration}: Computing {setType}({String(step.symbol)})</span>
                                <span className="text-ok">Added: {`{ ${addedStr} }`}</span>
                              </div>
                              <div className="text-text-1 font-sans text-[11px] pt-1">
                                Rule: {reasonStr}
                              </div>
                            </div>
                          );
                        }}
                      />
                    </div>
                  )}
                </>
              ) : (
                <div className="p-8 text-center text-text-1 animate-pulse">Running grammar analysis...</div>
              )}
            </div>
          )}

          {/* TAB 2: Transform (Left-Recursion Elimination & Left Factoring) */}
          {activeTab === 'transform' && (
            <div className="space-y-4 text-xs font-mono">
              <div className="p-3 bg-bg-2 border border-border rounded-lg flex items-center justify-between flex-wrap gap-2">
                <div className="space-y-0.5">
                  <div className="font-bold text-text-0">Grammar Transformations (Dragon Book §4.3)</div>
                  <div className="text-[11px] text-text-1 font-sans">
                    Transform arbitrary context-free grammars into predictive LL(1) forms.
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => runTransform('left_recursion')}
                    className="px-2.5 py-1 bg-accent/15 border border-accent/40 text-accent rounded font-medium hover:bg-accent/25 transition-colors"
                  >
                    Eliminate Left Recursion
                  </button>
                  <button
                    onClick={() => runTransform('left_factoring')}
                    className="px-2.5 py-1 bg-purple-950/60 border border-purple-700/50 text-purple-300 rounded font-medium hover:bg-purple-900/40 transition-colors"
                  >
                    Left Factor
                  </button>
                  <button
                    onClick={() => runTransform('both')}
                    className="px-2.5 py-1 bg-ok/15 border border-ok/40 text-ok rounded font-medium hover:bg-ok/25 transition-colors"
                  >
                    Both (Full Normalization)
                  </button>
                </div>
              </div>

              {transformResult ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    {/* Original */}
                    <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-1">
                      <div className="font-bold text-text-1 text-xs">Original Grammar</div>
                      <pre className="p-2 bg-bg-0 border border-border rounded text-[11px] max-h-48 overflow-auto whitespace-pre-wrap">
                        {transformResult.original_bnf}
                      </pre>
                    </div>

                    {/* Transformed */}
                    <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-accent text-xs">Transformed Grammar G'</span>
                        <button
                          onClick={handleUseTransformed}
                          className="flex items-center gap-1 text-[11px] text-accent hover:underline font-sans"
                        >
                          <span>Use as active input</span>
                          <ArrowRight className="w-3 h-3" />
                        </button>
                      </div>
                      <pre className="p-2 bg-bg-0 border border-border rounded text-[11px] max-h-48 overflow-auto whitespace-pre-wrap text-ok">
                        {transformResult.transformed_bnf}
                      </pre>
                    </div>
                  </div>

                  {/* Transformation Step Logs */}
                  {transformResult.steps && transformResult.steps.length > 0 && (
                    <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-2">
                      <div className="font-bold text-text-0 font-sans text-xs">
                        Transformation Step Log ({transformResult.steps.length} transformations applied)
                      </div>
                      <div className="space-y-1.5 max-h-48 overflow-auto">
                        {transformResult.steps.map((st: any, i: number) => (
                          <div key={i} className="p-2 bg-bg-1 border border-border/50 rounded text-[11px] space-y-0.5">
                            <div className="flex justify-between text-accent font-bold">
                              <span>Step #{st.step_number}: {st.transformation} on {st.nonterminal}</span>
                            </div>
                            <div className="text-text-1 font-sans">{st.explanation}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-8 text-center text-text-1 bg-bg-2/30 border border-dashed border-border rounded-lg">
                  Click one of the transformation buttons above to eliminate left recursion or left factor common prefixes.
                </div>
              )}
            </div>
          )}

          {/* TAB 3: LL(1) Table & Predictive Parse */}
          {activeTab === 'll1' && (
            <div className="space-y-4 text-xs font-mono">
              <div className="p-3 bg-bg-2 border border-border rounded-lg flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-3">
                  <span className="font-bold text-text-0">LL(1) Predictive Parsing Table M[A, a]</span>
                  {ll1Result && (
                    <span
                      className={`px-2 py-0.5 rounded font-bold text-[11px] ${
                        ll1Result.is_ll1
                          ? 'bg-ok/15 text-ok border border-ok/30'
                          : 'bg-err/15 text-err border border-err/30'
                      }`}
                    >
                      {ll1Result.is_ll1 ? 'Conflict-Free LL(1) ✓' : `${(ll1Result.conflicts || []).length} LL(1) Conflicts ✕`}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={testInput}
                    onChange={(e) => setTestInput(e.target.value)}
                    placeholder="Input tokens: id + id"
                    className="w-48 px-2 py-1 bg-bg-1 border border-border text-text-0 rounded outline-none"
                  />
                  <button
                    onClick={() => runLL1(testInput)}
                    className="px-2.5 py-1 bg-accent/15 border border-accent/40 text-accent rounded font-medium hover:bg-accent/25 transition-colors"
                  >
                    Parse String
                  </button>
                  <button
                    onClick={() => runRDPseudocode()}
                    className="px-2.5 py-1 bg-purple-950/60 border border-purple-700/50 text-purple-300 rounded font-medium hover:bg-purple-900/40 transition-colors"
                  >
                    Generate Recursive Descent
                  </button>
                </div>
              </div>

              {ll1Result ? (
                <>
                  {/* Parsing Table Grid */}
                  <div className="p-3 bg-bg-2 border border-border rounded-lg overflow-auto max-h-64">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-border text-text-1">
                          <th className="p-1.5 font-bold">Nonterminal</th>
                          <th className="p-1.5 font-bold">Transitions M[A, a]</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/40">
                        {Object.entries(ll1Result.table).map(([nt, row]) => (
                          <tr key={nt} className="hover:bg-bg-1">
                            <td className="p-1.5 font-bold text-accent align-top w-28">{nt}</td>
                            <td className="p-1.5">
                              <div className="flex flex-wrap gap-1.5">
                                {Object.entries(row).map(([term, prod]) => (
                                  <span
                                    key={term}
                                    className="px-1.5 py-0.5 bg-bg-0 border border-border rounded text-[11px]"
                                  >
                                    <span className="text-text-1">[{term}]:</span> <span className="text-text-0">{prod}</span>
                                  </span>
                                ))}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Parse String Trace */}
                  {ll1Result.parse_trace && (
                    <div className="space-y-2">
                      <div className="font-bold text-text-0 text-xs font-sans">
                        Predictive Stack Parse Simulation for "{testInput}"
                      </div>
                      <StepPlayer
                        steps={ll1Result.parse_trace}
                        render={(step: any) => (
                          <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-2 text-xs">
                            <div className="flex justify-between items-center text-accent font-bold">
                              <span>Step #{step.step}: {step.action}</span>
                            </div>
                            <div className="grid grid-cols-2 gap-2 text-[11px]">
                              <div>Stack: <span className="text-purple-300 font-bold">{step.stack?.join(' ')}</span></div>
                              <div>Input: <span className="text-cyan-300 font-bold">{step.input?.join(' ')}</span></div>
                            </div>
                          </div>
                        )}
                      />
                    </div>
                  )}

                  {/* Recursive Descent Pseudocode */}
                  {rdResult && (
                    <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-2">
                      <div className="font-bold text-text-0 font-sans text-xs">
                        Generated Recursive-Descent Parser Pseudocode
                      </div>
                      <pre className="p-3 bg-bg-0 border border-border rounded text-xs text-text-0 max-h-60 overflow-auto whitespace-pre-wrap">
                        {rdResult.pseudocode}
                      </pre>
                    </div>
                  )}
                </>
              ) : (
                <div className="p-8 text-center text-text-1 animate-pulse">Building LL(1) parsing table...</div>
              )}
            </div>
          )}

          {/* TAB 4: LR Family (LR0, SLR1, CLR1, LALR1) */}
          {activeTab === 'lr' && (
            <div className="space-y-4 text-xs font-mono">
              <div className="p-3 bg-bg-2 border border-border rounded-lg flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-3">
                  <span className="font-bold text-text-0">LR Automaton Family (Dragon Book §4.5 - §4.7)</span>
                  <div className="flex items-center gap-1 bg-bg-1 border border-border rounded p-0.5">
                    {['lr0', 'slr1', 'clr1', 'lalr1'].map((v) => (
                      <button
                        key={v}
                        onClick={() => {
                          setLrVariant(v);
                          runLR(v, testInput);
                        }}
                        className={`px-2 py-0.5 rounded text-[11px] font-bold uppercase transition-colors ${
                          lrVariant === v ? 'bg-accent/20 text-accent' : 'text-text-1 hover:text-text-0'
                        }`}
                      >
                        {v}
                      </button>
                    ))}
                  </div>
                </div>

                {lrResult && (
                  <div className="flex items-center gap-3">
                    <span className="text-text-1">States: <strong className="text-text-0">{lrResult.states_count}</strong></span>
                    <span
                      className={`px-2 py-0.5 rounded font-bold text-[11px] ${
                        lrResult.is_conflict_free
                          ? 'bg-ok/15 text-ok border border-ok/30'
                          : 'bg-err/15 text-err border border-err/30'
                      }`}
                    >
                      {lrResult.is_conflict_free ? 'Conflict-Free ✓' : `${(lrResult.conflicts || []).length} Conflicts ✕`}
                    </span>
                  </div>
                )}
              </div>

              {lrResult ? (
                <>
                  {/* ACTION and GOTO Tables */}
                  <div className="grid grid-cols-2 gap-4">
                    {/* Action Table */}
                    <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-2">
                      <div className="font-bold text-text-0">ACTION Table (Shifts & Reduces)</div>
                      <div className="space-y-1 max-h-56 overflow-auto">
                        {Object.entries(lrResult.action_table).map(([state, row]) => (
                          <div key={state} className="p-1.5 bg-bg-1 border border-border/50 rounded flex items-center justify-between">
                            <span className="font-bold text-accent">State {state}</span>
                            <span className="text-text-0 truncate max-w-xs">
                              {Object.entries(row)
                                .map(([t, a]) => `${t}:${a}`)
                                .join(' ')}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Goto Table */}
                    <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-2">
                      <div className="font-bold text-text-0">GOTO Table (Nonterminal Transitions)</div>
                      <div className="space-y-1 max-h-56 overflow-auto">
                        {Object.entries(lrResult.goto_table).map(([state, row]) => (
                          <div key={state} className="p-1.5 bg-bg-1 border border-border/50 rounded flex items-center justify-between">
                            <span className="font-bold text-purple-300">State {state}</span>
                            <span className="text-text-0">
                              {Object.entries(row)
                                .map(([nt, target]) => `${nt}→${target}`)
                                .join(' ')}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Shift-Reduce Parse Trace */}
                  {lrResult.parse_trace && (
                    <div className="space-y-2">
                      <div className="font-bold text-text-0 font-sans text-xs">
                        Shift-Reduce Parser Execution Trace for "{testInput}"
                      </div>
                      <StepPlayer
                        steps={lrResult.parse_trace}
                        render={(step: any) => (
                          <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-2 text-xs">
                            <div className="flex justify-between items-center text-accent font-bold">
                              <span>Step #{step.step}: {step.action}</span>
                            </div>
                            <div className="grid grid-cols-3 gap-2 text-[11px]">
                              <div>State Stack: <span className="text-purple-300 font-bold">{step.states?.join(' ')}</span></div>
                              <div>Symbol Stack: <span className="text-text-0 font-bold">{step.symbols?.join(' ')}</span></div>
                              <div>Remaining Input: <span className="text-cyan-300 font-bold">{step.input?.join(' ')}</span></div>
                            </div>
                          </div>
                        )}
                      />
                    </div>
                  )}
                </>
              ) : (
                <div className="p-8 text-center text-text-1 animate-pulse">Building LR automaton...</div>
              )}
            </div>
          )}

          {/* TAB 5: Operator Precedence */}
          {activeTab === 'op' && (
            <div className="space-y-4 text-xs font-mono">
              <div className="p-3 bg-bg-2 border border-border rounded-lg flex items-center justify-between">
                <div>
                  <div className="font-bold text-text-0">Operator-Precedence Relations (Dragon Book §4.6)</div>
                  <div className="text-[11px] text-text-1 font-sans">
                    Eligibility: No epsilon productions (ε) and no adjacent nonterminals in any RHS.
                  </div>
                </div>

                {opResult && (
                  <span
                    className={`px-2 py-0.5 rounded font-bold text-[11px] ${
                      opResult.is_operator_grammar
                        ? 'bg-ok/15 text-ok border border-ok/30'
                        : 'bg-err/15 text-err border border-err/30'
                    }`}
                  >
                    {opResult.is_operator_grammar ? 'Operator Grammar Eligible ✓' : 'Ineligible Grammar ✕'}
                  </span>
                )}
              </div>

              {opResult && (
                <>
                  {/* Leading & Trailing Sets */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-1">
                      <div className="font-bold text-accent">LEADING Sets</div>
                      {Object.entries(opResult.leading).map(([nt, syms]) => (
                        <div key={nt} className="flex justify-between p-1 bg-bg-1 border border-border/40 rounded text-[11px]">
                          <span>LEADING({nt})</span>
                          <span>{`{ ${syms.join(', ')} }`}</span>
                        </div>
                      ))}
                    </div>

                    <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-1">
                      <div className="font-bold text-purple-300">TRAILING Sets</div>
                      {Object.entries(opResult.trailing).map(([nt, syms]) => (
                        <div key={nt} className="flex justify-between p-1 bg-bg-1 border border-border/40 rounded text-[11px]">
                          <span>TRAILING({nt})</span>
                          <span>{`{ ${syms.join(', ')} }`}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Precedence Matrix */}
                  <div className="p-3 bg-bg-2 border border-border rounded-lg space-y-2">
                    <div className="font-bold text-text-0">Precedence Matrix (⋖, ≐, ⋗)</div>
                    <div className="space-y-1 max-h-48 overflow-auto">
                      {Object.entries(opResult.relations).map(([a, rels]) => (
                        <div key={a} className="p-1 bg-bg-1 border border-border/40 rounded flex items-center justify-between text-[11px]">
                          <span className="font-bold text-text-0 w-16">{a}</span>
                          <span className="text-text-1">
                            {Object.entries(rels)
                              .map(([b, r]) => `${a} ${r} ${b}`)
                              .join('   |   ')}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* TAB 6: Dangling Else Guided Demo */}
          {activeTab === 'dangling' && (
            <div className="space-y-4 text-xs font-sans">
              <div className="p-4 bg-bg-2 border border-border rounded-lg space-y-2">
                <h3 className="font-bold text-text-0 text-sm">The Classic Dangling-Else Ambiguity Problem</h3>
                <p className="text-text-1 leading-relaxed">
                  In grammars with optional <code className="text-accent">else</code> clauses, the statement{' '}
                  <code className="text-purple-300 font-mono">if (E1) if (E2) S1 else S2</code> has two distinct parse trees:
                  does the <code className="text-accent">else</code> pair with the outer or inner <code className="text-accent">if</code>?
                </p>
              </div>

              <div className="grid grid-cols-3 gap-4">
                {/* Approach 1 */}
                <div className="p-3 bg-bg-2 border border-err/40 rounded-lg space-y-2">
                  <div className="font-bold text-err">1. Ambiguous Grammar</div>
                  <p className="text-text-1 text-[11px]">
                    Produces a Shift/Reduce conflict in LR tables at state on token <code className="text-accent font-mono">else</code>.
                  </p>
                  <button
                    onClick={() => selectPreset('dangling_else')}
                    className="w-full py-1 bg-err/15 border border-err/40 text-err rounded font-medium hover:bg-err/25 transition-colors text-xs"
                  >
                    Load Ambiguous Preset
                  </button>
                </div>

                {/* Approach 2 */}
                <div className="p-3 bg-bg-2 border border-warn/40 rounded-lg space-y-2">
                  <div className="font-bold text-warn">2. Matched / Open Stmts</div>
                  <p className="text-text-1 text-[11px]">
                    Textbook disambiguation: split statements into MatchedStmt and OpenStmt. Conflict eliminated.
                  </p>
                  <button
                    onClick={() => selectPreset('dangling_else_resolved')}
                    className="w-full py-1 bg-warn/15 border border-warn/40 text-warn rounded font-medium hover:bg-warn/25 transition-colors text-xs"
                  >
                    Load Resolved Preset
                  </button>
                </div>

                {/* Approach 3 */}
                <div className="p-3 bg-bg-2 border border-ok/40 rounded-lg space-y-2">
                  <div className="font-bold text-ok">3. Vela Mandatory Braces</div>
                  <p className="text-text-1 text-[11px]">
                    Vela requires braces: <code className="text-accent font-mono">if (c) &#123; ... &#125;</code>.
                    FOLLOW(IfStmt) lacks <code className="text-accent font-mono">else</code>; zero ambiguity!
                  </p>
                  <button
                    onClick={() => selectPreset('vela')}
                    className="w-full py-1 bg-ok/15 border border-ok/40 text-ok rounded font-medium hover:bg-ok/25 transition-colors text-xs"
                  >
                    Load Vela Authoritative G
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
