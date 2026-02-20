'use client';

import { useEffect, useState } from 'react';
import { Bar } from 'react-chartjs-2';
import '@/components/charts/ChartSetup';
import { CHART_COLORS, CHART_DEFAULTS } from '@/components/charts/ChartSetup';
import { api } from '@/lib/api';
import { t } from '@/lib/i18n';
import { Card, CardTitle } from '@/components/ui/Card';
import { AlertTriangle, CheckCircle, Lightbulb } from 'lucide-react';

interface FeedbackData {
  total_failures: number;
  total_runs: number;
  failure_rate: number;
  patterns: Array<{ gate: string; count: number }>;
  top_messages: Array<{ message: string; count: number }>;
  suggestions: string[];
}

export default function FeedbackPage() {
  const [data, setData] = useState<FeedbackData | null>(null);

  useEffect(() => {
    api.getFeedback()
      .then((d) => setData({
        total_failures: d.total_failures ?? 0,
        total_runs: d.total_runs ?? 0,
        failure_rate: d.failure_rate ?? 0,
        patterns: d.patterns ?? [],
        top_messages: d.top_messages ?? [],
        suggestions: d.suggestions ?? [],
      }))
      .catch(() => {});
  }, []);

  if (!data) return <div className="animate-pulse h-96 rounded-xl bg-white/5" />;

  const hasFailures = data.total_failures > 0;

  const patternChartData = {
    labels: data.patterns.map((p) => p.gate),
    datasets: [{
      label: 'Failures',
      data: data.patterns.map((p) => p.count),
      backgroundColor: 'rgba(248,113,113,.3)',
      borderColor: CHART_COLORS.red,
      borderWidth: 2,
      borderRadius: 6,
    }],
  };

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="grid grid-cols-3 gap-5">
        <Card>
          <CardTitle>{t('total')} {t('runs')}</CardTitle>
          <div className="text-3xl font-bold text-blue-400 mt-1">{data.total_runs}</div>
        </Card>
        <Card>
          <CardTitle>{t('failed')}</CardTitle>
          <div className="text-3xl font-bold text-red-400 mt-1">{data.total_failures}</div>
        </Card>
        <Card>
          <CardTitle>Failure Rate</CardTitle>
          <div className={`text-3xl font-bold mt-1 ${data.failure_rate > 30 ? 'text-red-400' : data.failure_rate > 10 ? 'text-yellow-400' : 'text-emerald-400'}`}>
            {data.failure_rate}%
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Failure patterns */}
        <Card>
          <CardTitle>{t('failure_analysis')}</CardTitle>
          {hasFailures ? (
            <div className="h-52 mt-2">
              <Bar data={patternChartData} options={CHART_DEFAULTS as never} />
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-gray-500">
              <CheckCircle size={32} className="text-emerald-400 mb-3" />
              <p className="text-sm">{t('no_fail_pattern')}</p>
            </div>
          )}
        </Card>

        {/* Detailed failures */}
        <Card>
          <CardTitle>{t('fb_reasons')}</CardTitle>
          {data.top_messages.length > 0 ? (
            <div className="mt-3 space-y-2">
              {data.top_messages.map((m, i) => (
                <div key={i} className="flex items-start gap-3 text-sm">
                  <AlertTriangle size={14} className="text-yellow-400 mt-0.5 shrink-0" />
                  <span className="flex-1 text-gray-400 text-xs">{m.message}</span>
                  <span className="text-xs text-gray-500 shrink-0">{m.count} {t('fb_times')}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 py-8 text-center">{t('fb_no_failures')}</p>
          )}
        </Card>
      </div>

      {/* Suggestions */}
      <Card>
        <CardTitle>{t('suggestions')}</CardTitle>
        <div className="mt-3 space-y-2">
          {data.suggestions.map((s, i) => (
            <div key={i} className="flex items-start gap-3 rounded-lg border border-white/5 bg-white/[0.02] p-4">
              <Lightbulb size={16} className="text-yellow-400 mt-0.5 shrink-0" />
              <span className="text-sm text-gray-300">{s}</span>
            </div>
          ))}
          {!data.suggestions.length && (
            <p className="text-sm text-gray-500 text-center py-4">{t('no_suggestions')}</p>
          )}
        </div>
      </Card>
    </div>
  );
}
