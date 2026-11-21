import { create } from 'zustand';
import {
  api,
  type GrammarAnalyzeResponse,
  type GrammarLL1Response,
  type GrammarLRResponse,
  type GrammarOpPrecedenceResponse,
  type GrammarPresetItem,
  type GrammarRDPseudocodeResponse,
  type GrammarTransformResponse,
  type SDDEvaluateResponse,
} from '../api/client';

const DEFAULT_GRAMMAR = `E -> E + T | T
T -> T * F | F
F -> ( E ) | id
`;

interface LabState {
  grammarText: string;
  startSymbol: string;
  currentPresetId: string;
  presets: GrammarPresetItem[];
  analyzeResult: GrammarAnalyzeResponse | null;
  transformResult: GrammarTransformResponse | null;
  ll1Result: GrammarLL1Response | null;
  lrResult: GrammarLRResponse | null;
  opResult: GrammarOpPrecedenceResponse | null;
  rdResult: GrammarRDPseudocodeResponse | null;
  sddResult: SDDEvaluateResponse | null;
  loading: boolean;
  error: string | null;

  setGrammarText: (text: string) => void;
  setStartSymbol: (sym: string) => void;
  loadPresets: () => Promise<void>;
  selectPreset: (id: string) => Promise<void>;
  runAnalyze: () => Promise<void>;
  runTransform: (type: 'left_recursion' | 'left_factoring' | 'both') => Promise<void>;
  runLL1: (inputString?: string) => Promise<void>;
  runLR: (variant?: string, inputString?: string) => Promise<void>;
  runOpPrecedence: (inputString?: string) => Promise<void>;
  runRDPseudocode: () => Promise<void>;
  runSDD: (preset?: string, input?: string) => Promise<void>;
}

export const useLabStore = create<LabState>((set, get) => ({
  grammarText: DEFAULT_GRAMMAR,
  startSymbol: 'E',
  currentPresetId: 'arithmetic',
  presets: [],
  analyzeResult: null,
  transformResult: null,
  ll1Result: null,
  lrResult: null,
  opResult: null,
  rdResult: null,
  sddResult: null,
  loading: false,
  error: null,

  setGrammarText: (grammarText) => set({ grammarText }),
  setStartSymbol: (startSymbol) => set({ startSymbol }),

  loadPresets: async () => {
    try {
      const presets = await api.getGrammarPresets();
      set({ presets });
    } catch (err: unknown) {
      console.error('Failed to load grammar presets', err);
    }
  },

  selectPreset: async (id: string) => {
    try {
      set({ loading: true, error: null, currentPresetId: id });
      const detail = await api.getGrammarPreset(id);
      set({
        grammarText: detail.bnf_text,
        startSymbol: detail.start_symbol,
      });
      await get().runAnalyze();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ error: `Failed to load preset: ${msg}` });
    } finally {
      set({ loading: false });
    }
  },

  runAnalyze: async () => {
    const { grammarText, startSymbol } = get();
    try {
      set({ loading: true, error: null });
      const res = await api.analyzeGrammar({
        grammar_text: grammarText,
        start_symbol: startSymbol || undefined,
      });
      set({ analyzeResult: res });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ error: `Analysis failed: ${msg}` });
    } finally {
      set({ loading: false });
    }
  },

  runTransform: async (type) => {
    const { grammarText } = get();
    try {
      set({ loading: true, error: null });
      const res = await api.transformGrammar({
        grammar_text: grammarText,
        transform_type: type,
      });
      set({ transformResult: res });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ error: `Transform failed: ${msg}` });
    } finally {
      set({ loading: false });
    }
  },

  runLL1: async (inputString) => {
    const { grammarText, startSymbol } = get();
    try {
      set({ loading: true, error: null });
      const res = await api.ll1Grammar({
        grammar_text: grammarText,
        start_symbol: startSymbol || undefined,
        input_string: inputString || undefined,
      });
      set({ ll1Result: res });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ error: `LL(1) failed: ${msg}` });
    } finally {
      set({ loading: false });
    }
  },

  runLR: async (variant = 'slr1', inputString) => {
    const { grammarText } = get();
    try {
      set({ loading: true, error: null });
      const res = await api.lrGrammar({
        grammar_text: grammarText,
        variant,
        input_string: inputString || undefined,
      });
      set({ lrResult: res });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ error: `LR build failed: ${msg}` });
    } finally {
      set({ loading: false });
    }
  },

  runOpPrecedence: async (inputString) => {
    const { grammarText } = get();
    try {
      set({ loading: true, error: null });
      const res = await api.opPrecedenceGrammar({
        grammar_text: grammarText,
        input_string: inputString || undefined,
      });
      set({ opResult: res });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ error: `Operator precedence failed: ${msg}` });
    } finally {
      set({ loading: false });
    }
  },

  runRDPseudocode: async () => {
    const { grammarText } = get();
    try {
      set({ loading: true, error: null });
      const res = await api.rdPseudocodeGrammar({
        grammar_text: grammarText,
      });
      set({ rdResult: res });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ error: `Pseudocode generation failed: ${msg}` });
    } finally {
      set({ loading: false });
    }
  },

  runSDD: async (preset = 'desk_calculator', input = '') => {
    try {
      set({ loading: true, error: null });
      const res = await api.evaluateSDD({
        preset,
        input_text: input,
      });
      set({ sddResult: res });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ error: `SDD evaluation failed: ${msg}` });
    } finally {
      set({ loading: false });
    }
  },
}));
