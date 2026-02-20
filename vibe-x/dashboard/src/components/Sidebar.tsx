'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Shield,
  GraduationCap,
  RefreshCw,
  Search,
  Play,
  Users,
  Settings,
  FolderKanban,
} from 'lucide-react';

const NAV_ITEMS = [
  { href: '/', label: 'tab_overview', icon: LayoutDashboard },
  { href: '/gates', label: 'tab_gates', icon: Shield },
  { href: '/pipeline', label: 'tab_pipeline', icon: Play },
  { href: '/search', label: 'tab_search', icon: Search },
  { href: '/onboarding', label: 'tab_onboarding', icon: GraduationCap },
  { href: '/feedback', label: 'tab_feedback', icon: RefreshCw },
  { href: '/collab', label: 'tab_collab', icon: Users },
];

const ADMIN_ITEMS = [
  { href: '/projects', label: 'tab_projects', icon: FolderKanban },
  { href: '/admin', label: 'tab_admin', icon: Settings },
];

interface SidebarProps {
  t: (key: string) => string;
  isAdmin?: boolean;
}

export function Sidebar({ t, isAdmin }: SidebarProps) {
  const pathname = usePathname();

  const allItems = isAdmin ? [...NAV_ITEMS, ...ADMIN_ITEMS] : NAV_ITEMS;

  return (
    <aside className="fixed left-0 top-0 z-30 flex h-screen w-56 flex-col border-r border-white/10 bg-[#12121a]">
      <div className="flex items-center gap-3 px-5 py-5 border-b border-white/10">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600 text-sm font-bold">
          VX
        </div>
        <span className="text-sm font-semibold tracking-wide text-gray-200">VIBE-X</span>
      </div>

      <nav className="flex-1 overflow-y-auto py-4 px-3">
        {allItems.map(({ href, label, icon: Icon }) => {
          const active = href === '/' ? pathname === '/' : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 mb-1 text-sm transition-colors ${
                active
                  ? 'bg-violet-500/15 text-violet-400 font-medium'
                  : 'text-gray-400 hover:bg-white/5 hover:text-gray-200'
              }`}
            >
              <Icon size={18} />
              <span>{t(label)}</span>
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-white/10 px-4 py-3 text-xs text-gray-500">
        VIBE-X v1.0 — Team 바이브제왕
      </div>
    </aside>
  );
}
