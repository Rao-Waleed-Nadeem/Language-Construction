import React, { useState, useEffect, useRef } from 'react';
import {
  Play,
  Pause,
  SkipForward,
  SkipBack,
  RotateCcw,
  FastForward,
  Cpu,
  Terminal,
  AlertCircle,
  Layers,
  Circle,
  AlertTriangle,
} from 'lucide-react';
import { useCompileStore } from '../store/compileStore';
import { useUIStore } from '../store/uiStore';
import { BadgeUsedByCompiler } from '../components/common/Badge';
import { EmptyState } from '../components/common/Feedback';

export const VMPage: React.FC = () => {
  const {
    compileResult,
    stdin,
    setStdin,
    run,
    running,
    lastRunResult,
  } = useCompileStore();
  const { openJsonDrawer } = useUIStore();

  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(150); // ms per step
  const [breakpoints, setBreakpoints] = useState<Set<number>>(new Set());

  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Auto-run if compileResult is present and no lastRunResult
  useEffect(() => {
    if (compileResult && !lastRunResult && !running) {
      run(stdin);
    }
  }, [compileResult, lastRunResult, running, stdin, run]);

  // Synchronize step index when new run results arrive
  useEffect(() => {
    if (lastRunResult && lastRunResult.snapshots && lastRunResult.snapshots.length > 0) {
      setCurrentStepIndex(lastRunResult.snapshots.length - 1);
    } else {
      setCurrentStepIndex(0);
    }
  }, [lastRunResult]);

  // Playback timer loop
  useEffect(() => {
    if (isPlaying) {
      timerRef.current = setInterval(() => {
        setCurrentStepIndex((prev) => {
          const snapshots = lastRunResult?.snapshots || [];
          if (prev >= snapshots.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          const nextStep = prev + 1;
          const nextSnap = snapshots[nextStep];
          // Check breakpoint
          if (nextSnap && breakpoints.has(Number(nextSnap.pc))) {
            setIsPlaying(false);
          }
          return nextStep;
        });
      }, playbackSpeed);
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, playbackSpeed, lastRunResult, breakpoints]);

  if (!compileResult) {
    return (
      <EmptyState
        title="Virtual Machine Not Ready"
        description="Compile a program to load target instructions and execute them in the step-by-step register machine simulator."
      />
    );
  }

  const rawTarget: any = compileResult.target_program || {};
  const instructions: any[] = rawTarget.instructions || [];
  const snapshots: any[] = lastRunResult?.snapshots || [];
  const totalSnapshots = snapshots.length;

  // Active snapshot at currentStepIndex
  const currentSnap: any =
    totalSnapshots > 0 && currentStepIndex >= 0 && currentStepIndex < totalSnapshots
      ? snapshots[currentStepIndex]
      : null;

  // Previous snapshot for diffing register changes
  const prevSnap: any =
    currentStepIndex > 0 && currentStepIndex - 1 < totalSnapshots
      ? snapshots[currentStepIndex - 1]
      : null;

  // Active PC
  const currentPC: number = currentSnap ? currentSnap.pc : 0;

  // Stdout accumulated up to current step
  const stdoutUpToNow: string =
    lastRunResult && currentSnap
      ? (lastRunResult.stdout || '').slice(0, currentSnap.stdout_length || 0)
      : lastRunResult?.stdout || '';

  const toggleBreakpoint = (pc: number) => {
    setBreakpoints((prev) => {
      const next = new Set(prev);
      if (next.has(pc)) next.delete(pc);
      else next.add(pc);
      return next;
    });
  };

  const handleStepForward = () => {
    if (currentStepIndex < totalSnapshots - 1) {
      setCurrentStepIndex((prev) => prev + 1);
    }
  };

  const handleStepBackward = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex((prev) => prev - 1);
    }
  };

  const handleRunToEnd = () => {
    setIsPlaying(false);
    if (totalSnapshots > 0) {
      setCurrentStepIndex(totalSnapshots - 1);
    }
  };

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentStepIndex(0);
  };

  const handleReRun = async () => {
    setIsPlaying(false);
    await run(stdin);
  };

  const isHalted = currentStepIndex >= totalSnapshots - 1 && totalSnapshots > 0;
  const hasRuntimeError = lastRunResult && !lastRunResult.success;

  return (
    <div className="h-full flex flex-col bg-bg-0 overflow-hidden font-sans">
      {/* Top Toolbar: VM Control Bar */}
      <div className="h-10 bg-bg-2 border-b border-border flex items-center justify-between px-3 text-xs select-none">
        {/* Left: Step Controls */}
        <div className="flex items-center gap-1.5">
          {/* Reset */}
          <button
            onClick={handleReset}
            title="Reset to Step 0"
            className="p-1.5 rounded hover:bg-bg-1 text-text-1 hover:text-text-0 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          {/* Step Back (AC-V2) */}
          <button
            onClick={handleStepBackward}
            disabled={currentStepIndex <= 0}
            title="Step Backward (Restores Exact Machine State)"
            className="p-1.5 rounded hover:bg-bg-1 text-text-1 hover:text-text-0 disabled:opacity-30 transition-colors"
          >
            <SkipBack className="w-3.5 h-3.5" />
          </button>

          {/* Play / Pause */}
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            title={isPlaying ? 'Pause' : 'Play / Run Trace'}
            className="flex items-center gap-1 px-2.5 py-1 rounded bg-accent/20 hover:bg-accent/30 text-accent font-semibold transition-colors border border-accent/40"
          >
            {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            <span>{isPlaying ? 'Pause' : 'Run'}</span>
          </button>

          {/* Step Forward */}
          <button
            onClick={handleStepForward}
            disabled={currentStepIndex >= totalSnapshots - 1}
            title="Step Forward (1 Target Instruction)"
            className="p-1.5 rounded hover:bg-bg-1 text-text-1 hover:text-text-0 disabled:opacity-30 transition-colors"
          >
            <SkipForward className="w-3.5 h-3.5" />
          </button>

          {/* Run to End */}
          <button
            onClick={handleRunToEnd}
            disabled={isHalted}
            title="Run to End"
            className="p-1.5 rounded hover:bg-bg-1 text-text-1 hover:text-text-0 disabled:opacity-30 transition-colors"
          >
            <FastForward className="w-3.5 h-3.5" />
          </button>

          <span className="text-border mx-1">|</span>

          {/* Step Scrub Slider */}
          <div className="flex items-center gap-2">
            <span className="text-text-1 font-mono text-[11px]">
              Step <strong className="text-text-0">{totalSnapshots > 0 ? currentStepIndex + 1 : 0}</strong> / {totalSnapshots}
            </span>
            <input
              type="range"
              min={0}
              max={Math.max(0, totalSnapshots - 1)}
              value={currentStepIndex}
              onChange={(e) => {
                setIsPlaying(false);
                setCurrentStepIndex(Number(e.target.value));
              }}
              className="w-32 h-1 accent-accent cursor-pointer"
            />
          </div>

          <span className="text-border mx-1">|</span>

          {/* Playback speed */}
          <div className="flex items-center gap-1 text-[11px] text-text-1">
            <span>Speed:</span>
            <select
              value={playbackSpeed}
              onChange={(e) => setPlaybackSpeed(Number(e.target.value))}
              className="bg-bg-1 border border-border text-text-0 rounded px-1 py-0.5 outline-none font-mono"
            >
              <option value={500}>0.5x</option>
              <option value={150}>1x</option>
              <option value={50}>3x</option>
              <option value={10}>Max</option>
            </select>
          </div>
        </div>

        {/* Right: stdin input & re-run */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1">
            <span className="text-text-1 text-[11px]">stdin:</span>
            <input
              type="text"
              value={stdin}
              onChange={(e) => setStdin(e.target.value)}
              placeholder="Input stream..."
              className="px-2 py-0.5 bg-bg-1 border border-border text-text-0 rounded text-xs font-mono w-28 outline-none"
            />
          </div>

          <button
            onClick={handleReRun}
            disabled={running}
            className="px-2 py-1 rounded bg-bg-1 border border-border text-text-0 hover:border-accent text-xs transition-colors"
          >
            {running ? 'Running...' : 'Re-Run'}
          </button>

          <BadgeUsedByCompiler />

          <button
            onClick={() => openJsonDrawer('VM Execution Run & Snapshots', lastRunResult)}
            className="text-[11px] text-accent hover:underline"
          >
            Raw JSON
          </button>
        </div>
      </div>

      {/* AC-V4: Truncation Banner */}
      {lastRunResult?.truncated_snapshots && (
        <div className="bg-warn/10 border-b border-warn/30 px-3 py-1.5 flex items-center justify-between text-xs text-warn">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>
              Execution exceeded 5,000 steps ({lastRunResult.steps_executed} steps executed). History snapshots
              capped for performance; full stdout is shown below.
            </span>
          </div>
        </div>
      )}

      {/* Main 3-Column Workspace */}
      <div className="flex-1 flex overflow-hidden">
        {/* COLUMN 1: Program Disassembly with PC highlight & Breakpoints */}
        <div className="w-80 border-r border-border bg-bg-1 flex flex-col overflow-hidden">
          <div className="p-2.5 bg-bg-2 border-b border-border flex items-center justify-between text-xs">
            <span className="font-bold text-text-0">Disassembly</span>
            <span className="text-text-1 font-mono text-[11px]">{instructions.length} instrs</span>
          </div>

          <div className="flex-1 overflow-auto font-mono text-xs select-none">
            {instructions.map((inst: any, idx: number) => {
              const isCurrentPC = idx === currentPC;
              const hasBreakpoint = breakpoints.has(idx);

              return (
                <div
                  key={idx}
                  onClick={() => toggleBreakpoint(idx)}
                  className={`flex items-center px-2 py-1 cursor-pointer transition-colors ${
                    isCurrentPC
                      ? 'bg-accent/20 border-l-4 border-accent text-text-0 font-bold'
                      : 'hover:bg-bg-2/50 text-text-1 border-l-4 border-transparent'
                  }`}
                >
                  {/* Breakpoint Gutter */}
                  <div className="w-5 flex items-center justify-center">
                    {hasBreakpoint ? (
                      <Circle className="w-2.5 h-2.5 fill-err text-err" />
                    ) : isCurrentPC ? (
                      <span className="text-accent text-[11px]">▶</span>
                    ) : (
                      <span className="text-border text-[9px] group-hover:text-text-1">·</span>
                    )}
                  </div>

                  {/* Address */}
                  <div className="w-8 text-[11px] text-text-1">{idx.toString().padStart(3, '0')}</div>

                  {/* Label or Instruction */}
                  <div className="flex-1 truncate">
                    {inst.label ? (
                      <span className="text-warn">{inst.label}:</span>
                    ) : (
                      <>
                        <span className="text-accent font-semibold">{inst.opcode}</span>
                        <span className="text-text-0">
                          {' '}
                          {[inst.dst, inst.src1, inst.src2].filter(Boolean).join(', ')}
                        </span>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* COLUMN 2: Machine State (Registers, Flags, Stack) */}
        <div className="flex-1 flex flex-col border-r border-border overflow-hidden bg-bg-0">
          <div className="p-2.5 bg-bg-2 border-b border-border flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-accent" />
              <span className="font-bold text-text-0">Machine State</span>
            </div>
            {currentSnap && (
              <span className="font-mono text-text-1 text-[11px]">
                PC: {currentSnap.pc} | Call Depth: {currentSnap.call_depth}
              </span>
            )}
          </div>

          <div className="flex-1 overflow-auto p-4 space-y-4">
            {/* General Purpose Registers R0–R7 */}
            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs font-bold text-text-0">
                <span>Registers (R0–R7)</span>
                <span className="text-text-1 text-[11px] font-normal">Highlighted on value change</span>
              </div>

              <div className="grid grid-cols-4 gap-2 font-mono text-xs">
                {['R0', 'R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7'].map((reg) => {
                  const val = currentSnap?.registers ? currentSnap.registers[reg] : 0;
                  const prevVal = prevSnap?.registers ? prevSnap.registers[reg] : undefined;
                  const changed = prevVal !== undefined && prevVal !== val;

                  return (
                    <div
                      key={reg}
                      className={`p-2.5 rounded-lg border transition-colors ${
                        changed
                          ? 'bg-accent/20 border-accent text-accent font-bold ring-1 ring-accent'
                          : 'bg-bg-1 border-border text-text-0'
                      }`}
                    >
                      <div className="flex justify-between text-[10px] text-text-1">
                        <span>{reg}</span>
                        {changed && <span className="text-accent text-[9px]">UPDATED</span>}
                      </div>
                      <div className="text-sm font-bold truncate pt-0.5">
                        {val !== undefined && val !== null ? String(val) : '0'}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Special Registers & Condition Flags */}
            <div className="grid grid-cols-2 gap-4">
              {/* Special Pointers */}
              <div className="p-3 bg-bg-1 border border-border rounded-lg space-y-2">
                <div className="font-bold text-xs text-text-0">Control & Pointer Registers</div>
                <div className="grid grid-cols-3 gap-2 font-mono text-xs">
                  <div className="p-2 bg-bg-0 border border-border rounded">
                    <div className="text-[10px] text-text-1">PC</div>
                    <div className="font-bold text-accent">{currentPC}</div>
                  </div>
                  <div className="p-2 bg-bg-0 border border-border rounded">
                    <div className="text-[10px] text-text-1">SP</div>
                    <div className="font-bold text-ok">{currentSnap?.registers?.SP ?? 1024}</div>
                  </div>
                  <div className="p-2 bg-bg-0 border border-border rounded">
                    <div className="text-[10px] text-text-1">FP</div>
                    <div className="font-bold text-text-0">{currentSnap?.registers?.FP ?? 1024}</div>
                  </div>
                </div>
              </div>

              {/* Status Flags */}
              <div className="p-3 bg-bg-1 border border-border rounded-lg space-y-2">
                <div className="font-bold text-xs text-text-0">Status Flags</div>
                <div className="grid grid-cols-2 gap-2 font-mono text-xs">
                  <div
                    className={`p-2 rounded border ${
                      currentSnap?.flags?.ZF
                        ? 'bg-ok/20 border-ok text-ok font-bold'
                        : 'bg-bg-0 border-border text-text-1'
                    }`}
                  >
                    <div className="text-[10px]">Zero Flag (ZF)</div>
                    <div className="text-sm">{currentSnap?.flags?.ZF ? '1 (TRUE)' : '0 (FALSE)'}</div>
                  </div>
                  <div
                    className={`p-2 rounded border ${
                      currentSnap?.flags?.SF
                        ? 'bg-warn/20 border-warn text-warn font-bold'
                        : 'bg-bg-0 border-border text-text-1'
                    }`}
                  >
                    <div className="text-[10px]">Sign Flag (SF)</div>
                    <div className="text-sm">{currentSnap?.flags?.SF ? '1 (NEGATIVE)' : '0 (POSITIVE)'}</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Stack Frame View */}
            <div className="p-3 bg-bg-1 border border-border rounded-lg space-y-2">
              <div className="flex justify-between items-center text-xs font-bold text-text-0">
                <div className="flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-accent" />
                  <span>Activation Stack (Top of Stack)</span>
                </div>
                <span className="text-text-1 text-[11px] font-mono">
                  Stack Size: {currentSnap?.stack?.length || 0}
                </span>
              </div>

              <div className="p-2 bg-bg-0 border border-border rounded font-mono text-xs min-h-[60px] flex items-center justify-center">
                {currentSnap?.stack && currentSnap.stack.length > 0 ? (
                  <div className="w-full space-y-1">
                    {currentSnap.stack.map((item: any, i: number) => (
                      <div
                        key={i}
                        className="flex justify-between items-center p-1 bg-bg-1 border border-border/50 rounded text-[11px]"
                      >
                        <span className="text-text-1">Slot [-{currentSnap.stack.length - i}]:</span>
                        <span className="font-bold text-text-0">{JSON.stringify(item)}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <span className="text-text-1 text-xs">Stack empty (at frame base)</span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* COLUMN 3: Console Output & Status */}
        <div className="w-80 bg-bg-1 flex flex-col overflow-hidden">
          <div className="p-2.5 bg-bg-2 border-b border-border flex items-center justify-between text-xs">
            <div className="flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5 text-accent" />
              <span className="font-bold text-text-0">Execution Console</span>
            </div>
            {lastRunResult && (
              <span
                className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                  lastRunResult.exit_code === 0
                    ? 'bg-ok/20 text-ok border border-ok/40'
                    : 'bg-err/20 text-err border border-err/40'
                }`}
              >
                Exit: {lastRunResult.exit_code}
              </span>
            )}
          </div>

          {/* Faulting Instruction Alert if runtime error (AC-V3) */}
          {hasRuntimeError && (
            <div className="p-3 bg-err/10 border-b border-err/30 text-xs space-y-1">
              <div className="flex items-center gap-1.5 text-err font-bold">
                <AlertCircle className="w-4 h-4" />
                <span>Runtime Exception: {String(lastRunResult?.diagnostics?.[0]?.code || 'VL-RUN')}</span>
              </div>
              <div className="text-text-0 text-[11px]">
                {String(lastRunResult?.diagnostics?.[0]?.message || 'Program halted with a runtime fault.')}
              </div>
              <div className="text-[10px] text-text-1 font-mono pt-1">
                Faulting instruction at PC #{currentPC}
              </div>
            </div>
          )}

          {/* Stdout Stream */}
          <div className="flex-1 p-3 bg-bg-0 overflow-auto font-mono text-xs">
            <div className="text-text-1 text-[11px] mb-2 border-b border-border pb-1">
              Standard Output Stream:
            </div>
            {stdoutUpToNow ? (
              <pre className="text-text-0 whitespace-pre-wrap">{stdoutUpToNow}</pre>
            ) : (
              <span className="text-text-1 italic">(no stdout produced yet)</span>
            )}
          </div>

          {/* Execution Metrics Footer */}
          <div className="p-3 bg-bg-2 border-t border-border space-y-1 text-xs">
            <div className="flex justify-between text-text-1">
              <span>Steps Executed:</span>
              <span className="font-mono font-bold text-text-0">
                {lastRunResult?.steps_executed || 0}
              </span>
            </div>
            <div className="flex justify-between text-text-1">
              <span>Machine Cycles / Cost:</span>
              <span className="font-mono font-bold text-ok">{lastRunResult?.total_cost || 0}</span>
            </div>
            <div className="flex justify-between text-text-1">
              <span>VM State:</span>
              <span
                className={`font-semibold ${
                  hasRuntimeError ? 'text-err' : isHalted ? 'text-ok' : 'text-accent'
                }`}
              >
                {hasRuntimeError ? 'HALTED (FAULT)' : isHalted ? 'HALTED (EXIT 0)' : 'STEPPING'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
