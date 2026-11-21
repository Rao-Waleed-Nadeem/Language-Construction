import React from 'react';

export const App: React.FC = () => {
  return (
    <div className="flex h-screen w-screen flex-col bg-[#0d1117] text-zinc-100">
      <header className="flex h-10 items-center justify-between border-b border-[#30363d] px-4">
        <div className="flex items-center gap-2">
          <span className="font-bold tracking-wide text-blue-400">VELA STUDIO</span>
          <span className="text-xs text-zinc-400">CS 4031 Compiler Construction</span>
        </div>
      </header>
      <main className="flex-1 p-6">
        <h1 className="text-xl font-semibold">Vela Compiler & IDE Workbench</h1>
        <p className="mt-2 text-sm text-zinc-400">Workspace initialized successfully.</p>
      </main>
    </div>
  );
};
