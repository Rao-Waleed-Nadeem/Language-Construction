import React from 'react';
import { ActivityBar } from './ActivityBar';
import { TitleBar } from './TitleBar';
import { PhaseBar } from './PhaseBar';
import { StatusBar } from './StatusBar';
import { JsonDrawer } from '../common/JsonDrawer';
import { CommandPalette } from '../common/CommandPalette';
import { useUIStore } from '../../store/uiStore';
import { AlertOctagon, RefreshCw } from 'lucide-react';
import { api } from '../../api/client';

export const AppShell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { backendConnected, setBackendConnected } = useUIStore();

  const handleRetryConnection = async () => {
    try {
      await api.checkHealth();
      setBackendConnected(true);
    } catch {
      setBackendConnected(false);
    }
  };

  return (
    <div className="flex h-screen w-screen bg-bg-0 text-text-0 overflow-hidden font-sans">
      {/* 48px Activity bar */}
      <ActivityBar />

      {/* Main workbench body */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Title bar */}
        <TitleBar />

        {/* Pipeline stage bar */}
        <PhaseBar />

        {/* Backend unreachable banner */}
        {!backendConnected && (
          <div className="bg-err/15 border-b border-err/30 px-4 py-2 flex items-center justify-between text-xs text-err font-medium z-30">
            <div className="flex items-center gap-2">
              <AlertOctagon className="w-4 h-4 flex-shrink-0" />
              <span>
                Cannot reach the Vela backend at 127.0.0.1:8000 — ensure the server is running with{' '}
                <code className="px-1 py-0.5 bg-bg-0 border border-border rounded">powershell -File .\scripts\start.ps1</code>
              </span>
            </div>
            <button
              onClick={handleRetryConnection}
              className="flex items-center gap-1 px-2.5 py-0.5 bg-err/20 hover:bg-err/30 border border-err/40 rounded text-xs transition-colors"
            >
              <RefreshCw className="w-3 h-3" />
              Retry
            </button>
          </div>
        )}

        {/* Page content view */}
        <main className="flex-1 overflow-hidden relative bg-bg-0">
          {children}
        </main>

        {/* Status bar */}
        <StatusBar />
      </div>

      {/* Global Modals & Drawers */}
      <JsonDrawer />
      <CommandPalette />
    </div>
  );
};
