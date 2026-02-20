interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
}

const COLORS: Record<string, string> = {
  passed: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  failed: 'bg-red-500/20 text-red-400 border-red-500/30',
  warning: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  online: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  working: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  offline: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  critical: 'bg-red-500/20 text-red-400 border-red-500/30',
  info: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  high: 'bg-red-500/20 text-red-400 border-red-500/30',
  medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
};

export function StatusBadge({ status, size = 'sm' }: StatusBadgeProps) {
  const color = COLORS[status] ?? COLORS.offline;
  const sizeClass = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm';
  return (
    <span className={`inline-flex items-center rounded-md border font-semibold uppercase ${color} ${sizeClass}`}>
      {status}
    </span>
  );
}
