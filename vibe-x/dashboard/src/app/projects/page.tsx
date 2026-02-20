'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { t } from '@/lib/i18n';
import { Card } from '@/components/ui/Card';
import { ProgressBar } from '@/components/ui/ProgressBar';
import type { ProjectInfo, ProjectMember, AggregateSummary } from '@/lib/api';
import {
  FolderKanban, Users, Plus, AlertTriangle, Activity, Tag,
  UserPlus, Shield, ChevronDown, ChevronUp, Crown, Wrench, Eye, X,
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';

const PROJECT_ROLES = ['owner', 'maintainer', 'developer', 'viewer'] as const;
type ProjectRoleType = typeof PROJECT_ROLES[number];

const ROLE_ICON: Record<ProjectRoleType, typeof Crown> = {
  owner: Crown,
  maintainer: Shield,
  developer: Wrench,
  viewer: Eye,
};

const ROLE_COLOR: Record<ProjectRoleType, string> = {
  owner: 'text-amber-400 bg-amber-500/15 border-amber-500/30',
  maintainer: 'text-violet-400 bg-violet-500/15 border-violet-500/30',
  developer: 'text-emerald-400 bg-emerald-500/15 border-emerald-500/30',
  viewer: 'text-gray-400 bg-white/5 border-white/10',
};

const ROLE_I18N: Record<ProjectRoleType, string> = {
  owner: 'members_owner',
  maintainer: 'members_maintainer',
  developer: 'members_developer',
  viewer: 'members_viewer',
};

export default function ProjectsPage() {
  const [summary, setSummary] = useState<AggregateSummary | null>(null);
  const [projects, setProjects] = useState<ProjectInfo[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({
    project_id: '',
    name: '',
    root_path: '',
    description: '',
    team: '',
    tags: '',
  });
  const [msg, setMsg] = useState('');

  const loadData = useCallback(async () => {
    try {
      const [projRes, aggRes] = await Promise.all([
        api.getProjects(),
        api.getAggregateSummary(),
      ]);
      setProjects(projRes.projects);
      setSummary(aggRes);
    } catch { /* silent */ }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  async function handleRegister() {
    setMsg('');
    const res = await api.registerProject({
      project_id: form.project_id,
      name: form.name,
      root_path: form.root_path,
      description: form.description,
      team: form.team ? form.team.split(',').map((s) => s.trim()) : [],
      tags: form.tags ? form.tags.split(',').map((s) => s.trim()) : [],
    });
    if (res.success) {
      setShowAdd(false);
      setForm({ project_id: '', name: '', root_path: '', description: '', team: '', tags: '' });
      loadData();
    } else {
      setMsg(res.error ?? 'Error');
    }
  }

  async function handleUnregister(pid: string) {
    await api.unregisterProject(pid);
    loadData();
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-100">{t('projects_title' as never)}</h1>
        <button
          onClick={() => setShowAdd(!showAdd)}
          className="flex items-center gap-2 rounded-lg bg-violet-500/15 border border-violet-500/30 px-4 py-2 text-sm text-violet-400 hover:bg-violet-500/25 transition"
        >
          <Plus size={16} />
          {t('projects_add' as never)}
        </button>
      </div>

      {summary && (
        <div className="grid grid-cols-2 gap-4">
          <Card>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-violet-500/15">
                <FolderKanban size={20} className="text-violet-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-100">{summary.total_projects}</p>
                <p className="text-xs text-gray-500">{t('projects_total' as never)}</p>
              </div>
            </div>
          </Card>
          <Card>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/15">
                <Users size={20} className="text-emerald-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-100">{summary.total_team_members}</p>
                <p className="text-xs text-gray-500">{t('projects_members' as never)}</p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {showAdd && (
        <Card>
          <h3 className="text-sm font-medium text-gray-300 mb-3">{t('projects_register' as never)}</h3>
          <div className="grid grid-cols-2 gap-3">
            <input
              placeholder={t('projects_id' as never)}
              value={form.project_id}
              onChange={(e) => setForm({ ...form, project_id: e.target.value })}
              className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-gray-200 outline-none focus:border-violet-500"
            />
            <input
              placeholder={t('projects_name' as never)}
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-gray-200 outline-none focus:border-violet-500"
            />
            <input
              placeholder={t('projects_path' as never)}
              value={form.root_path}
              onChange={(e) => setForm({ ...form, root_path: e.target.value })}
              className="col-span-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-gray-200 outline-none focus:border-violet-500"
            />
            <input
              placeholder={t('projects_desc' as never)}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="col-span-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-gray-200 outline-none focus:border-violet-500"
            />
            <input
              placeholder={t('projects_team' as never)}
              value={form.team}
              onChange={(e) => setForm({ ...form, team: e.target.value })}
              className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-gray-200 outline-none focus:border-violet-500"
            />
            <input
              placeholder={t('projects_tags' as never)}
              value={form.tags}
              onChange={(e) => setForm({ ...form, tags: e.target.value })}
              className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-gray-200 outline-none focus:border-violet-500"
            />
          </div>
          <div className="mt-3 flex items-center gap-3">
            <button
              onClick={handleRegister}
              className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-700 transition"
            >
              {t('projects_register' as never)}
            </button>
            {msg && <span className="text-sm text-red-400">{msg}</span>}
          </div>
        </Card>
      )}

      {projects.length === 0 ? (
        <div className="text-center py-12 text-gray-500">{t('projects_empty' as never)}</div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {projects.map((p) => (
            <ProjectCard
              key={p.project_id}
              project={p}
              onUnregister={handleUnregister}
              onRefresh={loadData}
            />
          ))}
        </div>
      )}
    </div>
  );
}


function ProjectCard({
  project: p,
  onUnregister,
  onRefresh,
}: {
  project: ProjectInfo;
  onUnregister: (id: string) => void;
  onRefresh: () => void;
}) {
  const { user } = useAuth();
  const [expanded, setExpanded] = useState(false);
  const [members, setMembers] = useState<ProjectMember[]>(p.members ?? []);
  const [showAddMember, setShowAddMember] = useState(false);
  const [newMember, setNewMember] = useState({ username: '', role: 'developer' });
  const [memberMsg, setMemberMsg] = useState('');

  const currentUsername = user?.username ?? 'admin';

  const currentMember = members.find((m) => m.username === currentUsername);
  const canManageMembers = user?.role === 'admin' || (
    currentMember && (currentMember.project_role === 'owner' || currentMember.project_role === 'maintainer')
  );

  const healthScore = p.health_score ?? 0;
  const healthColor = healthScore >= 70 ? 'text-emerald-400' : healthScore >= 40 ? 'text-amber-400' : 'text-red-400';
  const barColor = healthScore >= 70 ? 'bg-emerald-500' : healthScore >= 40 ? 'bg-amber-500' : 'bg-red-500';

  async function loadMembers() {
    try {
      const res = await api.getProjectMembers(p.project_id);
      setMembers(res.members);
    } catch { /* silent */ }
  }

  async function handleAddMember() {
    setMemberMsg('');
    if (!newMember.username.trim()) return;
    const res = await api.addProjectMember(
      p.project_id, newMember.username.trim(), newMember.role, currentUsername,
    );
    if (res.success) {
      setShowAddMember(false);
      setNewMember({ username: '', role: 'developer' });
      loadMembers();
      onRefresh();
    } else {
      setMemberMsg(res.error ?? 'Error');
    }
  }

  async function handleRemoveMember(username: string) {
    if (!confirm(t('members_confirm_remove' as never))) return;
    await api.removeProjectMember(p.project_id, username, currentUsername);
    loadMembers();
    onRefresh();
  }

  async function handleChangeRole(username: string, newRole: string) {
    await api.changeProjectMemberRole(p.project_id, username, newRole, currentUsername);
    loadMembers();
  }

  function handleExpandToggle() {
    const next = !expanded;
    setExpanded(next);
    if (next) loadMembers();
  }

  return (
    <Card>
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-base font-semibold text-gray-100">{p.name}</h3>
          <p className="text-xs text-gray-500 mt-0.5">{p.project_id}</p>
        </div>
        <button
          onClick={() => onUnregister(p.project_id)}
          className="text-xs text-gray-600 hover:text-red-400 transition"
        >
          비활성화
        </button>
      </div>

      {p.description && (
        <p className="text-sm text-gray-400 mb-3">{p.description}</p>
      )}

      <div className="mb-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-gray-500">{t('projects_health' as never)}</span>
          <span className={`text-sm font-bold ${healthColor}`}>{healthScore}%</span>
        </div>
        <ProgressBar value={healthScore} color={barColor} />
      </div>

      <div className="flex items-center gap-4 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <Activity size={12} />
          {p.today_gate_runs ?? 0} {t('projects_gates' as never)}
        </span>
        <span className="flex items-center gap-1">
          <AlertTriangle size={12} />
          {p.active_alerts ?? 0} {t('projects_alerts' as never)}
        </span>
        <span className="flex items-center gap-1">
          <Users size={12} />
          {members.length || p.team?.length || 0}
        </span>
      </div>

      {p.tags && p.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-3">
          {p.tags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1 rounded-full bg-white/5 border border-white/10 px-2 py-0.5 text-[10px] text-gray-400"
            >
              <Tag size={9} />
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Members Toggle */}
      <button
        onClick={handleExpandToggle}
        className="mt-3 flex w-full items-center justify-between rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-xs text-gray-400 hover:bg-white/10 transition"
      >
        <span className="flex items-center gap-1.5">
          <Users size={13} />
          {t('members_title' as never)} ({members.length || p.team?.length || 0})
        </span>
        {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {/* Members Panel */}
      {expanded && (
        <div className="mt-2 space-y-2">
          {members.length === 0 ? (
            <p className="text-xs text-gray-600 text-center py-2">{t('members_empty' as never)}</p>
          ) : (
            members.map((m) => {
              const role = m.project_role as ProjectRoleType;
              const RoleIcon = ROLE_ICON[role] ?? Eye;
              const colorCls = ROLE_COLOR[role] ?? ROLE_COLOR.viewer;
              const isOwner = role === 'owner';

              return (
                <div
                  key={m.username}
                  className="flex items-center justify-between rounded-lg bg-white/[0.03] border border-white/5 px-3 py-2"
                >
                  <div className="flex items-center gap-2">
                    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] ${colorCls}`}>
                      <RoleIcon size={10} />
                      {t(ROLE_I18N[role] as never)}
                    </span>
                    <span className="text-sm text-gray-200">{m.username}</span>
                  </div>
                  {canManageMembers && !isOwner && (
                    <div className="flex items-center gap-1">
                      <select
                        value={role}
                        onChange={(e) => handleChangeRole(m.username, e.target.value)}
                        className="rounded border border-white/10 bg-white/5 px-1.5 py-0.5 text-[10px] text-gray-400 outline-none"
                      >
                        <option value="maintainer">{t('members_maintainer' as never)}</option>
                        <option value="developer">{t('members_developer' as never)}</option>
                        <option value="viewer">{t('members_viewer' as never)}</option>
                      </select>
                      <button
                        onClick={() => handleRemoveMember(m.username)}
                        className="rounded p-0.5 text-gray-600 hover:text-red-400 transition"
                      >
                        <X size={13} />
                      </button>
                    </div>
                  )}
                </div>
              );
            })
          )}

          {/* Add Member */}
          {canManageMembers && !showAddMember && (
            <button
              onClick={() => setShowAddMember(true)}
              className="flex w-full items-center justify-center gap-1 rounded-lg border border-dashed border-white/10 py-2 text-xs text-gray-500 hover:border-violet-500/40 hover:text-violet-400 transition"
            >
              <UserPlus size={13} />
              {t('members_add' as never)}
            </button>
          )}

          {canManageMembers && showAddMember && (
            <div className="flex items-center gap-2">
              <input
                placeholder={t('members_username' as never)}
                value={newMember.username}
                onChange={(e) => setNewMember({ ...newMember, username: e.target.value })}
                className="flex-1 rounded-lg border border-white/10 bg-white/5 px-2 py-1.5 text-xs text-gray-200 outline-none focus:border-violet-500"
              />
              <select
                value={newMember.role}
                onChange={(e) => setNewMember({ ...newMember, role: e.target.value })}
                className="rounded-lg border border-white/10 bg-white/5 px-2 py-1.5 text-xs text-gray-400 outline-none"
              >
                <option value="maintainer">{t('members_maintainer' as never)}</option>
                <option value="developer">{t('members_developer' as never)}</option>
                <option value="viewer">{t('members_viewer' as never)}</option>
              </select>
              <button
                onClick={handleAddMember}
                className="rounded-lg bg-violet-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-violet-700 transition"
              >
                {t('members_add' as never)}
              </button>
              <button
                onClick={() => { setShowAddMember(false); setMemberMsg(''); }}
                className="rounded p-1 text-gray-500 hover:text-gray-300 transition"
              >
                <X size={14} />
              </button>
            </div>
          )}

          {memberMsg && (
            <p className="text-xs text-red-400 text-center">{memberMsg}</p>
          )}
        </div>
      )}
    </Card>
  );
}
