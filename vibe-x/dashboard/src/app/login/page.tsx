'use client';

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { t } from '@/lib/i18n';

export default function LoginPage() {
  const router = useRouter();
  const { login, user } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (user) {
    router.replace('/');
    return null;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    const err = await login(username, password);
    setLoading(false);
    if (err) {
      setError(err);
    } else {
      router.replace('/');
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0d0d14]">
      <div className="w-full max-w-sm rounded-2xl border border-white/10 bg-[#12121a] p-8 shadow-2xl">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 text-lg font-bold text-white">
            VX
          </div>
          <h1 className="text-xl font-semibold text-gray-100">VIBE-X</h1>
          <p className="mt-1 text-sm text-gray-500">{t('login_title' as never)}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-400">{t('login_username' as never)}</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-gray-200 outline-none transition focus:border-violet-500 focus:ring-1 focus:ring-violet-500"
              placeholder="admin"
              autoFocus
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-400">{t('login_password' as never)}</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-gray-200 outline-none transition focus:border-violet-500 focus:ring-1 focus:ring-violet-500"
              placeholder="admin"
              required
            />
          </div>

          {error && (
            <div className="rounded-lg bg-red-500/10 border border-red-500/30 px-3 py-2 text-sm text-red-400">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-gradient-to-r from-violet-500 to-indigo-600 py-2.5 text-sm font-medium text-white transition hover:opacity-90 disabled:opacity-50"
          >
            {loading ? '...' : t('login_btn' as never)}
          </button>
        </form>

        <p className="mt-6 text-center text-xs text-gray-600">
          Default: admin / admin
        </p>
      </div>
    </div>
  );
}
