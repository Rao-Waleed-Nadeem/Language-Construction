import React, { useEffect, useState } from 'react';
import { Play, PlayCircle, RefreshCw, Command } from 'lucide-react';
import { useCompileStore } from '../../store/compileStore';
import { useUIStore } from '../../store/uiStore';
import { api, type ExampleItem } from '../../api/client';

export const TitleBar: React.FC = () => {
  const {
    filename,
    stale,
    compiling,
    running,
    optimize,
    autoCompile,
    currentExampleId,
    setOptimize,
    setAutoCompile,
    compile,
    run,
    loadExample,
  } = useCompileStore();

  const { setCommandPaletteOpen } = useUIStore();
  const [examples, setExamples] = useState<ExampleItem[]>([]);

  useEffect(() => {
    api.getExamples().then(setExamples).catch(console.error);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'Enter') {
        e.preventDefault();
        run();
      } else if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        compile();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [compile, run]);

  return (
    <header className="h-10 bg-bg-2 border-b border-border flex items-center justify-between px-3 text-xs select-none z-10">
      {/* Left: Branding & current file / example */}
      <div className="flex items-center gap-3">
        <span className="font-semibold text-text-0 tracking-wide">Vela Studio</span>
        <span className="text-border">/</span>

        {/* Example picker dropdown */}
        <select
          value={currentExampleId || ''}
          onChange={(e) => {
            if (e.target.value) loadExample(e.target.value);
          }}
          className="bg-bg-1 border border-border text-text-0 px-2 py-0.5 rounded text-xs outline-none cursor-pointer hover:border-text-1 focus:border-accent"
        >
          <option value="">{filename}</option>
          {examples.map((ex) => (
            <option key={ex.id} value={ex.id}>
              {ex.title} ({ex.filename})
            </option>
          ))}
        </select>

        {stale && (
          <span className="flex items-center gap-1 text-[11px] text-warn font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-warn animate-pulse" />
            Uncompiled
          </span>
        )}
      </div>

      {/* Center: Command Palette Trigger */}
      <button
        onClick={() => setCommandPaletteOpen(true)}
        className="flex items-center gap-2 px-3 py-1 bg-bg-1 border border-border rounded-lg text-text-1 hover:text-text-0 hover:border-text-1 transition-colors"
      >
        <Command className="w-3.5 h-3.5 text-accent" />
        <span className="text-[11px]">Command Palette</span>
        <kbd className="px-1 py-0.2 bg-bg-2 border border-border rounded text-[10px] font-mono">
          Ctrl+K
        </kbd>
      </button>

      {/* Right: Actions and toggles */}
      <div className="flex items-center gap-3">
        {/* Auto-compile toggle */}
        <label className="flex items-center gap-1.5 cursor-pointer text-text-1 hover:text-text-0 text-[11px]">
          <input
            type="checkbox"
            checked={autoCompile}
            onChange={(e) => setAutoCompile(e.target.checked)}
            className="accent-accent cursor-pointer"
          />
          <span>Auto-compile</span>
        </label>

        {/* Optimization level toggle */}
        <div className="flex items-center gap-1 bg-bg-1 border border-border rounded p-0.5">
          <button
            onClick={() => setOptimize(false)}
            className={`px-2 py-0.5 rounded text-[11px] font-mono transition-colors ${
              !optimize ? 'bg-accent/20 text-accent font-bold' : 'text-text-1 hover:text-text-0'
            }`}
          >
            O0
          </button>
          <button
            onClick={() => setOptimize(true)}
            className={`px-2 py-0.5 rounded text-[11px] font-mono transition-colors ${
              optimize ? 'bg-accent/20 text-accent font-bold' : 'text-text-1 hover:text-text-0'
            }`}
          >
            O1
          </button>
        </div>

        {/* Compile button */}
        <button
          onClick={() => compile()}
          disabled={compiling}
          title="Compile (Ctrl+Enter)"
          className="flex items-center gap-1.5 px-3 py-1 bg-accent/15 border border-accent/40 hover:bg-accent/25 text-accent rounded font-medium transition-colors disabled:opacity-50"
        >
          {compiling ? (
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Play className="w-3.5 h-3.5 fill-current" />
          )}
          <span>{compiling ? 'Compiling' : 'Compile'}</span>
        </button>

        {/* Run button */}
        <button
          onClick={() => run()}
          disabled={running}
          title="Run VM (Ctrl+Shift+Enter)"
          className="flex items-center gap-1.5 px-3 py-1 bg-ok/15 border border-ok/40 hover:bg-ok/25 text-ok rounded font-medium transition-colors disabled:opacity-50"
        >
          {running ? (
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <PlayCircle className="w-3.5 h-3.5" />
          )}
          <span>{running ? 'Running' : 'Run'}</span>
        </button>
      </div>
    </header>
  );
};
