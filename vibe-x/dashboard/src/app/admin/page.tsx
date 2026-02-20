'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { api } from '@/lib/api';
import { t } from '@/lib/i18n';
import { Card } from '@/components/ui/Card';
import type { AuthUser } from '@/lib/api';
import { UserPlus, Shield, Trash2, RotateCcw, Power } from 'lucide-react';

const ROLES = ['admin', 'lead', 'developer', 'viewer'] as const;

const ROLE_COLORS: Record<string, string> = {
  admin: 'bg-red-500/15 text-red-400 border-red-500/30',
  lead: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  developer: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  viewer: 'bg-gray-500/15 text-gray-400 border-gray-500/30',
};

export default function AdminPage() {
  const { user: currentUser, isAdmin, isLead } = useAuth();
  const [users, setUsers] = useState<AuthUser[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ username: '', password: '', role: 'developer', display_name: '', email: '' });
  const [msg, setMsg] = useState('');
  const [resetTarget, setResetTarget] = useState<string | null>(null);
  const [newPw, setNewPw] = useState('');

  useEffect(() => {
    loadUsers();
  }, []);

  async function loadUsers() {
    try {
      const res = await api.getUsers();
      if (res.success && res.users) setUsers(res.users);
    } catch { /* silent */ }
  }

  async function handleAdd() {
    setMsg('');
    const res = await api.registerUser(form);
    if (res.success) {
      setShowAdd(false);
      setForm({ username: '', password: '', role: 'developer', display_name: '', email: '' });
      loadUsers();
    } else {
      setMsg(res.error ?? 'Error');
    }
  }

  async function handleToggleActive(u: AuthUser) {
    if (u.is_active) {
      await api.deactivateUser(u.username);
    } else {
      await api.activateUser(u.username);
    }
    loadUsers();
  }

  async function handleDelete(username: string) {
    if (!confirm(t('admin_confirm_delete' as never))) return;
    await api.deleteUser(username);
    loadUsers();
  }

  async function handleResetPassword() {
    if (!resetTarget || !newPw) return;
    const res = await api.resetPassword(resetTarget, newPw);
    if (res.success) {
      setResetTarget(null);
      setNewPw('');
    } else {
      setMsg(res.error ?? 'Error');
    }
  }

  async function handleRoleChange(username: string, role: string) {
    await api.updateRole(username, role);
    loadUsers();
  }

  if (!isLead) {
    return (
      <div className="flex h-64 items-center justify-center text-gray-500">
        권한이 부족합니다. ADMIN 또는 LEAD 역할이 필요합니다.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-100">{t('admin_title' as never)}</h1>
        <button
          onClick={() => setShowAdd(!showAdd)}
          className="flex items-center gap-2 rounded-lg bg-violet-500/15 border border-violet-500/30 px-4 py-2 text-sm text-violet-400 hover:bg-violet-500/25 transition"
        >
          <UserPlus size={16} />
          {t('admin_add_user' as never)}
        </button>
      </div>

      {showAdd && (
        <Card>
          <div className="grid grid-cols-2 gap-3">
            <input
              placeholder={t('login_username' as never)}
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-gray-200 outline-none focus:border-violet-500"
            />
            <input
              type="password"
              placeholder={t('login_password' as never)}
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-gray-200 outline-none focus:border-violet-500"
            />
            <input
              placeholder="Display Name"
              value={form.display_name}
              onChange={(e) => setForm({ ...form, display_name: e.target.value })}
              className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-gray-200 outline-none focus:border-violet-500"
            />
            <input
              placeholder="Email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-gray-200 outline-none focus:border-violet-500"
            />
            <select
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value })}
              className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-gray-200 outline-none focus:border-violet-500"
            >
              {ROLES.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
            <button
              onClick={handleAdd}
              className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-700 transition"
            >
              {t('admin_add_user' as never)}
            </button>
          </div>
          {msg && <p className="mt-2 text-sm text-red-400">{msg}</p>}
        </Card>
      )}

      {resetTarget && (
        <Card>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-300">
              {t('admin_reset_pw' as never)}: <strong>{resetTarget}</strong>
            </span>
            <input
              type="password"
              placeholder={t('admin_new_pw' as never)}
              value={newPw}
              onChange={(e) => setNewPw(e.target.value)}
              className="flex-1 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-gray-200 outline-none focus:border-violet-500"
            />
            <button
              onClick={handleResetPassword}
              className="rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700 transition"
            >
              OK
            </button>
            <button
              onClick={() => { setResetTarget(null); setNewPw(''); }}
              className="text-sm text-gray-500 hover:text-gray-300"
            >
              Cancel
            </button>
          </div>
        </Card>
      )}

      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-white/10 text-gray-500">
                <th className="px-4 py-3 font-medium">{t('login_username' as never)}</th>
                <th className="px-4 py-3 font-medium">Display Name</th>
                <th className="px-4 py-3 font-medium">{t('admin_role' as never)}</th>
                <th className="px-4 py-3 font-medium">{t('admin_status' as never)}</th>
                <th className="px-4 py-3 font-medium">Last Login</th>
                <th className="px-4 py-3 font-medium text-right">{t('admin_actions' as never)}</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.username} className="border-b border-white/5 hover:bg-white/[0.02] transition">
                  <td className="px-4 py-3 font-medium text-gray-200">{u.username}</td>
                  <td className="px-4 py-3 text-gray-400">{u.display_name}</td>
                  <td className="px-4 py-3">
                    {isAdmin && u.username !== 'admin' ? (
                      <select
                        value={u.role}
                        onChange={(e) => handleRoleChange(u.username, e.target.value)}
                        className={`rounded-md border px-2 py-1 text-xs font-medium ${ROLE_COLORS[u.role]} bg-transparent outline-none`}
                      >
                        {ROLES.map((r) => (
                          <option key={r} value={r}>{r}</option>
                        ))}
                      </select>
                    ) : (
                      <span className={`inline-block rounded-md border px-2 py-1 text-xs font-medium ${ROLE_COLORS[u.role]}`}>
                        {u.role}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1.5 text-xs ${u.is_active ? 'text-emerald-400' : 'text-gray-500'}`}>
                      <span className={`h-1.5 w-1.5 rounded-full ${u.is_active ? 'bg-emerald-400' : 'bg-gray-600'}`} />
                      {u.is_active ? t('admin_active' as never) : t('admin_inactive' as never)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500">
                    {u.last_login ? new Date(u.last_login).toLocaleDateString() : '-'}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {u.username !== 'admin' && u.username !== currentUser?.username && (
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => handleToggleActive(u)}
                          title={u.is_active ? t('admin_deactivate' as never) : t('admin_activate' as never)}
                          className="rounded p-1.5 text-gray-500 hover:bg-white/5 hover:text-amber-400 transition"
                        >
                          <Power size={14} />
                        </button>
                        {isAdmin && (
                          <>
                            <button
                              onClick={() => setResetTarget(u.username)}
                              title={t('admin_reset_pw' as never)}
                              className="rounded p-1.5 text-gray-500 hover:bg-white/5 hover:text-blue-400 transition"
                            >
                              <RotateCcw size={14} />
                            </button>
                            <button
                              onClick={() => handleDelete(u.username)}
                              title={t('admin_delete' as never)}
                              className="rounded p-1.5 text-gray-500 hover:bg-white/5 hover:text-red-400 transition"
                            >
                              <Trash2 size={14} />
                            </button>
                          </>
                        )}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
