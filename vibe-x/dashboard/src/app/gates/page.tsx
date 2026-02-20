'use client';

import { useEffect, useState } from 'react';
import { Bar } from 'react-chartjs-2';
import '@/components/charts/ChartSetup';
import { CHART_COLORS, CHART_DEFAULTS } from '@/components/charts/ChartSetup';
import { api } from '@/lib/api';
import { t } from '@/lib/i18n';
import { Card, CardTitle } from '@/components/ui/Card';
import { StatusBadge } from '@/components/ui/StatusBadge';
import type { DashboardData } from '@/lib/api';

const GATE_NAMES = ['Syntax', 'Rules', 'Integration', 'Review', 'Architecture', 'Collision'];

export default function GatesPage() {
  const [data, setData] = useState<DashboardData | null>(null);

  useEffect(() => {
    api.getDashboard().then(setData).catch(() => {});
  }, []);

  if (!data) return <div className="animate-pulse h-96 rounded-xl bg-white/5" />;

  const rates = data.gate_pass_rates;
  const chartData = {
    labels: GATE_NAMES.map((n, i) => `G${i + 1}: ${n}`),
    datasets: [{
      label: 'Pass Rate %',
      data: rates,
      backgroundColor: rates.map((r) => (r >= 80 ? 'rgba(52,211,153,.4)' : r >= 50 ? 'rgba(251,191,36,.4)' : 'rgba(248,113,113,.4)')),
      borderColor: rates.map((r) => (r >= 80 ? CHART_COLORS.green : r >= 50 ? CHART_COLORS.yellow : CHART_COLORS.red)),
      borderWidth: 2,
      borderRadius: 6,
    }],
  };

  const recent = [...data.recent_gates].reverse();

  return (
    <div className="space-y-6">
      <Card>
        <CardTitle>{t('gate_stats_title')}</CardTitle>
        <div className="h-64 mt-2">
          <Bar data={chartData} options={{ ...CHART_DEFAULTS, scales: { ...CHART_DEFAULTS.scales, y: { ...CHART_DEFAULTS.scales.y, max: 100 } } } as never} />
        </div>
      </Card>

      <Card>
        <CardTitle>{t('gate_analysis_title')}</CardTitle>
        <div className="max-h-96 overflow-y-auto">
          {recent.length === 0 && (
            <p className="text-gray-500 text-sm py-8 text-center">{t('gate_history_empty')}</p>
          )}
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-[#1e1e2e]">
              <tr className="text-gray-500 text-xs border-b border-white/5">
                <th className="py-2 text-left pl-4">Gate</th>
                <th className="py-2 text-left">Name</th>
                <th className="py-2 text-left">Status</th>
                <th className="py-2 text-left">Message</th>
                <th className="py-2 text-right pr-4">Time</th>
              </tr>
            </thead>
            <tbody>
              {recent.map((g, i) => (
                <tr key={i} className="border-b border-white/5 hover:bg-white/[0.02]">
                  <td className="py-2.5 pl-4 font-mono text-gray-400">G{g.gate}</td>
                  <td className="py-2.5 text-gray-300">{g.name}</td>
                  <td className="py-2.5"><StatusBadge status={g.status} /></td>
                  <td className="py-2.5 text-gray-400 truncate max-w-sm">{g.message}</td>
                  <td className="py-2.5 text-right pr-4 text-xs text-gray-500">{g.timestamp.slice(11, 19)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
