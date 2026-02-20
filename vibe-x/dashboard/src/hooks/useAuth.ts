'use client';

import { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { api } from '@/lib/api';
import type { AuthUser } from '@/lib/api';

interface AuthState {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<string | null>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
  isAdmin: boolean;
  isLead: boolean;
  hasPermission: (action: string) => boolean;
}

const ROLE_RANK: Record<string, number> = {
  admin: 4,
  lead: 3,
  developer: 2,
  viewer: 1,
};

export function useAuthProvider(): AuthState {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const storeToken = (t: string | null) => {
    setToken(t);
    if (typeof window !== 'undefined') {
      if (t) localStorage.setItem('vibe-x-token', t);
      else localStorage.removeItem('vibe-x-token');
    }
  };

  const refresh = useCallback(async () => {
    const stored = typeof window !== 'undefined' ? localStorage.getItem('vibe-x-token') : null;
    if (!stored) {
      setLoading(false);
      return;
    }
    setToken(stored);
    try {
      const res = await api.getMe();
      if (res.success && res.user) {
        setUser(res.user);
      } else {
        storeToken(null);
        setUser(null);
      }
    } catch {
      storeToken(null);
      setUser(null);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const login = useCallback(async (username: string, password: string): Promise<string | null> => {
    try {
      const res = await api.login(username, password);
      if (res.success && res.token && res.user) {
        storeToken(res.token);
        setUser(res.user);
        return null;
      }
      return res.error ?? '로그인 실패';
    } catch {
      return '서버 연결 실패';
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } catch { /* silent */ }
    storeToken(null);
    setUser(null);
  }, []);

  const isAdmin = user?.role === 'admin';
  const isLead = user?.role === 'lead' || isAdmin;

  const hasPermission = useCallback(
    (action: string): boolean => {
      if (!user) return false;
      const rank = ROLE_RANK[user.role] ?? 0;
      switch (action) {
        case 'user:manage':
          return rank >= ROLE_RANK.lead;
        case 'gate:bypass':
          return rank >= ROLE_RANK.lead;
        case 'config:write':
          return rank >= ROLE_RANK.admin;
        default:
          return rank >= ROLE_RANK.viewer;
      }
    },
    [user],
  );

  return { user, token, loading, login, logout, refresh, isAdmin, isLead, hasPermission };
}

export const AuthContext = createContext<AuthState | null>(null);

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
