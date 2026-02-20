'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { t } from '@/lib/i18n';
import { Card, CardTitle } from '@/components/ui/Card';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Play, Loader2 } from 'lucide-react';
import type { PipelineResult } from '@/lib/api';

export default function PipelinePage() {
  const [filePath, setFilePath] = useState('');
  const [author, setAuthor] = useState('');
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [error, setError] = useState('');

  async function runPipeline() {
    if (!filePath.trim()) return;
    setRunning(true);
    setError('');
    setResult(null);

    try {
      const data = await api.runPipeline(filePath.trim(), author.trim() || 'anonymous');
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Pipeline failed');
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardTitle>{t('pipeline_runner_title')}</CardTitle>
        <div className="flex gap-3 mt-3">
          <input
            value={filePath}
            onChange={(e) => setFilePath(e.target.value)}
            placeholder={t('pipeline_placeholder')}
            className="flex-1 rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-gray-200 outline-none focus:border-violet-500/50 transition-colors placeholder:text-gray-500"
            onKeyDown={(e) => e.key === 'Enter' && runPipeline()}
          />
          <input
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            placeholder={t('pipeline_author_ph')}
            className="w-40 rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-gray-200 outline-none focus:border-violet-500/50 transition-colors placeholder:text-gray-500"
          />
          <button
            onClick={runPipeline}
            disabled={running || !filePath.trim()}
            className="flex items-center gap-2 rounded-lg bg-violet-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {running ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
            {running ? t('pipeline_running') : t('pipeline_run_btn')}
          </button>
        </div>
      </Card>

      {error && (
        <Card className="border-red-500/20">
          <p className="text-red-400 text-sm">{error}</p>
        </Card>
      )}

      {result && (
        <Card>
          <div className="flex items-center justify-between mb-4">
            <CardTitle>
              Results: <span className="text-gray-300 font-mono">{result.file_path}</span>
            </CardTitle>
            <StatusBadge status={result.overall_status} size="md" />
          </div>

          <div className="grid grid-cols-6 gap-3">
            {result.gates.map((g) => (
              <div
                key={g.gate}
                className={`rounded-lg border p-4 text-center ${
                  g.status === 'passed'
                    ? 'border-emerald-500/20 bg-emerald-500/5'
                    : g.status === 'failed'
                    ? 'border-red-500/20 bg-red-500/5'
                    : 'border-yellow-500/20 bg-yellow-500/5'
                }`}
              >
                <div className="text-xs text-gray-500 mb-1">Gate {g.gate}</div>
                <div className="text-sm font-medium text-gray-300 mb-2">{g.name}</div>
                <StatusBadge status={g.status} />
              </div>
            ))}
          </div>

          {result.gates.some((g) => g.details.length > 0) && (
            <div className="mt-4 border-t border-white/5 pt-4 space-y-2">
              {result.gates
                .filter((g) => g.details.length > 0)
                .map((g) => (
                  <div key={g.gate}>
                    <h4 className="text-sm font-medium text-gray-400 mb-1">Gate {g.gate}: {g.name}</h4>
                    {g.details.map((d, i) => (
                      <p key={i} className="text-xs text-gray-500 pl-4 py-0.5 font-mono">{d}</p>
                    ))}
                  </div>
                ))}
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
