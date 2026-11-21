import React, { useEffect, useRef } from 'react';
import Editor, { type OnMount, type Monaco } from '@monaco-editor/react';
import type { editor } from 'monaco-editor';
import { velaLanguageDefinition } from '../../features/editor/monarch';
import { useUIStore, type SourceSpan } from '../../store/uiStore';

interface SourceViewProps {
  source: string;
  readOnly?: boolean;
  onChange?: (value: string) => void;
  activeSpan?: SourceSpan | null;
  className?: string;
  height?: string;
}

export const SourceView: React.FC<SourceViewProps> = ({
  source,
  readOnly = false,
  onChange,
  activeSpan,
  className = '',
  height = '100%',
}) => {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const monacoRef = useRef<Monaco | null>(null);
  const decorationsRef = useRef<string[]>([]);

  const { hoverSpan, pinnedSpan, setHoverSpan, setPinnedSpan } = useUIStore();

  const handleEditorDidMount: OnMount = (ed, monaco) => {
    editorRef.current = ed;
    monacoRef.current = monaco;

    // Register Vela language if not already registered
    if (!monaco.languages.getLanguages().some((l: { id: string }) => l.id === 'vela')) {
      monaco.languages.register({ id: 'vela' });
      monaco.languages.setMonarchTokensProvider('vela', velaLanguageDefinition);
      monaco.languages.setLanguageConfiguration('vela', {
        comments: {
          lineComment: '//',
          blockComment: ['/*', '*/'],
        },
        brackets: [
          ['{', '}'],
          ['[', ']'],
          ['(', ')'],
        ],
        autoClosingPairs: [
          { open: '{', close: '}' },
          { open: '[', close: ']' },
          { open: '(', close: ')' },
          { open: '"', close: '"' },
          { open: "'", close: "'" },
        ],
      });
    }

    // Set custom dark theme matching design tokens
    monaco.editor.defineTheme('vela-dark', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'keyword', foreground: 'c792ea', fontStyle: 'bold' },
        { token: 'type.identifier', foreground: '82aaff' },
        { token: 'identifier', foreground: 'e6e9ef' },
        { token: 'number', foreground: 'f78c6c' },
        { token: 'number.float', foreground: 'f78c6c' },
        { token: 'string', foreground: 'c3e88d' },
        { token: 'string.char', foreground: 'c3e88d' },
        { token: 'comment', foreground: '5c6773', fontStyle: 'italic' },
        { token: 'operator', foreground: '89ddff' },
        { token: 'delimiter', foreground: '9aa4b5' },
      ],
      colors: {
        'editor.background': '#0b0e14',
        'editor.foreground': '#e6e9ef',
        'editorLineNumber.foreground': '#252c3a',
        'editorLineNumber.activeForeground': '#9aa4b5',
        'editor.lineHighlightBackground': '#11151d',
        'editor.selectionBackground': '#252c3a',
        'editorCursor.foreground': '#5eead4',
      },
    });

    monaco.editor.setTheme('vela-dark');

    // Hover listener
    ed.onMouseMove((e) => {
      if (e.target.position) {
        // Can be used to inspect token
      }
    });

    // Escape clears pin
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        setPinnedSpan(null);
        setHoverSpan(null);
      }
    });
  };

  // Update highlight decorations when hoverSpan, pinnedSpan, or activeSpan change
  useEffect(() => {
    const ed = editorRef.current;
    const monaco = monacoRef.current;
    if (!ed || !monaco) return;

    const targetSpan = hoverSpan || pinnedSpan || activeSpan;

    if (targetSpan) {
      const newDecorations: editor.IModelDeltaDecoration[] = [
        {
          range: new monaco.Range(
            targetSpan.start_line,
            targetSpan.start_col,
            targetSpan.end_line,
            targetSpan.end_col
          ),
          options: {
            isWholeLine: false,
            className: 'bg-accent/25 border-b-2 border-accent',
            inlineClassName: 'bg-accent/25 rounded px-0.5',
            marginClassName: 'bg-accent',
          },
        },
      ];

      decorationsRef.current = ed.deltaDecorations(decorationsRef.current, newDecorations);

      // Scroll into view if pinned
      if (pinnedSpan) {
        ed.revealRangeInCenterIfOutsideViewport(
          new monaco.Range(
            targetSpan.start_line,
            targetSpan.start_col,
            targetSpan.end_line,
            targetSpan.end_col
          )
        );
      }
    } else {
      decorationsRef.current = ed.deltaDecorations(decorationsRef.current, []);
    }
  }, [hoverSpan, pinnedSpan, activeSpan]);

  return (
    <div className={`relative w-full h-full border border-border rounded-lg overflow-hidden ${className}`}>
      <Editor
        height={height}
        language="vela"
        theme="vela-dark"
        value={source}
        options={{
          readOnly,
          minimap: { enabled: false },
          fontSize: 13,
          fontFamily: '"JetBrains Mono", Consolas, Monaco, monospace',
          lineNumbers: 'on',
          scrollBeyondLastLine: false,
          automaticLayout: true,
          tabSize: 4,
          insertSpaces: true,
          renderLineHighlight: 'all',
          cursorBlinking: 'smooth',
          bracketPairColorization: { enabled: true },
        }}
        onChange={(val) => onChange?.(val || '')}
        onMount={handleEditorDidMount}
      />
    </div>
  );
};
