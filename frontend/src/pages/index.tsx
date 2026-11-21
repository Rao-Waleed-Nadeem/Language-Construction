import React from 'react';
import { EmptyState } from '../components/common/Feedback';

export { DashboardPage } from './DashboardPage';
export { PlaygroundPage } from './PlaygroundPage';
export { LexerPage } from './LexerPage';
export { ParserPage } from './ParserPage';
export { GrammarLabPage } from './GrammarLabPage';
export { SemanticPage } from './SemanticPage';
export { TreesPage } from './TreesPage';
export { IRPage } from './IRPage';
export { OptimizerPage } from './OptimizerPage';
export { CodeGenPage } from './CodeGenPage';
export { VMPage } from './VMPage';
export const ReferencePage: React.FC = () => <EmptyState title="Reference" description="Language manual & error catalogue" />;
