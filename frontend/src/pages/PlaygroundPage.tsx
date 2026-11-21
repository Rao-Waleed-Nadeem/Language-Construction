import React, { useState } from 'react';
import {
  Play,
  Terminal,
  AlertCircle,
  FileText,
  ShieldCheck,
  Download,
  Upload,
  RotateCcw,
  RefreshCw,
  Code2,
} from 'lucide-react';
import { useCompileStore } from '../store/compileStore';
import { useUIStore } from '../store/uiStore';
import { SourceView } from '../components/common/SourceView';
import { DiagnosticList, type DiagnosticItem } from '../components/common/DiagnosticList';

export const PlaygroundPage: React.FC = () => {
  const {
    source,
    stdin,
    filename,
    compileResult,
    lastRunResult,
    lastVerifyResult,
    running,
    verifying,
    setSource,
    setStdin,
    compile,
    run,
    verify,
  } = useCompileStore();

  const { openJsonDrawer } = useUIStore();

  const [activeTab, setActiveTab] = useState<'output' | 'problems' | 'stdin' | 'verify'>('output');

  const diagnostics: DiagnosticItem[] = (compileResult?.diagnostics || []).map((d) => ({
    code: String(d.code || 'VL-000'),
    severity: String(d.severity || 'error'),
    phase: String(d.phase || 'compiler'),
    message: String(d.message || ''),
    span: d.span as DiagnosticItem['span'],
    hint: d.hint ? String(d.hint) : null,
  }));

  const errorCount = diagnostics.filter((d) => d.severity.toLowerCase() === 'error').length;
  const warningCount = diagnostics.filter((d) => d.severity.toLowerCase() === 'warning').length;

  const handleDownload = () => {
    const blob = new Blob([source], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || 'main.vela';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        if (typeof event.target?.result === 'string') {
          setSource(event.target.result);
        }
      };
      reader.readAsText(file);
    }
  };

  return (
    <div className="h-full flex flex-col bg-bg-0 overflow-hidden">
      {/* Editor & Console Toolbar */}
      <div className="h-9 bg-bg-2 border-b border-border flex items-center justify-between px-3 text-xs">
        <div className="flex items-center gap-2">
          <span className="font-mono text-text-0 font-medium">{filename}</span>
          <span className="text-border">|</span>

          {/* Upload .vela */}
          <label className="flex items-center gap-1 px-2 py-0.5 rounded bg-bg-1 hover:bg-bg-0 text-text-1 hover:text-text-0 border border-border cursor-pointer transition-colors">
            <Upload className="w-3 h-3" />
            <span>Open</span>
            <input type="file" accept=".vela,.txt" onChange={handleUpload} className="hidden" />
          </label>

          {/* Download .vela */}
          <button
            onClick={handleDownload}
            className="flex items-center gap-1 px-2 py-0.5 rounded bg-bg-1 hover:bg-bg-0 text-text-1 hover:text-text-0 border border-border transition-colors"
          >
            <Download className="w-3 h-3" />
            <span>Save</span>
          </button>

          {/* Reset */}
          <button
            onClick={() => compile()}
            title="Recompile"
            className="flex items-center gap-1 px-2 py-0.5 rounded bg-bg-1 hover:bg-bg-0 text-text-1 hover:text-text-0 border border-border transition-colors"
          >
            <RotateCcw className="w-3 h-3" />
            <span>Recompile</span>
          </button>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => verify()}
            disabled={verifying}
            className="flex items-center gap-1.5 px-2.5 py-1 bg-bg-1 hover:bg-bg-0 border border-border rounded text-text-0 font-medium transition-colors disabled:opacity-50"
          >
            {verifying ? <RefreshCw className="w-3 h-3 animate-spin" /> : <ShieldCheck className="w-3.5 h-3.5 text-accent" />}
            <span>Verify (Oracle = VM)</span>
          </button>

          <button
            onClick={() => run()}
            disabled={running}
            className="flex items-center gap-1.5 px-3 py-1 bg-ok/15 border border-ok/40 hover:bg-ok/25 text-ok rounded font-semibold transition-colors disabled:opacity-50"
          >
            {running ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-current" />}
            <span>Run</span>
          </button>
        </div>
      </div>

      {/* Main split: Editor (60%) and Tabs (40%) */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Code Editor */}
        <div className="w-[60%] h-full flex flex-col border-r border-border">
          <SourceView
            source={source}
            onChange={setSource}
            readOnly={false}
            className="flex-1 rounded-none border-none"
          />
        </div>

        {/* Right: Output / Problems / Stdin / Verify */}
        <div className="w-[40%] h-full flex flex-col bg-bg-1">
          {/* Tab bar */}
          <div className="flex items-center border-b border-border bg-bg-2 px-2 text-xs">
            <button
              onClick={() => setActiveTab('output')}
              className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors ${
                activeTab === 'output'
                  ? 'border-accent text-accent bg-bg-1'
                  : 'border-transparent text-text-1 hover:text-text-0'
              }`}
            >
              <Terminal className="w-3.5 h-3.5" />
              <span>Console Output</span>
            </button>

            <button
              onClick={() => setActiveTab('problems')}
              className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors ${
                activeTab === 'problems'
                  ? 'border-accent text-accent bg-bg-1'
                  : 'border-transparent text-text-1 hover:text-text-0'
              }`}
            >
              <AlertCircle className="w-3.5 h-3.5" />
              <span>Problems</span>
              {(errorCount > 0 || warningCount > 0) && (
                <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] bg-err/20 text-err font-bold">
                  {errorCount + warningCount}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab('stdin')}
              className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors ${
                activeTab === 'stdin'
                  ? 'border-accent text-accent bg-bg-1'
                  : 'border-transparent text-text-1 hover:text-text-0'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Stdin</span>
            </button>

            <button
              onClick={() => setActiveTab('verify')}
              className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition-colors ${
                activeTab === 'verify'
                  ? 'border-accent text-accent bg-bg-1'
                  : 'border-transparent text-text-1 hover:text-text-0'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Verification</span>
            </button>
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-auto p-3">
            {activeTab === 'output' && (
              <div className="h-full flex flex-col font-mono text-xs">
                {/* Status chip */}
                {lastRunResult && (
                  <div className="flex items-center justify-between pb-2 mb-2 border-b border-border text-[11px] text-text-1">
                    <div className="flex items-center gap-3">
                      <span className={lastRunResult.exit_code === 0 ? 'text-ok font-bold' : 'text-err font-bold'}>
                        Exit: {lastRunResult.exit_code}
                      </span>
                      <span>Steps: {lastRunResult.steps_executed}</span>
                      <span>Cost: {lastRunResult.total_cost}</span>
                    </div>
                    <button
                      onClick={() => openJsonDrawer('Run Execution Result', lastRunResult)}
                      className="text-accent hover:underline flex items-center gap-1"
                    >
                      <Code2 className="w-3 h-3" />
                      JSON
                    </button>
                  </div>
                )}

                {/* Console output display */}
                <div className="flex-1 p-3 bg-bg-0 border border-border rounded-lg overflow-auto whitespace-pre-wrap text-text-0 select-text">
                  {running ? (
                    <div className="flex items-center gap-2 text-text-1 animate-pulse">
                      <RefreshCw className="w-3.5 h-3.5 animate-spin text-accent" />
                      <span>Executing on Virtual Machine...</span>
                    </div>
                  ) : lastRunResult ? (
                    lastRunResult.stdout ? (
                      lastRunResult.stdout
                    ) : (
                      <span className="text-text-1 italic font-sans">
                        Program exited with status {lastRunResult.exit_code} (no standard output produced).
                      </span>
                    )
                  ) : (
                    <span className="text-text-1 italic font-sans">
                      Press "Run" (Ctrl+Shift+Enter) to compile and execute program on the target Virtual Machine.
                    </span>
                  )}

                  {/* Runtime errors */}
                  {lastRunResult && !lastRunResult.success && lastRunResult.diagnostics && (
                    <div className="mt-4 p-3 bg-err/10 border border-err/40 rounded text-err">
                      <div className="font-bold flex items-center gap-1.5 mb-1">
                        <AlertCircle className="w-4 h-4" />
                        <span>Runtime Error</span>
                      </div>
                      {lastRunResult.diagnostics.map((d, i) => (
                        <div key={i} className="text-xs pl-5 space-y-0.5">
                          <span className="font-bold">{String(d.code)}: </span>
                          <span>{String(d.message)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'problems' && (
              <div className="h-full flex flex-col">
                <DiagnosticList diagnostics={diagnostics} className="h-full" />
              </div>
            )}

            {activeTab === 'stdin' && (
              <div className="h-full flex flex-col space-y-2">
                <div className="text-[11px] text-text-1">
                  Enter inputs passed sequentially to <code className="text-accent">read</code> statements.
                </div>
                <textarea
                  value={stdin}
                  onChange={(e) => setStdin(e.target.value)}
                  placeholder="e.g.&#10;42&#10;hello&#10;3.14"
                  className="flex-1 p-3 bg-bg-0 border border-border rounded-lg font-mono text-xs text-text-0 outline-none resize-none focus:border-accent"
                />
              </div>
            )}

            {activeTab === 'verify' && (
              <div className="h-full flex flex-col space-y-3 font-sans text-xs">
                <div className="flex items-center justify-between p-3 bg-bg-2 border border-border rounded-lg">
                  <div>
                    <h3 className="font-bold text-text-0">Independent 3-Way Oracle Verification</h3>
                    <p className="text-[11px] text-text-1">
                      Compares Unoptimized TAC Oracle, Optimized TAC Oracle, and Target Virtual Machine.
                    </p>
                  </div>
                  <button
                    onClick={() => verify()}
                    disabled={verifying}
                    className="px-3 py-1.5 bg-accent/15 border border-accent/40 text-accent rounded font-medium hover:bg-accent/25 transition-colors disabled:opacity-50"
                  >
                    {verifying ? 'Checking...' : 'Run Verification'}
                  </button>
                </div>

                {lastVerifyResult ? (
                  <div className="space-y-3">
                    <div
                      className={`p-3 rounded-lg border flex items-center gap-2 font-bold ${
                        lastVerifyResult.match
                          ? 'bg-ok/10 border-ok/30 text-ok'
                          : 'bg-err/10 border-err/30 text-err'
                      }`}
                    >
                      {lastVerifyResult.match ? (
                        <>
                          <ShieldCheck className="w-5 h-5" />
                          <span>All 3 execution engines produced identical output ✓</span>
                        </>
                      ) : (
                        <>
                          <AlertCircle className="w-5 h-5" />
                          <span>Behavior mismatch detected across compiler optimization pipeline</span>
                        </>
                      )}
                    </div>

                    <div className="grid grid-cols-3 gap-2 font-mono text-[11px]">
                      <div className="p-2.5 bg-bg-2 border border-border rounded">
                        <div className="font-bold text-text-1 mb-1">TAC Oracle (O0)</div>
                        <div className="text-text-0 whitespace-pre">
                          {String(lastVerifyResult.oracle_unopt?.stdout || '(empty)')}
                        </div>
                      </div>
                      <div className="p-2.5 bg-bg-2 border border-border rounded">
                        <div className="font-bold text-text-1 mb-1">TAC Oracle (O1)</div>
                        <div className="text-text-0 whitespace-pre">
                          {String(lastVerifyResult.oracle_opt?.stdout || '(empty)')}
                        </div>
                      </div>
                      <div className="p-2.5 bg-bg-2 border border-border rounded">
                        <div className="font-bold text-text-1 mb-1">Target VM</div>
                        <div className="text-text-0 whitespace-pre">
                          {String(lastVerifyResult.vm?.stdout || '(empty)')}
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="p-6 text-center text-text-1 bg-bg-2/30 border border-dashed border-border rounded-lg">
                    Press "Run Verification" to prove semantic preservation across the entire compiler pipeline.
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
