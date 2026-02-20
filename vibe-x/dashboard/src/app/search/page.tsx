'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { t } from '@/lib/i18n';
import { Card, CardTitle } from '@/components/ui/Card';
import { Search, Database, RefreshCw } from 'lucide-react';
import type { SearchResult } from '@/lib/api';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [stats, setStats] = useState<{ total_chunks: number; collection: string; status: string } | null>(null);
  const [reindexing, setReindexing] = useState(false);

  useEffect(() => {
    api.getRagStats().then(setStats).catch(() => {});
  }, []);

  async function search() {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const data = await api.searchCode(query.trim());
      setResults(data.results || []);
    } catch { /* silent */ }
    setSearching(false);
  }

  async function reindex() {
    setReindexing(true);
    try {
      await api.reindex();
      const s = await api.getRagStats();
      setStats(s);
    } catch { /* silent */ }
    setReindexing(false);
  }

  return (
    <div className="space-y-6">
      <Card>
        <div className="flex items-center justify-between mb-4">
          <CardTitle>{t('rag_search_title')}</CardTitle>
          {stats && (
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span className="flex items-center gap-1"><Database size={12} /> {stats.total_chunks} {t('rag_chunks')}</span>
              <span>{t('rag_status')}: {stats.status}</span>
              <button onClick={reindex} disabled={reindexing}
                className="flex items-center gap-1 rounded-md border border-white/10 px-2.5 py-1 hover:border-white/20 transition-colors disabled:opacity-50">
                <RefreshCw size={12} className={reindexing ? 'animate-spin' : ''} />
                {t('rag_reindex')}
              </button>
            </div>
          )}
        </div>
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t('rag_placeholder')}
              onKeyDown={(e) => e.key === 'Enter' && search()}
              className="w-full rounded-lg border border-white/10 bg-white/5 pl-11 pr-4 py-2.5 text-sm text-gray-200 outline-none focus:border-violet-500/50 transition-colors placeholder:text-gray-500"
            />
          </div>
          <button onClick={search} disabled={searching}
            className="rounded-lg bg-violet-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-violet-500 disabled:opacity-50 transition-colors">
            {searching ? t('rag_searching') : t('rag_search_btn')}
          </button>
        </div>
      </Card>

      {results.length > 0 && (
        <Card>
          <CardTitle>{results.length} {t('rag_results_count')}</CardTitle>
          <div className="space-y-3 mt-3">
            {results.map((r, i) => (
              <div key={i} className="rounded-lg border border-white/5 bg-white/[0.02] overflow-hidden">
                <div className="flex items-center justify-between px-4 py-2 bg-white/[0.02] border-b border-white/5">
                  <span className="text-sm font-mono text-violet-400">{r.file_path}</span>
                  <div className="flex items-center gap-3 text-xs text-gray-500">
                    <span>{t('rag_lines')}: {r.start_line}-{r.end_line}</span>
                    <span className="text-emerald-400 font-medium">{(r.relevance_score * 100).toFixed(0)}%</span>
                  </div>
                </div>
                <pre className="p-4 text-xs text-gray-300 overflow-x-auto leading-relaxed max-h-48">
                  <code>{r.content}</code>
                </pre>
              </div>
            ))}
          </div>
        </Card>
      )}

      {results.length === 0 && !searching && query && (
        <Card><p className="text-sm text-gray-500 text-center py-4">{t('rag_no_results')}</p></Card>
      )}
      {!query && !results.length && (
        <Card><p className="text-sm text-gray-500 text-center py-4">{t('rag_empty')}</p></Card>
      )}
    </div>
  );
}
