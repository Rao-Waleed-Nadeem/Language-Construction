import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import {
  DashboardPage,
  PlaygroundPage,
  LexerPage,
  ParserPage,
  GrammarLabPage,
  SemanticPage,
  TreesPage,
  IRPage,
  OptimizerPage,
  CodeGenPage,
  VMPage,
  ReferencePage,
} from './pages';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/playground" element={<PlaygroundPage />} />
          <Route path="/lexer" element={<LexerPage />} />
          <Route path="/parser" element={<ParserPage />} />
          <Route path="/grammar-lab" element={<GrammarLabPage />} />
          <Route path="/semantic" element={<SemanticPage />} />
          <Route path="/trees" element={<TreesPage />} />
          <Route path="/ir" element={<IRPage />} />
          <Route path="/optimizer" element={<OptimizerPage />} />
          <Route path="/codegen" element={<CodeGenPage />} />
          <Route path="/vm" element={<VMPage />} />
          <Route path="/reference" element={<ReferencePage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  );
};

export default App;
