/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'bg-0': 'var(--bg-0)',
        'bg-1': 'var(--bg-1)',
        'bg-2': 'var(--bg-2)',
        'border': 'var(--border)',
        'text-0': 'var(--text-0)',
        'text-1': 'var(--text-1)',
        'accent': 'var(--accent)',
        'ok': 'var(--ok)',
        'warn': 'var(--warn)',
        'err': 'var(--err)',
        'sel': 'var(--sel)',
        phase: {
          lexer: 'var(--phase-lexer)',
          parser: 'var(--phase-parser)',
          semantic: 'var(--phase-semantic)',
          ir: 'var(--phase-ir)',
          optimizer: 'var(--phase-optimizer)',
          codegen: 'var(--phase-codegen)',
          vm: 'var(--phase-vm)',
        }
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'Consolas', 'Monaco', 'Courier New', 'monospace'],
      }
    },
  },
  plugins: [],
}
