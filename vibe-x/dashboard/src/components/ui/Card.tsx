interface CardProps {
  children: React.ReactNode;
  className?: string;
}

export function Card({ children, className = '' }: CardProps) {
  return (
    <div className={`rounded-xl border border-white/10 bg-[#1e1e2e] p-5 ${className}`}>
      {children}
    </div>
  );
}

export function CardTitle({ children, className = '' }: CardProps) {
  return (
    <h3 className={`text-sm font-medium text-gray-400 mb-2 ${className}`}>{children}</h3>
  );
}

export function CardValue({ children, className = '' }: CardProps) {
  return (
    <div className={`text-3xl font-bold ${className}`}>{children}</div>
  );
}
