import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  PlaySquare,
  Binary,
  GitCommit,
  FlaskConical,
  CheckCircle2,
  Network,
  Cpu,
  Zap,
  HardDrive,
  Terminal,
  BookOpen,
} from 'lucide-react';

interface NavItem {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/playground', label: 'Playground', icon: PlaySquare },
  { to: '/lexer', label: 'Lexer Explorer', icon: Binary },
  { to: '/parser', label: 'Parser Explorer', icon: GitCommit },
  { to: '/grammar-lab', label: 'Grammar Lab', icon: FlaskConical },
  { to: '/semantic', label: 'Semantic Analysis', icon: CheckCircle2 },
  { to: '/trees', label: 'AST & DAG Trees', icon: Network },
  { to: '/ir', label: 'Intermediate Code', icon: Cpu },
  { to: '/optimizer', label: 'Optimization Lab', icon: Zap },
  { to: '/codegen', label: 'Target CodeGen', icon: HardDrive },
  { to: '/vm', label: 'Virtual Machine', icon: Terminal },
  { to: '/reference', label: 'Documentation', icon: BookOpen },
];

export const ActivityBar: React.FC = () => {
  return (
    <aside className="w-12 h-full bg-bg-1 border-r border-border flex flex-col items-center py-2 z-20 flex-shrink-0 select-none">
      {/* Top logo mark */}
      <div className="w-8 h-8 rounded bg-accent/10 border border-accent/40 flex items-center justify-center text-accent font-bold font-mono text-sm mb-3">
        V
      </div>

      {/* Nav items */}
      <nav className="flex-1 flex flex-col gap-1 w-full px-1.5 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              title={item.label}
              className={({ isActive }) =>
                `w-9 h-9 rounded flex items-center justify-center transition-colors relative group ${
                  isActive
                    ? 'bg-bg-2 text-accent border border-accent/40 shadow-sm'
                    : 'text-text-1 hover:text-text-0 hover:bg-bg-2'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon className="w-4 h-4" />
                  {isActive && (
                    <div className="absolute left-0 top-1.5 bottom-1.5 w-0.5 bg-accent rounded-r" />
                  )}
                  {/* Tooltip on hover */}
                  <div className="absolute left-11 px-2 py-1 bg-bg-2 text-text-0 border border-border rounded text-[11px] font-medium whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity shadow-lg z-50">
                    {item.label}
                  </div>
                </>
              )}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
};
