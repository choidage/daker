'use client';

import { Globe, Wifi, WifiOff, LogOut, User } from 'lucide-react';
import type { AuthUser } from '@/lib/api';

interface HeaderProps {
  title: string;
  wsStatus: string;
  lang: string;
  onToggleLang: () => void;
  statusLabel: string;
  user?: AuthUser | null;
  onLogout?: () => void;
}

export function Header({ title, wsStatus, lang, onToggleLang, statusLabel, user, onLogout }: HeaderProps) {
  return (
    <header className="flex items-center justify-between border-b border-white/10 bg-[#12121a] px-6 py-3 sticky top-0 z-20">
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600 text-sm font-bold">
          VX
        </div>
        <h1 className="text-lg font-semibold text-gray-200">
          <span className="text-violet-400">VIBE-X</span>{' '}
          <span className="text-gray-400 font-normal text-sm hidden sm:inline">{title}</span>
        </h1>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-xs">
          {wsStatus === 'live' ? (
            <Wifi size={14} className="text-emerald-400" />
          ) : (
            <WifiOff size={14} className="text-yellow-400" />
          )}
          <span className={wsStatus === 'live' ? 'text-emerald-400' : 'text-yellow-400'}>
            {statusLabel}
          </span>
        </div>
        <button
          onClick={onToggleLang}
          className="flex items-center gap-1.5 rounded-md border border-white/10 px-3 py-1.5 text-xs text-gray-400 hover:text-gray-200 hover:border-white/20 transition-colors"
        >
          <Globe size={14} />
          {lang.toUpperCase()}
        </button>

        {user && (
          <div className="flex items-center gap-3 border-l border-white/10 pl-4">
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <User size={14} />
              <span className="text-gray-300 font-medium">{user.display_name || user.username}</span>
              <span className="rounded bg-white/5 border border-white/10 px-1.5 py-0.5 text-[10px] uppercase tracking-wider text-gray-500">
                {user.role}
              </span>
            </div>
            {onLogout && (
              <button
                onClick={onLogout}
                className="flex items-center gap-1 rounded-md px-2 py-1.5 text-xs text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                title="Logout"
              >
                <LogOut size={13} />
              </button>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
