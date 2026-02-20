'use client';

import { useState } from 'react';
import { AlertTriangle, X } from 'lucide-react';
import type { AlertData } from '@/lib/api';

interface AlertBarProps {
  alerts: AlertData[];
  onDismissAll: () => void;
}

export function AlertBar({ alerts, onDismissAll }: AlertBarProps) {
  const [expanded, setExpanded] = useState(false);

  if (!alerts.length) return null;

  const critical = alerts.filter((a) => a.level === 'critical');
  const topAlert = critical[0] ?? alerts[0];

  return (
    <div className="border-b border-red-500/20 bg-red-500/5">
      <div
        className="flex items-center gap-3 px-6 py-2.5 cursor-pointer hover:bg-red-500/10 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <AlertTriangle size={16} className="text-yellow-400" />
        <span className={`flex-1 text-sm ${critical.length ? 'text-red-400' : 'text-yellow-400'}`}>
          {topAlert.title}
        </span>
        <span className="rounded-full bg-red-500/15 px-2.5 py-0.5 text-xs font-bold text-red-400">
          {alerts.length}
        </span>
        <button
          onClick={(e) => { e.stopPropagation(); onDismissAll(); }}
          className="rounded-md border border-white/10 px-3 py-1 text-xs text-gray-400 hover:text-gray-200 hover:border-white/20 transition-colors"
        >
          Dismiss All
        </button>
      </div>

      {expanded && (
        <div className="max-h-60 overflow-y-auto border-t border-white/5">
          {alerts.map((alert) => (
            <div key={alert.alert_id} className="flex items-start gap-3 px-6 py-3 border-b border-white/5 last:border-0">
              <div className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${
                alert.level === 'critical' ? 'bg-red-500' : alert.level === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
              }`} />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-gray-200">{alert.title}</div>
                <div className="text-xs text-gray-400 mt-0.5">{alert.message}</div>
              </div>
              <div className="text-xs text-gray-500 whitespace-nowrap">
                {new Date(alert.created_at).toLocaleTimeString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
