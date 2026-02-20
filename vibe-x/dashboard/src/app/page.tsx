'use client';

import { useEffect, useState } from 'react';
import { Line, Doughnut, Bar } from 'react-chartjs-2';
import '@/components/charts/ChartSetup';
import { CHART_COLORS, CHART_DEFAULTS } from '@/components/charts/ChartSetup';
import { api } from '@/lib/api';
import { t } from '@/lib/i18n';
import { Card, CardTitle, CardValue } from '@/components/ui/Card';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { StatusBadge } from '@/components/ui/StatusBadge';
import type { DashboardData, HealthBreakdown } from '@/lib/api';

export default function OverviewPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [health, setHealth] = useState<HealthBreakdown | null>(null);

  useEffect(() => {
    fetchAll();
    const id = setInterval(fetchAll, 30000);
    return () => clearInterval(id);
  }, []);

  async function fetchAll() {
    try {
      const [d, h] = await Promise.all([api.getDashboard(), api.getHealth()]);
      setData(d);
      setHealth(h);
    } catch { /* silent */ }
  }

  if (!data) return <LoadingSkeleton />;

  return (
    <div className="space-y-6">
      <StatCards data={data} />
      {health && <HealthBreakdownGrid health={health} />}
      <div className="grid grid-cols-2 gap-6">
        <WeeklyTrendChart data={data} />
        <RecentGates data={data} />
      </div>
      <div className="grid grid-cols-3 gap-6">
        <GateDonut data={data} />
        <CostTrend data={data} />
        <TeamActivity data={data} />
      </div>
    </div>
  );
}

function StatCards({ data }: { data: DashboardData }) {
  const scoreColor =
    data.health_score >= 70 ? 'text-emerald-400' : data.health_score >= 40 ? 'text-yellow-400' : 'text-red-400';
  const barColor =
    data.health_score >= 70 ? 'bg-emerald-500' : data.health_score >= 40 ? 'bg-yellow-500' : 'bg-red-500';

  return (
    <div className="grid grid-cols-4 gap-5">
      <Card>
        <CardTitle>{t('health_score')}</CardTitle>
        <CardValue className={scoreColor}>{data.health_score}</CardValue>
        <ProgressBar value={data.health_score} color={barColor} className="mt-3" />
      </Card>
      <Card>
        <CardTitle>{t('gate_pass_rate')}</CardTitle>
        <CardValue className="text-blue-400">{data.today.pass_rate}%</CardValue>
        <p className="text-xs text-gray-500 mt-1">{t('today')}: {data.today.gate_runs} {t('runs')}</p>
      </Card>
      <Card>
        <CardTitle>{t('ai_cost_today')}</CardTitle>
        <CardValue className="text-yellow-400">${data.today.ai_cost}</CardValue>
        <p className="text-xs text-gray-500 mt-1">{t('total')}: ${data.cumulative.total_cost_usd}</p>
      </Card>
      <Card>
        <CardTitle>{t('files_indexed')}</CardTitle>
        <CardValue className="text-violet-400">{data.cumulative.total_files_indexed}</CardValue>
        <p className="text-xs text-gray-500 mt-1">{t('searches')}: {data.today.searches}</p>
      </Card>
    </div>
  );
}

function HealthBreakdownGrid({ health }: { health: HealthBreakdown }) {
  const items = [
    { label: t('hb_gate_label'), value: health.gate_pass_rate, color: 'bg-emerald-500', text: 'text-emerald-400' },
    { label: t('hb_arch_label'), value: health.architecture_consistency, color: 'bg-blue-500', text: 'text-blue-400' },
    { label: t('hb_quality_label'), value: health.code_quality, color: 'bg-violet-500', text: 'text-violet-400' },
    { label: t('hb_activity_label'), value: health.activity_index, color: 'bg-yellow-500', text: 'text-yellow-400' },
  ];

  return (
    <Card>
      <CardTitle>{t('health_breakdown')}</CardTitle>
      <div className="grid grid-cols-4 gap-4 mt-3">
        {items.map((item) => (
          <div key={item.label} className="rounded-lg border border-white/5 bg-white/[0.02] p-4 text-center">
            <div className={`text-2xl font-bold ${item.text}`}>{Math.round(item.value)}%</div>
            <div className="text-xs text-gray-500 mt-1">{item.label}</div>
            <ProgressBar value={item.value} color={item.color} className="mt-3" />
          </div>
        ))}
      </div>
      {health.tech_debt_items.length > 0 && (
        <div className="mt-4 border-t border-white/5 pt-4">
          <h4 className="text-sm font-medium text-gray-400 mb-3">{t('tech_debt_title')}</h4>
          {health.tech_debt_items.map((d, i) => (
            <div key={i} className="flex items-center gap-3 py-2 border-b border-white/5 last:border-0 text-sm">
              <StatusBadge status={d.severity} />
              <span className="flex-1">{d.issue} (Gate {d.gate}, {d.count}x)</span>
              <span className="text-xs text-gray-500">{d.suggestion}</span>
            </div>
          ))}
        </div>
      )}
      {health.tech_debt_items.length === 0 && (
        <p className="text-xs text-gray-500 mt-3">{t('tech_debt_empty')}</p>
      )}
    </Card>
  );
}

function WeeklyTrendChart({ data }: { data: DashboardData }) {
  const labels = data.weekly_trend.map((d) => d.date.slice(5));
  const chartData = {
    labels,
    datasets: [
      {
        label: 'Passed',
        data: data.weekly_trend.map((d) => d.passed),
        borderColor: CHART_COLORS.green,
        backgroundColor: 'rgba(52,211,153,.1)',
        fill: true,
        tension: 0.4,
      },
      {
        label: 'Failed',
        data: data.weekly_trend.map((d) => d.failed),
        borderColor: CHART_COLORS.red,
        backgroundColor: 'rgba(248,113,113,.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  return (
    <Card>
      <CardTitle>{t('weekly_trend')}</CardTitle>
      <div className="h-52">
        <Line data={chartData} options={CHART_DEFAULTS as never} />
      </div>
    </Card>
  );
}

function RecentGates({ data }: { data: DashboardData }) {
  const recent = [...data.recent_gates].reverse().slice(0, 12);
  return (
    <Card>
      <CardTitle>{t('recent_gates')}</CardTitle>
      <div className="max-h-52 overflow-y-auto space-y-1">
        {recent.map((g, i) => (
          <div key={i} className="flex items-center gap-3 rounded-md px-3 py-1.5 hover:bg-white/5 text-sm">
            <StatusBadge status={g.status} />
            <span className="text-gray-300 flex-1 truncate">
              Gate {g.gate}: {g.name}
            </span>
            <span className="text-xs text-gray-500">{g.timestamp.slice(11, 19)}</span>
          </div>
        ))}
        {!recent.length && <p className="text-sm text-gray-500 py-4 text-center">{t('no_data')}</p>}
      </div>
    </Card>
  );
}

function GateDonut({ data }: { data: DashboardData }) {
  const t_ = data.today;
  const chartData = {
    labels: ['Passed', 'Failed', 'Warning'],
    datasets: [{
      data: [t_.gate_passed, t_.gate_failed, t_.gate_warned],
      backgroundColor: [CHART_COLORS.green, CHART_COLORS.red, CHART_COLORS.yellow],
      borderWidth: 0,
    }],
  };
  return (
    <Card>
      <CardTitle>{t('gate_distribution')}</CardTitle>
      <div className="h-44 flex items-center justify-center">
        <Doughnut data={chartData} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { display: true, position: 'bottom', labels: { color: '#9ca3af', font: { size: 11 } } } } } as never} />
      </div>
    </Card>
  );
}

function CostTrend({ data }: { data: DashboardData }) {
  const labels = data.weekly_trend.map((d) => d.date.slice(5));
  const chartData = {
    labels,
    datasets: [{
      label: 'Cost ($)',
      data: data.weekly_trend.map((d) => d.cost),
      backgroundColor: 'rgba(251,191,36,.3)',
      borderColor: CHART_COLORS.yellow,
      borderWidth: 2,
      borderRadius: 4,
    }],
  };
  return (
    <Card>
      <CardTitle>{t('cost_trend')}</CardTitle>
      <div className="h-44">
        <Bar data={chartData} options={CHART_DEFAULTS as never} />
      </div>
    </Card>
  );
}

function TeamActivity({ data }: { data: DashboardData }) {
  return (
    <Card>
      <CardTitle>{t('team_activity')}</CardTitle>
      <div className="max-h-44 overflow-y-auto space-y-2">
        {data.team.map((m) => (
          <div key={m.name} className="flex items-center gap-3 text-sm">
            <div className={`h-2 w-2 rounded-full ${m.status === 'online' ? 'bg-emerald-400' : m.status === 'working' ? 'bg-blue-400' : 'bg-gray-500'}`} />
            <span className="flex-1 text-gray-300">{m.name}</span>
            <span className="text-xs text-gray-500">{m.active_files} files</span>
          </div>
        ))}
        {!data.team.length && <p className="text-sm text-gray-500 py-4 text-center">{t('no_team')}</p>}
      </div>
    </Card>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="grid grid-cols-4 gap-5">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-28 rounded-xl bg-white/5" />
        ))}
      </div>
      <div className="h-40 rounded-xl bg-white/5" />
      <div className="grid grid-cols-2 gap-6">
        <div className="h-64 rounded-xl bg-white/5" />
        <div className="h-64 rounded-xl bg-white/5" />
      </div>
    </div>
  );
}
