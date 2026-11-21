/**
 * Typed API Client for Vela Studio backend.
 * All requests and responses are strictly typed via OpenAPI generated schema.
 */

import type { components } from './schema';

export type Schemas = components['schemas'];
export type CompileRequest = Schemas['CompileRequest'];
export type CompileResponse = Schemas['CompileResponse'];
export type RunRequest = Schemas['RunRequest'];
export type RunResponse = Schemas['RunResponse'];
export type VerifyRequest = Schemas['VerifyRequest'];
export type VerifyResponse = Schemas['VerifyResponse'];
export type SelftestResponse = Schemas['SelfTestResponse'];
export type LanguageResponse = Schemas['LanguageResponse'];
export type ExampleItem = Schemas['ExampleItem'];
export type ExampleDetail = Schemas['ExampleDetail'];
export type GrammarPresetItem = Schemas['GrammarPresetItem'];
export type GrammarPresetDetail = Schemas['GrammarPresetDetail'];
export type GrammarAnalyzeRequest = Schemas['GrammarAnalyzeRequest'];
export type GrammarAnalyzeResponse = Schemas['GrammarAnalyzeResponse'];
export type GrammarTransformRequest = Schemas['GrammarTransformRequest'];
export type GrammarTransformResponse = Schemas['GrammarTransformResponse'];
export type GrammarLL1Request = Schemas['GrammarLL1Request'];
export type GrammarLL1Response = Schemas['GrammarLL1Response'];
export type GrammarLRRequest = Schemas['GrammarLRRequest'];
export type GrammarLRResponse = Schemas['GrammarLRResponse'];
export type GrammarOpPrecedenceRequest = Schemas['GrammarOpPrecedenceRequest'];
export type GrammarOpPrecedenceResponse = Schemas['GrammarOpPrecedenceResponse'];
export type GrammarRDPseudocodeRequest = Schemas['GrammarRDPseudocodeRequest'];
export type GrammarRDPseudocodeResponse = Schemas['GrammarRDPseudocodeResponse'];
export type SDDEvaluateRequest = Schemas['SDDEvaluateRequest'];
export type SDDEvaluateResponse = Schemas['SDDEvaluateResponse'];

export class ApiError extends Error {
  status: number;
  data?: unknown;

  constructor(status: number, message: string, data?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(url, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...init?.headers,
    },
  });

  if (!resp.ok) {
    let errBody: unknown;
    try {
      errBody = await resp.json();
    } catch {
      errBody = await resp.text();
    }
    const message = typeof errBody === 'object' && errBody && 'detail' in errBody
      ? String((errBody as { detail: unknown }).detail)
      : `HTTP ${resp.status}: ${resp.statusText}`;
    throw new ApiError(resp.status, message, errBody);
  }

  return (await resp.json()) as T;
}

export const api = {
  // Health
  checkHealth: () => fetchJson<{ status: string; compiler: string; version: string }>('/api/health'),

  // Language & Specification
  getLanguage: () => fetchJson<LanguageResponse>('/api/language'),

  // Examples
  getExamples: () => fetchJson<ExampleItem[]>('/api/examples'),
  getExample: (id: string) => fetchJson<ExampleDetail>(`/api/examples/${encodeURIComponent(id)}`),

  // Compiler Pipeline
  compile: (req: CompileRequest) =>
    fetchJson<CompileResponse>('/api/compile', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  run: (req: RunRequest) =>
    fetchJson<RunResponse>('/api/run', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  verify: (req: VerifyRequest) =>
    fetchJson<VerifyResponse>('/api/verify', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  selftest: () => fetchJson<SelftestResponse>('/api/selftest'),

  // Grammar Lab
  getGrammarPresets: () => fetchJson<GrammarPresetItem[]>('/api/grammar/presets'),
  getGrammarPreset: (id: string) =>
    fetchJson<GrammarPresetDetail>(`/api/grammar/presets/${encodeURIComponent(id)}`),

  analyzeGrammar: (req: GrammarAnalyzeRequest) =>
    fetchJson<GrammarAnalyzeResponse>('/api/grammar/analyze', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  transformGrammar: (req: GrammarTransformRequest) =>
    fetchJson<GrammarTransformResponse>('/api/grammar/transform', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  ll1Grammar: (req: GrammarLL1Request) =>
    fetchJson<GrammarLL1Response>('/api/grammar/ll1', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  lrGrammar: (req: GrammarLRRequest) =>
    fetchJson<GrammarLRResponse>('/api/grammar/lr', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  opPrecedenceGrammar: (req: GrammarOpPrecedenceRequest) =>
    fetchJson<GrammarOpPrecedenceResponse>('/api/grammar/op-precedence', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  rdPseudocodeGrammar: (req: GrammarRDPseudocodeRequest) =>
    fetchJson<GrammarRDPseudocodeResponse>('/api/grammar/rd-pseudocode', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  evaluateSDD: (req: SDDEvaluateRequest) =>
    fetchJson<SDDEvaluateResponse>('/api/sdd/evaluate', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  // Documentation
  getDocs: () => fetchJson<Array<{ name: string; filename: string; title: string }>>('/api/docs'),
  getDoc: (name: string) =>
    fetchJson<{ name: string; title: string; content: string }>(`/api/docs/${encodeURIComponent(name)}`),
};
