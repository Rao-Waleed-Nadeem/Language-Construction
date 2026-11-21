import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BookOpen,
  Code,
  AlertTriangle,
  FolderOpen,
  FileText,
  Search,
  ExternalLink,
  Layers,
} from 'lucide-react';
import { api, type LanguageResponse, type ExampleItem } from '../api/client';
import { useCompileStore } from '../store/compileStore';
import { BadgeUsedByCompiler } from '../components/common/Badge';

interface ErrorEntry {
  code: string;
  category: 'Lexical' | 'Syntax' | 'Limit' | 'Semantic' | 'Runtime' | 'Warning';
  meaning: string;
  reportedAt: string;
  sampleInvalid: string;
  fix: string;
}

const ERROR_CATALOGUE: ErrorEntry[] = [
  // Lexical Errors
  {
    code: 'VL-LEX-001',
    category: 'Lexical',
    meaning: 'invalid character',
    reportedAt: 'the character',
    sampleInvalid: 'let x: int = @5;',
    fix: 'Remove or replace illegal non-ASCII or unsupported characters.',
  },
  {
    code: 'VL-LEX-002',
    category: 'Lexical',
    meaning: 'unterminated string literal',
    reportedAt: 'opening quote',
    sampleInvalid: 'let s: string = "hello;',
    fix: 'Close the string literal before the end of the line with a closing double quote (").',
  },
  {
    code: 'VL-LEX-003',
    category: 'Lexical',
    meaning: 'unterminated char literal',
    reportedAt: 'opening quote',
    sampleInvalid: "let c: char = 'a;",
    fix: "Close the char literal with a closing single quote (').",
  },
  {
    code: 'VL-LEX-004',
    category: 'Lexical',
    meaning: 'empty char literal',
    reportedAt: "the ''",
    sampleInvalid: "let c: char = '';",
    fix: 'Provide exactly one character inside the single quotes, e.g. \'a\' or \'\\0\'.',
  },
  {
    code: 'VL-LEX-005',
    category: 'Lexical',
    meaning: 'char literal has more than one character',
    reportedAt: 'opening quote',
    sampleInvalid: "let c: char = 'ab';",
    fix: 'Use a string literal ("ab") for multiple characters or keep a single character.',
  },
  {
    code: 'VL-LEX-006',
    category: 'Lexical',
    meaning: 'invalid escape sequence',
    reportedAt: 'the backslash',
    sampleInvalid: 'let s: string = "bad \\k escape";',
    fix: 'Use standard escape sequences: \\n, \\t, \\r, \\0, \\\\, \\\', \\".',
  },
  {
    code: 'VL-LEX-007',
    category: 'Lexical',
    meaning: 'unterminated block comment',
    reportedAt: 'the /*',
    sampleInvalid: '/* unclosed comment func main() {}',
    fix: 'Close the block comment with */ before the end of the file.',
  },
  {
    code: 'VL-LEX-008',
    category: 'Lexical',
    meaning: 'malformed number',
    reportedAt: 'start of the number',
    sampleInvalid: 'let x: int = 12abc;',
    fix: 'Separate numeric literal from subsequent identifier with a space or operator.',
  },
  {
    code: 'VL-LEX-009',
    category: 'Lexical',
    meaning: 'integer literal out of range',
    reportedAt: 'the literal',
    sampleInvalid: 'let x: int = 99999999999999999999;',
    fix: 'Keep integer values within signed 32-bit limits (-2,147,483,648 to 2,147,483,647).',
  },
  {
    code: 'VL-LEX-010',
    category: 'Lexical',
    meaning: 'identifier longer than 64 characters',
    reportedAt: 'the identifier',
    sampleInvalid: 'let aVeryLongIdentifierNameExceedingTheSixtyFourCharacterLimitPrescribedInSpec: int = 1;',
    fix: 'Shorten the identifier name to 64 characters or fewer.',
  },
  {
    code: 'VL-LEX-011',
    category: 'Lexical',
    meaning: 'char literal outside Latin-1 (code > 255)',
    reportedAt: 'the literal',
    sampleInvalid: "let c: char = '€';",
    fix: 'Vela char literals must have codepoints in the Latin-1 range (≤ 255).',
  },

  // Syntax Errors
  {
    code: 'VL-SYN-001',
    category: 'Syntax',
    meaning: 'unexpected token (message names what was expected)',
    reportedAt: 'the unexpected token',
    sampleInvalid: 'func main() { let x = 5; }',
    fix: 'Provide the expected syntax, e.g. explicit type annotation `let x: int = 5;`.',
  },
  {
    code: 'VL-SYN-002',
    category: 'Syntax',
    meaning: 'unexpected end of file',
    reportedAt: 'the EOF position',
    sampleInvalid: 'func main() {',
    fix: 'Ensure all opened braces, parentheses, and brackets are matched and closed.',
  },
  {
    code: 'VL-SYN-003',
    category: 'Syntax',
    meaning: 'nesting too deep (> 200)',
    reportedAt: 'the token that exceeded it',
    sampleInvalid: '((((... 201 times ...))))',
    fix: 'Refactor deeply nested blocks or parenthesized expressions to stay within 200 levels.',
  },

  // Limits
  {
    code: 'VL-LIM-001',
    category: 'Limit',
    meaning: 'more than 50,000 tokens (compiler limit; scan stops)',
    reportedAt: 'the first token over the limit',
    sampleInvalid: '50,001 tokens in a single translation unit',
    fix: 'Split large translation units or reduce program size below 50,000 tokens.',
  },

  // Semantic Errors
  {
    code: 'VL-SEM-001',
    category: 'Semantic',
    meaning: 'undeclared variable',
    reportedAt: 'the identifier',
    sampleInvalid: 'func main() { show y; }',
    fix: 'Declare variables before using them: `let y: int = 10;`.',
  },
  {
    code: 'VL-SEM-002',
    category: 'Semantic',
    meaning: 'redeclaration in the same scope',
    reportedAt: 'the new name',
    sampleInvalid: 'func main() { let x: int = 1; let x: int = 2; }',
    fix: 'Use distinct variable names within the same block scope.',
  },
  {
    code: 'VL-SEM-003',
    category: 'Semantic',
    meaning: 'type mismatch in initialization/assignment',
    reportedAt: 'the value expression',
    sampleInvalid: 'func main() { let x: int = "hello"; }',
    fix: 'Assign values matching the declared variable type.',
  },
  {
    code: 'VL-SEM-004',
    category: 'Semantic',
    meaning: 'invalid operand types for operator',
    reportedAt: 'the operator',
    sampleInvalid: 'func main() { let s: string = "a" - "b"; }',
    fix: 'Use operators only with permitted types (e.g. + for string concatenation, not -).',
  },
  {
    code: 'VL-SEM-005',
    category: 'Semantic',
    meaning: 'condition is not bool',
    reportedAt: 'the condition expression',
    sampleInvalid: 'func main() { if 42 { show 1; } }',
    fix: 'Ensure if/while loop conditions evaluate to boolean expressions (e.g. `x != 0`).',
  },
  {
    code: 'VL-SEM-006',
    category: 'Semantic',
    meaning: 'call to undeclared function / name is not a function',
    reportedAt: 'the callee name',
    sampleInvalid: 'func main() { foo(); }',
    fix: 'Define the function before invoking it or check the identifier spelling.',
  },
  {
    code: 'VL-SEM-007',
    category: 'Semantic',
    meaning: 'wrong number of arguments',
    reportedAt: 'the callee name',
    sampleInvalid: 'func add(a: int, b: int) -> int { return a + b; }\nfunc main() { add(1); }',
    fix: 'Pass arguments matching the function parameter count.',
  },
  {
    code: 'VL-SEM-008',
    category: 'Semantic',
    meaning: 'argument type mismatch',
    reportedAt: 'the argument',
    sampleInvalid: 'func f(x: int) {}\nfunc main() { f("test"); }',
    fix: 'Pass argument expressions matching parameter types.',
  },
  {
    code: 'VL-SEM-009',
    category: 'Semantic',
    meaning: 'return value/type mismatch',
    reportedAt: 'the returned expression (or return)',
    sampleInvalid: 'func f() { return 10; }',
    fix: 'Return values only when a return type is specified, or omit the return value in void functions.',
  },
  {
    code: 'VL-SEM-010',
    category: 'Semantic',
    meaning: 'missing return on some path',
    reportedAt: 'the function name',
    sampleInvalid: 'func f(x: int) -> int { if x > 0 { return 1; } }',
    fix: 'Ensure all execution branches terminate with a return statement.',
  },
  {
    code: 'VL-SEM-011',
    category: 'Semantic',
    meaning: 'break/continue outside a valid construct',
    reportedAt: 'the keyword',
    sampleInvalid: 'func main() { break; }',
    fix: 'Use break and continue statements only inside loop bodies or switch cases.',
  },
  {
    code: 'VL-SEM-012',
    category: 'Semantic',
    meaning: 'duplicate case label',
    reportedAt: 'the duplicate label',
    sampleInvalid: 'switch x { case 1: break; case 1: break; }',
    fix: 'Ensure all case constants within a switch statement are unique.',
  },
  {
    code: 'VL-SEM-013',
    category: 'Semantic',
    meaning: 'switch expression not int/char, or label type mismatch',
    reportedAt: 'the switch expression / the label',
    sampleInvalid: 'switch "test" { case "a": break; }',
    fix: 'Switch expressions and case labels must be integer or character literals.',
  },
  {
    code: 'VL-SEM-014',
    category: 'Semantic',
    meaning: 'array index not int',
    reportedAt: 'the index',
    sampleInvalid: 'let a: int[5]; let v: int = a[2.5];',
    fix: 'Use integer values or variables for indexing arrays.',
  },
  {
    code: 'VL-SEM-015',
    category: 'Semantic',
    meaning: 'indexing a non-array',
    reportedAt: 'the identifier',
    sampleInvalid: 'let x: int = 5; let y: int = x[0];',
    fix: 'Apply subscript brackets [] only to variables declared as arrays.',
  },
  {
    code: 'VL-SEM-016',
    category: 'Semantic',
    meaning: 'too many array initializers',
    reportedAt: 'first extra initializer',
    sampleInvalid: 'let a: int[2] = [1, 2, 3];',
    fix: 'Provide at most N initializer elements for an array of size N.',
  },
  {
    code: 'VL-SEM-017',
    category: 'Semantic',
    meaning: 'invalid array size (not 1..10,000)',
    reportedAt: 'the size literal',
    sampleInvalid: 'let a: int[0];',
    fix: 'Array sizes must be constant integer literals between 1 and 10,000.',
  },
  {
    code: 'VL-SEM-018',
    category: 'Semantic',
    meaning: 'missing/ill-formed main',
    reportedAt: '1:1 (or the main name)',
    sampleInvalid: 'func start() {}',
    fix: 'Define exactly one `func main()` without parameters or return type.',
  },
  {
    code: 'VL-SEM-019',
    category: 'Semantic',
    meaning: 'invalid as conversion',
    reportedAt: 'the as keyword',
    sampleInvalid: 'let x: int = "hello" as int;',
    fix: 'Cast only allowed types: int <-> float, int <-> char, char <-> int.',
  },
  {
    code: 'VL-SEM-020',
    category: 'Semantic',
    meaning: 'global initializer not a literal',
    reportedAt: 'the initializer',
    sampleInvalid: 'let g: int = 2 + 3;',
    fix: 'Global variables must be initialized with literal constants.',
  },
  {
    code: 'VL-SEM-021',
    category: 'Semantic',
    meaning: 'array used as a value',
    reportedAt: 'the array name',
    sampleInvalid: 'let a: int[2]; let b: int[2] = a;',
    fix: 'Vela arrays cannot be assigned as whole values; access elements individually.',
  },
  {
    code: 'VL-SEM-022',
    category: 'Semantic',
    meaning: 'constant index out of range',
    reportedAt: 'the index',
    sampleInvalid: 'let a: int[3]; show a[5];',
    fix: 'Keep constant indices strictly within 0 <= index < size.',
  },
  {
    code: 'VL-SEM-023',
    category: 'Semantic',
    meaning: 'void function used as a value',
    reportedAt: 'the callee name',
    sampleInvalid: 'func log() {}\nfunc main() { let x: int = log(); }',
    fix: 'Do not assign or evaluate void function invocations inside expressions.',
  },

  // Runtime Errors
  {
    code: 'VL-RUN-001',
    category: 'Runtime',
    meaning: 'division or modulo by zero',
    reportedAt: 'the operator',
    sampleInvalid: 'let z: int = 0; show 10 / z;',
    fix: 'Verify divisor is non-zero before performing division or modulo operations.',
  },
  {
    code: 'VL-RUN-002',
    category: 'Runtime',
    meaning: 'array index out of bounds',
    reportedAt: 'the indexing expression',
    sampleInvalid: 'let a: int[3]; let i: int = 3; show a[i];',
    fix: 'Ensure dynamic array indices stay within [0, size - 1].',
  },
  {
    code: 'VL-RUN-003',
    category: 'Runtime',
    meaning: 'input exhausted',
    reportedAt: 'the read',
    sampleInvalid: 'read x; // with empty stdin',
    fix: 'Provide sufficient input in stdin before reading.',
  },
  {
    code: 'VL-RUN-004',
    category: 'Runtime',
    meaning: 'invalid input format',
    reportedAt: 'the read',
    sampleInvalid: 'read x; // with "abc" for int',
    fix: 'Ensure input stream matches the target variable data type.',
  },
  {
    code: 'VL-RUN-005',
    category: 'Runtime',
    meaning: 'conversion out of range',
    reportedAt: 'the as',
    sampleInvalid: 'let c: char = 300 as char;',
    fix: 'Ensure values cast to char fit within [0, 255].',
  },
  {
    code: 'VL-RUN-006',
    category: 'Runtime',
    meaning: 'call stack overflow (depth > 1000)',
    reportedAt: 'the call',
    sampleInvalid: 'func f() { f(); }\nfunc main() { f(); }',
    fix: 'Provide base cases to terminate recursive calls.',
  },
  {
    code: 'VL-RUN-007',
    category: 'Runtime',
    meaning: 'instruction budget exceeded',
    reportedAt: 'current statement',
    sampleInvalid: 'while true {}',
    fix: 'Ensure loops terminate within the 100,000 instruction budget.',
  },
  {
    code: 'VL-RUN-008',
    category: 'Runtime',
    meaning: 'output limit exceeded',
    reportedAt: 'the show',
    sampleInvalid: 'for i in 0..100000 { show i; }',
    fix: 'Keep program output within the 64KB stdout limit.',
  },

  // Warnings
  {
    code: 'VL-WRN-001',
    category: 'Warning',
    meaning: 'unused local variable (warning, P2)',
    reportedAt: 'the declaration',
    sampleInvalid: 'func main() { let unused: int = 10; }',
    fix: 'Use the variable or remove the unused declaration.',
  },
];

const GRAMMAR_VERIFIED_PROPERTIES = [
  { property: 'LL(1) (Original Grammar G)', result: 'False', note: 'Contains left-factoring and dangling else ambiguity' },
  { property: 'LL(1) (Transformed Grammar G\')', result: 'True', note: 'After Algorithm 4.19 left-recursion elimination & 4.22 left factoring' },
  { property: 'LR(0)', result: 'False', note: 'Has shift-reduce conflicts in expression and statement rules' },
  { property: 'SLR(1)', result: 'True', note: 'All conflicts resolved using FOLLOW sets' },
  { property: 'LALR(1)', result: 'True', note: 'Merged core states produce 0 conflict states' },
  { property: 'CLR(1) / Canonical LR(1)', result: 'True', note: 'Fully deterministic LR(1) parse table' },
  { property: 'Operator Precedence', result: 'True', note: 'Valid leading/trailing precedence relations matrix' },
  { property: 'Chomsky Hierarchy Classification', result: 'Type-2 Context-Free', note: 'All productions have single non-terminal on LHS' },
];

export const ReferencePage: React.FC = () => {
  const navigate = useNavigate();
  const { setSource } = useCompileStore();

  const [activeSection, setActiveSection] = useState<'tour' | 'grammar' | 'errors' | 'examples' | 'docs'>('tour');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [languageData, setLanguageData] = useState<LanguageResponse | null>(null);
  const [examplesList, setExamplesList] = useState<ExampleItem[]>([]);
  const [docsList, setDocsList] = useState<Array<{ name: string; filename: string; title: string }>>([]);
  const [selectedDoc, setSelectedDoc] = useState<string>('00_PROJECT_MASTER_SPEC');
  const [docContent, setDocContent] = useState<string>('');

  useEffect(() => {
    // Load language specification
    api.getLanguage().then(setLanguageData).catch(() => {});
    // Load examples list
    api.getExamples().then(setExamplesList).catch(() => {});
    // Load docs list
    api.getDocs().then((docs) => {
      setDocsList(docs);
      if (docs.length > 0) {
        setSelectedDoc(docs[0].name);
      }
    }).catch(() => {});
  }, []);

  // Fetch document content when selectedDoc changes
  useEffect(() => {
    if (activeSection === 'docs' && selectedDoc) {
      api.getDoc(selectedDoc).then((res) => setDocContent(res.content)).catch(() => {});
    }
  }, [activeSection, selectedDoc]);

  // Client-side search across error catalogue
  const filteredErrors = ERROR_CATALOGUE.filter((err) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      err.code.toLowerCase().includes(q) ||
      err.meaning.toLowerCase().includes(q) ||
      err.sampleInvalid.toLowerCase().includes(q) ||
      err.fix.toLowerCase().includes(q)
    );
  });

  // Client-side search across examples
  const filteredExamples = examplesList.filter((ex) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return ex.title.toLowerCase().includes(q) || (ex.description && ex.description.toLowerCase().includes(q));
  });

  const handleOpenInPlayground = async (exId: string) => {
    try {
      const detail = await api.getExample(exId);
      setSource(detail.source);
      navigate('/playground');
    } catch {
      // Fallback
      navigate('/playground');
    }
  };

  return (
    <div className="h-full flex bg-bg-0 overflow-hidden font-sans">
      {/* LEFT SIDEBAR: Table of Contents & Search */}
      <div className="w-72 border-r border-border bg-bg-1 flex flex-col overflow-hidden select-none">
        {/* Top Header */}
        <div className="p-3 bg-bg-2 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-xs text-text-0">
            <BookOpen className="w-4 h-4 text-accent" />
            <span>Vela Reference Manual</span>
          </div>
          <BadgeUsedByCompiler />
        </div>

        {/* Global Search Box (AC-R4) */}
        <div className="p-2 border-b border-border bg-bg-0">
          <div className="relative flex items-center">
            <Search className="w-3.5 h-3.5 text-text-1 absolute left-2 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search reference (e.g. dangling)..."
              className="w-full bg-bg-1 border border-border text-text-0 pl-7 pr-2 py-1 text-xs rounded outline-none placeholder:text-text-1 focus:border-accent"
            />
          </div>
        </div>

        {/* Navigation Sections */}
        <div className="flex-1 overflow-auto p-2 space-y-1 text-xs">
          <button
            onClick={() => setActiveSection('tour')}
            className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg transition-colors text-left ${
              activeSection === 'tour'
                ? 'bg-accent/15 text-accent font-semibold'
                : 'text-text-1 hover:text-text-0 hover:bg-bg-2'
            }`}
          >
            <Code className="w-4 h-4" />
            <span>Language Tour & Spec</span>
          </button>

          <button
            onClick={() => setActiveSection('grammar')}
            className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg transition-colors text-left ${
              activeSection === 'grammar'
                ? 'bg-accent/15 text-accent font-semibold'
                : 'text-text-1 hover:text-text-0 hover:bg-bg-2'
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>Grammar & Theory (G & G')</span>
          </button>

          <button
            onClick={() => setActiveSection('errors')}
            className={`w-full flex items-center justify-between px-3 py-2 rounded-lg transition-colors text-left ${
              activeSection === 'errors'
                ? 'bg-accent/15 text-accent font-semibold'
                : 'text-text-1 hover:text-text-0 hover:bg-bg-2'
            }`}
          >
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              <span>Error Catalogue</span>
            </div>
            <span className="px-1.5 py-0.2 rounded text-[10px] bg-bg-2 border border-border text-text-1">
              47 codes
            </span>
          </button>

          <button
            onClick={() => setActiveSection('examples')}
            className={`w-full flex items-center justify-between px-3 py-2 rounded-lg transition-colors text-left ${
              activeSection === 'examples'
                ? 'bg-accent/15 text-accent font-semibold'
                : 'text-text-1 hover:text-text-0 hover:bg-bg-2'
            }`}
          >
            <div className="flex items-center gap-2">
              <FolderOpen className="w-4 h-4" />
              <span>Examples Library</span>
            </div>
            <span className="px-1.5 py-0.2 rounded text-[10px] bg-bg-2 border border-border text-text-1">
              {examplesList.length}
            </span>
          </button>

          <button
            onClick={() => setActiveSection('docs')}
            className={`w-full flex items-center justify-between px-3 py-2 rounded-lg transition-colors text-left ${
              activeSection === 'docs'
                ? 'bg-accent/15 text-accent font-semibold'
                : 'text-text-1 hover:text-text-0 hover:bg-bg-2'
            }`}
          >
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4" />
              <span>Specifications & Specs</span>
            </div>
            <span className="px-1.5 py-0.2 rounded text-[10px] bg-bg-2 border border-border text-text-1">
              {docsList.length} docs
            </span>
          </button>
        </div>
      </div>

      {/* RIGHT CONTENT AREA: Active Section Content */}
      <div className="flex-1 flex flex-col overflow-hidden bg-bg-0">
        {/* SECTION 1: Language Tour */}
        {activeSection === 'tour' && (
          <div className="flex-1 overflow-auto p-6 space-y-6 max-w-4xl">
            <div>
              <h1 className="text-xl font-bold text-text-0">Vela Language Tour</h1>
              <p className="text-xs text-text-1 pt-1">
                Authoritative language specification, keywords, types, and operator precedence tables loaded directly from
                the compiler core.
              </p>
            </div>

            {/* Keywords Table (AC-R1) */}
            <div className="space-y-2">
              <h2 className="text-sm font-bold text-text-0">1. Keywords (26 Reserved Words)</h2>
              <div className="p-3 bg-bg-1 border border-border rounded-lg flex flex-wrap gap-1.5 font-mono text-xs">
                {languageData?.keywords?.map((kw) => (
                  <span
                    key={kw}
                    className="px-2 py-0.5 rounded bg-bg-2 border border-border text-accent font-semibold"
                  >
                    {kw}
                  </span>
                )) || <span className="text-text-1">Loading keywords...</span>}
              </div>
            </div>

            {/* Operator Precedence Table (AC-R1) */}
            <div className="space-y-2">
              <h2 className="text-sm font-bold text-text-0">2. Operator Precedence & Associativity Table</h2>
              <div className="border border-border rounded-lg overflow-hidden font-mono text-xs">
                <table className="w-full text-left">
                  <thead className="bg-bg-2 border-b border-border text-[11px] text-text-1">
                    <tr>
                      <th className="p-2.5">Level</th>
                      <th className="p-2.5">Operators</th>
                      <th className="p-2.5">Description</th>
                      <th className="p-2.5">Associativity</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border bg-bg-1">
                    {languageData?.precedence?.map((p: any) => (
                      <tr key={p.level} className="hover:bg-bg-2/50">
                        <td className="p-2.5 font-bold text-accent">{p.level}</td>
                        <td className="p-2.5 text-text-0 font-bold">{p.operators?.join('  ')}</td>
                        <td className="p-2.5 text-text-1 font-sans">{p.description}</td>
                        <td className="p-2.5 text-ok">{p.associativity}</td>
                      </tr>
                    )) || (
                      <tr>
                        <td colSpan={4} className="p-4 text-center text-text-1">
                          Loading precedence table...
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Scoping Rules & Types */}
            <div className="space-y-2">
              <h2 className="text-sm font-bold text-text-0">3. Built-In Types & Scoping</h2>
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div className="p-3 bg-bg-1 border border-border rounded-lg space-y-1.5">
                  <div className="font-bold text-text-0">Primitive Types:</div>
                  <div className="text-text-1 space-y-1 font-mono text-[11px]">
                    <div><span className="text-accent font-bold">int</span>: 32-bit signed two's complement integer</div>
                    <div><span className="text-accent font-bold">float</span>: IEEE 754 single-precision float</div>
                    <div><span className="text-accent font-bold">char</span>: 8-bit Latin-1 character (code &le; 255)</div>
                    <div><span className="text-accent font-bold">bool</span>: Boolean value (true or false)</div>
                    <div><span className="text-accent font-bold">string</span>: Immutable UTF-8 text string</div>
                    <div><span className="text-accent font-bold">T[N]</span>: Fixed-size homogeneous array of N elements</div>
                  </div>
                </div>

                <div className="p-3 bg-bg-1 border border-border rounded-lg space-y-1.5">
                  <div className="font-bold text-text-0">Lexical Scoping Rules:</div>
                  <div className="text-text-1 space-y-1 text-[11px]">
                    <div>• Block-scoped variables with shadowing permitted in nested blocks.</div>
                    <div>• No redeclarations within the same scope (VL-SEM-002).</div>
                    <div>• Global scope variables must be initialized with compile-time literals.</div>
                    <div>• Exactly one entry point required: <code>func main()</code> (VL-SEM-018).</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* SECTION 2: Grammar & Parsing Theory */}
        {activeSection === 'grammar' && (
          <div className="flex-1 overflow-auto p-6 space-y-6 max-w-4xl text-xs">
            <div>
              <h1 className="text-xl font-bold text-text-0">Vela Formal Grammar & Parsing Properties</h1>
              <p className="text-xs text-text-1 pt-1">
                Verified properties of the authoritative grammar <code>G</code> and transformed LL(1) grammar <code>G'</code>.
              </p>
            </div>

            {/* Verified Properties Table (doc 01 §13.4) */}
            <div className="space-y-2">
              <h2 className="text-sm font-bold text-text-0">Verified Grammatical Properties (doc 01 §13.4)</h2>
              <div className="border border-border rounded-lg overflow-hidden font-mono text-xs">
                <table className="w-full text-left">
                  <thead className="bg-bg-2 border-b border-border text-[11px] text-text-1">
                    <tr>
                      <th className="p-2.5">Grammar Property</th>
                      <th className="p-2.5">Result</th>
                      <th className="p-2.5">Theoretical Justification & Derivation Note</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border bg-bg-1">
                    {GRAMMAR_VERIFIED_PROPERTIES.map((prop) => (
                      <tr key={prop.property} className="hover:bg-bg-2/50">
                        <td className="p-2.5 font-bold text-text-0">{prop.property}</td>
                        <td className="p-2.5 font-bold">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[11px] ${
                              prop.result === 'True' || prop.result.includes('Type-2')
                                ? 'bg-ok/20 text-ok border border-ok/40'
                                : 'bg-warn/20 text-warn border border-warn/40'
                            }`}
                          >
                            {prop.result}
                          </span>
                        </td>
                        <td className="p-2.5 text-text-1 font-sans">{prop.note}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Dangling Else Disambiguation note (AC-R4 search keyword) */}
            <div className="p-3 bg-bg-1 border border-border rounded-lg space-y-1.5">
              <div className="font-bold text-text-0">Dangling Else Disambiguation:</div>
              <p className="text-text-1">
                In classical languages, the nested if-else construct exhibits ambiguity because an <code>else</code> can bind
                to either the inner or outer <code>if</code>. Vela eliminates this ambiguity at the grammar level by requiring
                mandatory curly braces <code>{`{ ... }`}</code> around all statement blocks, and additionally documents the
                classical matched / unmatched statement transformation in the Grammar Lab.
              </p>
            </div>
          </div>
        )}

        {/* SECTION 3: Error Catalogue (47 codes, AC-R2) */}
        {activeSection === 'errors' && (
          <div className="flex-1 flex flex-col p-4 overflow-hidden space-y-3">
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-lg font-bold text-text-0">Vela Error Catalogue (All 47 Codes)</h1>
                <p className="text-xs text-text-1">
                  Exhaustive diagnostic code reference with causes, sample invalid code, and recommended fixes.
                </p>
              </div>
              <span className="text-xs font-mono text-text-1">
                Showing {filteredErrors.length} of {ERROR_CATALOGUE.length} codes
              </span>
            </div>

            <div className="flex-1 overflow-auto space-y-2 pr-1">
              {filteredErrors.map((err) => (
                <div
                  key={err.code}
                  className="p-3 bg-bg-1 border border-border rounded-lg space-y-2 hover:border-accent/40 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-xs px-2 py-0.5 rounded bg-bg-2 border border-border text-accent">
                        {err.code}
                      </span>
                      <span className="font-bold text-xs text-text-0">{err.meaning}</span>
                    </div>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-bg-2 border border-border text-text-1">
                      Phase: {err.category}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="p-2 bg-bg-0 border border-border rounded space-y-1">
                      <div className="text-[10px] text-err font-bold">Sample Invalid Code:</div>
                      <pre className="font-mono text-[11px] text-err overflow-auto whitespace-pre-wrap">
                        {err.sampleInvalid}
                      </pre>
                    </div>

                    <div className="p-2 bg-bg-0 border border-border rounded space-y-1">
                      <div className="text-[10px] text-ok font-bold">Fix / Solution:</div>
                      <div className="text-[11px] text-text-0">{err.fix}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* SECTION 4: Examples Library (AC-R3) */}
        {activeSection === 'examples' && (
          <div className="flex-1 flex flex-col p-4 overflow-hidden space-y-3">
            <div>
              <h1 className="text-lg font-bold text-text-0">Bundled Examples Library</h1>
              <p className="text-xs text-text-1">
                Standard syllabus test programs covering all features from minimal expressions to 3-address IR lowering.
              </p>
            </div>

            <div className="flex-1 overflow-auto grid grid-cols-2 gap-4 pr-1">
              {filteredExamples.map((ex) => (
                <div
                  key={ex.id}
                  className="p-3.5 bg-bg-1 border border-border rounded-lg flex flex-col justify-between space-y-3 hover:border-accent/40 transition-colors"
                >
                  <div className="space-y-1">
                    <div className="flex justify-between items-center">
                      <span className="font-mono font-bold text-accent text-xs">{ex.filename}</span>
                      <span className="text-[11px] text-text-1 font-mono">#{ex.id}</span>
                    </div>
                    <div className="font-bold text-xs text-text-0">{ex.title}</div>
                    <div className="text-xs text-text-1">{ex.description}</div>
                  </div>

                  <div className="flex justify-between items-center pt-2 border-t border-border">
                    <button
                      onClick={() => handleOpenInPlayground(ex.id)}
                      className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-accent/20 hover:bg-accent/30 text-accent text-xs font-semibold border border-accent/40 transition-colors"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      <span>Open in Playground</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* SECTION 5: Specification Documents */}
        {activeSection === 'docs' && (
          <div className="flex-1 flex overflow-hidden">
            {/* Docs Sub-list */}
            <div className="w-64 border-r border-border bg-bg-1 flex flex-col overflow-hidden select-none">
              <div className="p-2.5 bg-bg-2 border-b border-border font-bold text-xs text-text-0">
                Specifications ({docsList.length})
              </div>
              <div className="flex-1 overflow-auto p-1.5 space-y-1 text-xs">
                {docsList.map((doc) => (
                  <button
                    key={doc.name}
                    onClick={() => setSelectedDoc(doc.name)}
                    className={`w-full text-left px-2.5 py-1.5 rounded transition-colors truncate ${
                      selectedDoc === doc.name
                        ? 'bg-accent/15 text-accent font-semibold'
                        : 'text-text-1 hover:text-text-0 hover:bg-bg-2'
                    }`}
                  >
                    {doc.title}
                  </button>
                ))}
              </div>
            </div>

            {/* Doc Text Viewer */}
            <div className="flex-1 overflow-auto p-6 bg-bg-0 text-text-0 font-sans text-xs">
              <pre className="font-mono text-xs whitespace-pre-wrap leading-relaxed text-text-0">
                {docContent || 'Loading document specification...'}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
