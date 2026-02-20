'use client';

import { useState, useEffect, useCallback } from 'react';
import { usePathname } from 'next/navigation';
import { TabBar } from '@/components/TabBar';
import { Header } from '@/components/Header';
import { AlertBar } from '@/components/AlertBar';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useAuthProvider, AuthContext } from '@/hooks/useAuth';
import { api } from '@/lib/api';
import { t, getLang, toggleLang } from '@/lib/i18n';
import type { AlertData } from '@/lib/api';

const PUBLIC_PATHS = ['/login'];

export function AppShell({ children }: { children: React.ReactNode }) {
  const auth = useAuthProvider();
  const pathname = usePathname();
  const [lang, setLangState] = useState('ko');
  const [alerts, setAlerts] = useState<AlertData[]>([]);
  const [, setForceRender] = useState(0);

  useEffect(() => {
    setLangState(getLang());
  }, []);

  const handleWsMessage = useCallback((msg: { type: string; data?: unknown }) => {
    if (msg.type === 'alert') {
      fetchAlerts();
    }
    if (msg.type === 'dashboard_update' || msg.type === 'gate_result') {
      evaluateAndFetchAlerts();
    }
  }, []);

  const { status: wsStatus } = useWebSocket(handleWsMessage);

  useEffect(() => {
    if (auth.user) {
      fetchAlerts();
      evaluateAndFetchAlerts();
    }
  }, [auth.user]);

  async function fetchAlerts() {
    try {
      const data = await api.getAlerts(true);
      setAlerts(data.alerts);
    } catch { /* silent */ }
  }

  async function evaluateAndFetchAlerts() {
    try {
      await api.evaluateAlerts();
      await fetchAlerts();
    } catch { /* silent */ }
  }

  function handleToggleLang() {
    const next = toggleLang();
    setLangState(next);
    setForceRender((n) => n + 1);
  }

  async function handleDismissAll() {
    try {
      await api.acknowledgeAlert('all');
      setAlerts([]);
    } catch { /* silent */ }
  }

  const statusLabel = wsStatus === 'live' ? t('live' as never) : wsStatus === 'reconnecting' ? t('reconnecting' as never) : t('connecting' as never);

  const isPublicPage = PUBLIC_PATHS.includes(pathname);

  if (isPublicPage) {
    return (
      <AuthContext.Provider value={auth}>
        {children}
      </AuthContext.Provider>
    );
  }

  if (auth.loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-gray-500">
        {t('loading' as never)}
      </div>
    );
  }

  if (!auth.user) {
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
    return null;
  }

  return (
    <AuthContext.Provider value={auth}>
      <div className="flex min-h-screen flex-col">
        <Header
          title={t('header_title' as never)}
          wsStatus={wsStatus}
          lang={lang}
          onToggleLang={handleToggleLang}
          statusLabel={statusLabel}
          user={auth.user}
          onLogout={auth.logout}
        />
        <TabBar t={(key) => t(key as never)} isAdmin={auth.isLead} />
        <AlertBar alerts={alerts} onDismissAll={handleDismissAll} />
        <main className="flex-1 p-6">
          {children}
        </main>
      </div>
    </AuthContext.Provider>
  );
}
