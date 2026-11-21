import { create } from 'zustand';

export interface SourceSpan {
  start_line: number;
  start_col: number;
  end_line: number;
  end_col: number;
}

interface UIState {
  hoverSpan: SourceSpan | null;
  pinnedSpan: SourceSpan | null;
  backendConnected: boolean;
  jsonDrawerData: unknown | null;
  jsonDrawerTitle: string | null;
  commandPaletteOpen: boolean;

  setHoverSpan: (span: SourceSpan | null) => void;
  setPinnedSpan: (span: SourceSpan | null) => void;
  setBackendConnected: (connected: boolean) => void;
  openJsonDrawer: (title: string, data: unknown) => void;
  closeJsonDrawer: () => void;
  setCommandPaletteOpen: (open: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
  hoverSpan: null,
  pinnedSpan: null,
  backendConnected: true,
  jsonDrawerData: null,
  jsonDrawerTitle: null,
  commandPaletteOpen: false,

  setHoverSpan: (hoverSpan) => set({ hoverSpan }),
  setPinnedSpan: (pinnedSpan) => set({ pinnedSpan }),
  setBackendConnected: (backendConnected) => set({ backendConnected }),
  openJsonDrawer: (jsonDrawerTitle, jsonDrawerData) => set({ jsonDrawerTitle, jsonDrawerData }),
  closeJsonDrawer: () => set({ jsonDrawerData: null, jsonDrawerTitle: null }),
  setCommandPaletteOpen: (commandPaletteOpen) => set({ commandPaletteOpen }),
}));
