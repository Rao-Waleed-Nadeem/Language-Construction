import React, { useState, useMemo } from 'react';
import { ArrowUpDown, Copy, Search, Check } from 'lucide-react';
import { useUIStore, type SourceSpan } from '../../store/uiStore';

export interface Column<T> {
  key: keyof T | string;
  header: string;
  render?: (row: T, index: number) => React.ReactNode;
  sortable?: boolean;
  width?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  filterPlaceholder?: string;
  getSpan?: (row: T) => SourceSpan | null | undefined;
  className?: string;
}

export function DataTable<T extends Record<string, any>>({
  columns,
  data,
  filterPlaceholder = 'Filter rows...',
  getSpan,
  className = '',
}: DataTableProps<T>) {
  const [filter, setFilter] = useState('');
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortAsc, setSortAsc] = useState(true);
  const [copied, setCopied] = useState(false);

  const { setHoverSpan, setPinnedSpan } = useUIStore();

  const filteredData = useMemo(() => {
    let result = data;
    if (filter.trim()) {
      const q = filter.toLowerCase();
      result = result.filter((row) =>
        Object.values(row).some((val) => String(val).toLowerCase().includes(q))
      );
    }
    if (sortKey) {
      result = [...result].sort((a, b) => {
        const aVal = a[sortKey];
        const bVal = b[sortKey];
        if (aVal === bVal) return 0;
        if (aVal === null || aVal === undefined) return 1;
        if (bVal === null || bVal === undefined) return -1;
        const cmp = aVal < bVal ? -1 : 1;
        return sortAsc ? cmp : -cmp;
      });
    }
    return result;
  }, [data, filter, sortKey, sortAsc]);

  const copyAsTSV = () => {
    const headers = columns.map((c) => c.header).join('\t');
    const rows = filteredData
      .map((row) =>
        columns
          .map((col) => {
            const val = row[col.key as keyof T];
            return typeof val === 'object' ? JSON.stringify(val) : String(val ?? '');
          })
          .join('\t')
      )
      .join('\n');
    navigator.clipboard.writeText(`${headers}\n${rows}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(true);
    }
  };

  return (
    <div className={`flex flex-col h-full bg-bg-1 border border-border rounded-lg overflow-hidden ${className}`}>
      {/* Table toolbar */}
      <div className="flex items-center justify-between p-2 border-b border-border bg-bg-2 gap-2 text-xs">
        <div className="flex items-center gap-1.5 px-2 py-1 bg-bg-1 border border-border rounded w-64 text-text-0">
          <Search className="w-3.5 h-3.5 text-text-1" />
          <input
            type="text"
            placeholder={filterPlaceholder}
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="bg-transparent border-none outline-none w-full text-xs text-text-0 placeholder:text-text-1"
          />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-text-1 font-mono">
            {filteredData.length} {filteredData.length === 1 ? 'row' : 'rows'}
          </span>
          <button
            onClick={copyAsTSV}
            title="Copy as TSV"
            className="flex items-center gap-1 px-2 py-1 bg-bg-1 hover:bg-bg-0 border border-border rounded text-text-1 hover:text-text-0 transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-ok" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied' : 'TSV'}</span>
          </button>
        </div>
      </div>

      {/* Table content */}
      <div className="flex-1 overflow-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead className="sticky top-0 bg-bg-2 border-b border-border z-10">
            <tr>
              {columns.map((col) => (
                <th
                  key={String(col.key)}
                  style={{ width: col.width }}
                  onClick={() => col.sortable !== false && handleSort(String(col.key))}
                  className={`p-2 font-semibold text-text-1 select-none ${
                    col.sortable !== false ? 'cursor-pointer hover:text-text-0' : ''
                  }`}
                >
                  <div className="flex items-center gap-1">
                    <span>{col.header}</span>
                    {col.sortable !== false && <ArrowUpDown className="w-3 h-3 opacity-60" />}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border/40 font-mono">
            {filteredData.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="p-6 text-center text-text-1">
                  No matching records
                </td>
              </tr>
            ) : (
              filteredData.map((row, idx) => {
                const span = getSpan?.(row);
                return (
                  <tr
                    key={idx}
                    onMouseEnter={() => span && setHoverSpan(span)}
                    onMouseLeave={() => span && setHoverSpan(null)}
                    onClick={() => span && setPinnedSpan(span)}
                    className={`hover:bg-bg-2/70 transition-colors ${
                      span ? 'cursor-pointer' : ''
                    }`}
                  >
                    {columns.map((col) => (
                      <td key={String(col.key)} className="p-2 text-text-0 align-top">
                        {col.render ? col.render(row, idx) : String(row[col.key as keyof T] ?? '')}
                      </td>
                    ))}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
