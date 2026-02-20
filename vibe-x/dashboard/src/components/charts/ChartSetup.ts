'use client';

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
  Filler,
);

export const CHART_COLORS = {
  green: '#34d399',
  red: '#f87171',
  yellow: '#fbbf24',
  blue: '#60a5fa',
  violet: '#a78bfa',
  gray: '#6b7280',
};

export const CHART_DEFAULTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
  },
  scales: {
    x: {
      grid: { color: 'rgba(255,255,255,0.05)' },
      ticks: { color: '#6b7280', font: { size: 11 } },
    },
    y: {
      grid: { color: 'rgba(255,255,255,0.05)' },
      ticks: { color: '#6b7280', font: { size: 11 } },
    },
  },
};
