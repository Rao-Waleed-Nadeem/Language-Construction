import { create } from 'zustand';
import { api, type CompileResponse, type RunResponse, type VerifyResponse } from '../api/client';

const DEFAULT_SOURCE = `// Welcome to Vela Studio!
// A pedagogical compiler exploration environment.

func add(a: int, b: int) -> int {
    return a + b;
}

func main() {
    let x: int = 10;
    let y: int = 20;
    let sum: int = add(x, y);
    show "Sum = ", sum;
}
`;

interface CompileState {
  source: string;
  stdin: string;
  filename: string;
  currentExampleId: string | null;
  optimize: boolean;
  optLevel: number;
  autoCompile: boolean;
  compiling: boolean;
  running: boolean;
  verifying: boolean;
  compileResult: CompileResponse | null;
  lastRunResult: RunResponse | null;
  lastVerifyResult: VerifyResponse | null;
  stale: boolean;
  error: string | null;

  setSource: (source: string) => void;
  setStdin: (stdin: string) => void;
  setOptimize: (optimize: boolean) => void;
  setAutoCompile: (autoCompile: boolean) => void;
  loadExample: (id: string) => Promise<void>;
  compile: () => Promise<CompileResponse | null>;
  run: (stdinOverride?: string, useOracle?: boolean) => Promise<RunResponse | null>;
  verify: () => Promise<VerifyResponse | null>;
}

let compileTimeout: NodeJS.Timeout | null = null;

export const useCompileStore = create<CompileState>((set, get) => ({
  source: DEFAULT_SOURCE,
  stdin: '',
  filename: 'main.vela',
  currentExampleId: null,
  optimize: true,
  optLevel: 1,
  autoCompile: false,
  compiling: false,
  running: false,
  verifying: false,
  compileResult: null,
  lastRunResult: null,
  lastVerifyResult: null,
  stale: true,
  error: null,

  setSource: (source: string) => {
    set({ source, stale: true });
    if (get().autoCompile) {
      if (compileTimeout) clearTimeout(compileTimeout);
      compileTimeout = setTimeout(() => {
        get().compile();
      }, 800);
    }
  },

  setStdin: (stdin: string) => set({ stdin }),

  setOptimize: (optimize: boolean) => {
    set({ optimize, stale: true });
    if (get().autoCompile) {
      get().compile();
    }
  },

  setAutoCompile: (autoCompile: boolean) => set({ autoCompile }),

  loadExample: async (id: string) => {
    try {
      set({ compiling: true, error: null });
      const ex = await api.getExample(id);
      set({
        source: ex.source,
        stdin: ex.stdin || '',
        currentExampleId: id,
        filename: `${id}.vela`,
        stale: true,
      });
      await get().compile();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ error: `Failed to load example: ${msg}` });
    } finally {
      set({ compiling: false });
    }
  },

  compile: async () => {
    const { source, filename, optimize, optLevel } = get();
    try {
      set({ compiling: true, error: null });
      const res = await api.compile({
        source,
        filename,
        optimize,
        opt_level: optLevel,
        max_opt_iterations: 10,
      });
      set({ compileResult: res, stale: false });
      return res;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ error: `Compile failed: ${msg}` });
      return null;
    } finally {
      set({ compiling: false });
    }
  },

  run: async (stdinOverride?: string, useOracle = false) => {
    const { source, stdin, optimize } = get();
    try {
      set({ running: true, error: null });
      const res = await api.run({
        source,
        stdin: stdinOverride !== undefined ? stdinOverride : stdin,
        optimize,
        use_oracle: useOracle,
      });
      set({ lastRunResult: res });
      return res;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ error: `Run failed: ${msg}` });
      return null;
    } finally {
      set({ running: false });
    }
  },

  verify: async () => {
    const { source, stdin } = get();
    try {
      set({ verifying: true, error: null });
      const res = await api.verify({
        source,
        stdin,
      });
      set({ lastVerifyResult: res });
      return res;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ error: `Verify failed: ${msg}` });
      return null;
    } finally {
      set({ verifying: false });
    }
  },
}));
