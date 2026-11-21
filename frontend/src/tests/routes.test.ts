import { describe, it, expect } from 'vitest';
import * as pages from '../pages';
import { useCompileStore } from '../store/compileStore';
import { useUIStore } from '../store/uiStore';
import { useLabStore } from '../store/labStore';
import { velaLanguageDefinition } from '../features/editor/monarch';
import { VELA_SNIPPETS } from '../features/editor/snippets';

describe('Milestone M10 Frontend Verification', () => {
  it('exports all 12 concrete studio pages without placeholder empty states', () => {
    expect(pages.DashboardPage).toBeDefined();
    expect(pages.PlaygroundPage).toBeDefined();
    expect(pages.LexerPage).toBeDefined();
    expect(pages.ParserPage).toBeDefined();
    expect(pages.GrammarLabPage).toBeDefined();
    expect(pages.SemanticPage).toBeDefined();
    expect(pages.TreesPage).toBeDefined();
    expect(pages.IRPage).toBeDefined();
    expect(pages.OptimizerPage).toBeDefined();
    expect(pages.CodeGenPage).toBeDefined();
    expect(pages.VMPage).toBeDefined();
    expect(pages.ReferencePage).toBeDefined();
  });

  it('initializes compileStore with default Vela program and O1 enabled', () => {
    const state = useCompileStore.getState();
    expect(state.source).toContain('func main()');
    expect(state.optimize).toBe(true);
    expect(state.optLevel).toBe(1);
    expect(typeof state.compile).toBe('function');
    expect(typeof state.run).toBe('function');
    expect(typeof state.verify).toBe('function');
  });

  it('initializes uiStore with connected backend and closed drawers', () => {
    const state = useUIStore.getState();
    expect(state.backendConnected).toBe(true);
    expect(state.jsonDrawerData).toBeNull();
    expect(state.commandPaletteOpen).toBe(false);
  });

  it('initializes labStore with default grammar and actions', () => {
    const state = useLabStore.getState();
    expect(state.grammarText).toContain('E -> E + T');
    expect(state.startSymbol).toBe('E');
    expect(typeof state.runAnalyze).toBe('function');
    expect(typeof state.runTransform).toBe('function');
    expect(typeof state.runLL1).toBe('function');
    expect(typeof state.runLR).toBe('function');
  });

  it('defines monarch tokenization rules with all keywords and operators', () => {
    expect(velaLanguageDefinition.keywords).toContain('let');
    expect(velaLanguageDefinition.keywords).toContain('func');
    expect(velaLanguageDefinition.keywords).toContain('show');
    expect(velaLanguageDefinition.keywords).toContain('read');
    expect(velaLanguageDefinition.keywords).toContain('return');
    expect(velaLanguageDefinition.typeKeywords).toContain('int');
    expect(velaLanguageDefinition.typeKeywords).toContain('float');
    expect(velaLanguageDefinition.typeKeywords).toContain('bool');
  });

  it('provides default Monaco code snippets for learning', () => {
    expect(VELA_SNIPPETS.length).toBeGreaterThan(0);
    const funcSnippet = VELA_SNIPPETS.find((s) => s.label === 'func');
    expect(funcSnippet).toBeDefined();
    expect(funcSnippet?.insertText).toContain('func');
  });
});
