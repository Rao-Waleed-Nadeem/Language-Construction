import React from 'react';
import { EmptyState } from '../components/common/Feedback';

export { DashboardPage } from './DashboardPage';
export { PlaygroundPage } from './PlaygroundPage';
export { LexerPage } from './LexerPage';
export { ParserPage } from './ParserPage';
export { GrammarLabPage } from './GrammarLabPage';
export { SemanticPage } from './SemanticPage';
export { TreesPage } from './TreesPage';
export const IRPage: React.FC = () => <EmptyState title="Intermediate Code" description="TAC, blocks & control flow graph" />;
export const OptimizerPage: React.FC = () => <EmptyState title="Optimizer Lab" description="Optimization passes & diffs" />;
export const CodeGenPage: React.FC = () => <EmptyState title="Target CodeGen" description="Target ISA & register allocation" />;
export const VMPage: React.FC = () => <EmptyState title="Virtual Machine" description="Execution simulator & state inspection" />;
export const ReferencePage: React.FC = () => <EmptyState title="Reference" description="Language manual & error catalogue" />;
