export interface Snippet {
  label: string;
  detail: string;
  insertText: string;
}

export const VELA_SNIPPETS: Snippet[] = [
  {
    label: 'func',
    detail: 'Function declaration',
    insertText: 'func ${1:name}(${2:params}) -> ${3:void} {\n\t${4:// body}\n}',
  },
  {
    label: 'if',
    detail: 'If statement',
    insertText: 'if (${1:condition}) {\n\t${2:// body}\n}',
  },
  {
    label: 'ifelse',
    detail: 'If-Else statement',
    insertText: 'if (${1:condition}) {\n\t${2:// then}\n} else {\n\t${3:// else}\n}',
  },
  {
    label: 'while',
    detail: 'While loop',
    insertText: 'while (${1:condition}) {\n\t${2:// loop body}\n}',
  },
  {
    label: 'for',
    detail: 'For loop over range',
    insertText: 'for (${1:i} in ${2:0}..${3:10}) {\n\t${4:// loop body}\n}',
  },
  {
    label: 'switch',
    detail: 'Switch-case statement',
    insertText: 'switch (${1:expr}) {\n\tcase ${2:val}:\n\t\t${3:// case body}\n\tdefault:\n\t\t${4:// default body}\n}',
  },
  {
    label: 'let',
    detail: 'Variable declaration',
    insertText: 'let ${1:name}: ${2:int} = ${3:value};',
  },
  {
    label: 'show',
    detail: 'Show (print) statement',
    insertText: 'show ${1:expr};',
  },
  {
    label: 'read',
    detail: 'Read (input) statement',
    insertText: 'read ${1:target};',
  },
];
