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
  FolderKanban,
  Settings,
  FileCode2,
} from 'lucide-react';

const NAV_ITEMS = [
  { href: '/', label: 'tab_overview', icon: LayoutDashboard },
  { href: '/gates', label: 'tab_gates', icon: Shield },
  { href: '/pipeline', label: 'tab_pipeline', icon: Play },
  { href: '/search', label: 'tab_search', icon: Search },
  { href: '/onboarding', label: 'tab_onboarding', icon: GraduationCap },
  { href: '/feedback', label: 'tab_feedback', icon: RefreshCw },
  { href: '/collab', label: 'tab_collab', icon: Users },
  { href: '/meta', label: 'tab_meta', icon: FileCode2 },
];

const ADMIN_ITEMS = [
  { href: '/projects', label: 'tab_projects', icon: FolderKanban },
  { href: '/admin', label: 'tab_admin', icon: Settings },
];

interface TabBarProps {
  t: (key: string) => string;
  isAdmin?: boolean;
}

export function TabBar({ t, isAdmin }: TabBarProps) {
  const pathname = usePathname();
  const allItems = isAdmin ? [...NAV_ITEMS, ...ADMIN_ITEMS] : NAV_ITEMS;

  return (
    <div className="border-b border-white/10 bg-[#12121a]/60 backdrop-blur-sm px-6 overflow-x-auto">
      <div className="flex items-center gap-1">
        {allItems.map(({ href, label, icon: Icon }) => {
          const active = href === '/' ? pathname === '/' : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-2 whitespace-nowrap px-4 py-3 text-sm border-b-2 transition-colors ${
                active
                  ? 'border-violet-500 text-violet-400 font-medium'
                  : 'border-transparent text-gray-500 hover:text-gray-300 hover:border-white/20'
              }`}
            >
              <Icon size={15} />
              <span>{t(label)}</span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
