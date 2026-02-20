interface ProgressBarProps {
  value: number;
  color?: string;
  className?: string;
}

export function ProgressBar({ value, color = 'bg-emerald-500', className = '' }: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div className={`h-1.5 w-full rounded-full bg-white/5 overflow-hidden ${className}`}>
      <div
        className={`h-full rounded-full transition-all duration-700 ${color}`}
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
