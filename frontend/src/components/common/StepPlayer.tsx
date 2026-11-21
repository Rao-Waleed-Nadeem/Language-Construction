import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, SkipBack, SkipForward, ChevronLeft, ChevronRight } from 'lucide-react';

interface StepPlayerProps<T> {
  steps: T[];
  render: (step: T, index: number) => React.ReactNode;
  initialStep?: number;
  onStepChange?: (index: number) => void;
  className?: string;
}

export function StepPlayer<T>({
  steps,
  render,
  initialStep = 0,
  onStepChange,
  className = '',
}: StepPlayerProps<T>) {
  const [currentStep, setCurrentStep] = useState(initialStep);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1); // 0.25x, 0.5x, 1x, 2x, 4x

  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const totalSteps = steps.length;

  const goToStep = (step: number) => {
    const target = Math.max(0, Math.min(step, totalSteps - 1));
    setCurrentStep(target);
    onStepChange?.(target);
  };

  useEffect(() => {
    if (isPlaying) {
      if (currentStep >= totalSteps - 1) {
        setIsPlaying(false);
        return;
      }
      const intervalMs = Math.max(50, 800 / speed);
      timerRef.current = setTimeout(() => {
        goToStep(currentStep + 1);
      }, intervalMs);
    }
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [isPlaying, currentStep, totalSteps, speed]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Only listen if not typing in an input
      if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement)?.tagName)) return;
      if (e.key === 'ArrowLeft') {
        goToStep(currentStep - 1);
      } else if (e.key === 'ArrowRight') {
        goToStep(currentStep + 1);
      } else if (e.key === ' ') {
        e.preventDefault();
        setIsPlaying((p) => !p);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentStep, totalSteps]);

  if (totalSteps === 0) {
    return (
      <div className="p-4 text-center text-xs text-text-1 bg-bg-1 border border-border rounded">
        No execution steps recorded
      </div>
    );
  }

  const activeItem = steps[currentStep];

  return (
    <div className={`flex flex-col bg-bg-1 border border-border rounded-lg overflow-hidden ${className}`}>
      {/* Player header / controls */}
      <div className="flex items-center justify-between p-2 bg-bg-2 border-b border-border text-xs gap-3 select-none">
        {/* Playback buttons */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => {
              setIsPlaying(false);
              goToStep(0);
            }}
            disabled={currentStep === 0}
            title="First step (⏮)"
            className="p-1 rounded hover:bg-bg-1 disabled:opacity-30 text-text-0 transition-colors"
          >
            <SkipBack className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => {
              setIsPlaying(false);
              goToStep(currentStep - 1);
            }}
            disabled={currentStep === 0}
            title="Previous step (←)"
            className="p-1 rounded hover:bg-bg-1 disabled:opacity-30 text-text-0 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            title={isPlaying ? 'Pause (Space)' : 'Play (Space)'}
            className="p-1.5 rounded bg-accent/20 text-accent hover:bg-accent/30 transition-colors"
          >
            {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 fill-current" />}
          </button>
          <button
            onClick={() => {
              setIsPlaying(false);
              goToStep(currentStep + 1);
            }}
            disabled={currentStep >= totalSteps - 1}
            title="Next step (→)"
            className="p-1 rounded hover:bg-bg-1 disabled:opacity-30 text-text-0 transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
          <button
            onClick={() => {
              setIsPlaying(false);
              goToStep(totalSteps - 1);
            }}
            disabled={currentStep >= totalSteps - 1}
            title="Last step (⏭)"
            className="p-1 rounded hover:bg-bg-1 disabled:opacity-30 text-text-0 transition-colors"
          >
            <SkipForward className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Step progress & scrub slider */}
        <div className="flex-1 flex items-center gap-2">
          <input
            type="range"
            min={0}
            max={totalSteps - 1}
            value={currentStep}
            onChange={(e) => {
              setIsPlaying(false);
              goToStep(Number(e.target.value));
            }}
            className="w-full h-1 bg-border rounded-lg appearance-none cursor-pointer accent-accent"
          />
          <span className="font-mono text-text-1 text-xs whitespace-nowrap">
            {currentStep + 1} / {totalSteps}
          </span>
        </div>

        {/* Speed multiplier selector */}
        <div className="flex items-center gap-1 border-l border-border pl-2">
          {[0.5, 1, 2, 4].map((s) => (
            <button
              key={s}
              onClick={() => setSpeed(s)}
              className={`px-1.5 py-0.5 rounded text-[10px] font-mono transition-colors ${
                speed === s ? 'bg-accent text-bg-0 font-bold' : 'text-text-1 hover:text-text-0'
              }`}
            >
              {s}x
            </button>
          ))}
        </div>
      </div>

      {/* Rendered step content */}
      <div className="flex-1 overflow-auto p-4">{render(activeItem, currentStep)}</div>
    </div>
  );
}
