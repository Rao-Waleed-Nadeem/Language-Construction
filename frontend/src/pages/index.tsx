import React from 'react';
import { EmptyState } from '../components/common/Feedback';

export const DashboardPage: React.FC = () => <EmptyState title="Dashboard" description="Overview & quickstart" />;
export const PlaygroundPage: React.FC = () => <EmptyState title="Playground" description="Code editor & console" />;
export const LexerPage: React.FC = () => <EmptyState title="Lexer Explorer" description="Tokens, DFAs & scanner" />;
export const ParserPage: React.FC = () => <EmptyState title="Parser Explorer" description="LL(1) parse tree & trace" />;
export const GrammarLabPage: React.FC = () => <EmptyState title="Grammar Lab" description="Grammar analysis & parsing lab" />;
export const SemanticPage: React.FC = () => <EmptyState title="Semantic Analysis" description="Type checks & symbol tables" />;
export const TreesPage: React.FC = () => <EmptyState title="AST & DAG" description="Abstract syntax tree & expression DAG" />;
export const IRPage: React.FC = () => <EmptyState title="Intermediate Code" description="TAC, blocks & control flow graph" />;
export const OptimizerPage: React.FC = () => <EmptyState title="Optimizer Lab" description="Optimization passes & diffs" />;
export const CodeGenPage: React.FC = () => <EmptyState title="Target CodeGen" description="Target ISA & register allocation" />;
export const VMPage: React.FC = () => <EmptyState title="Virtual Machine" description="Execution simulator & state inspection" />;
export const ReferencePage: React.FC = () => <EmptyState title="Reference" description="Language manual & error catalogue" />;
