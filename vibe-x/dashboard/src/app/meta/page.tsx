'use client';

import { useEffect, useState, useMemo } from 'react';
import {
  FileCode2, Zap, Database, ChevronDown, ChevronUp,
  Search, PieChart, GitBranch, Pencil, Trash2, X, Check,
  ArrowRight, CircleDot, FileQuestion,
} from 'lucide-react';
import { api, MetaInfo, MetaCoverage, DepGraph } from '@/lib/api';
import { t } from '@/lib/i18n';
import { Card, CardTitle } from '@/components/ui/Card';
import { ProgressBar } from '@/components/ui/ProgressBar';

type TabId = 'list' | 'coverage' | 'graph';

export default function MetaPage() {
  const [tab, setTab] = useState<TabId>('list');
  const [metas, setMetas] = useState<MetaInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionMsg, setActionMsg] = useState('');

  const loadMetas = () => {
    setLoading(true);
    api
      .getMetaList()
      .then((d) => setMetas(d.metas))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadMetas(); }, []);

  const handleBatchAnalyze = async () => {
    setActionMsg('Analyzing...');
    try {
      const result = await api.batchAnalyzeMeta();
      setActionMsg(`${result.count} meta files generated`);
      loadMetas();
    } catch {
      setActionMsg('Batch analysis failed');
    }
  };

  const handleIndex = async () => {
    setActionMsg('Indexing...');
    try {
      const result = await api.indexMetas();
      setActionMsg(result.message);
    } catch {
      setActionMsg('Indexing failed');
    }
  };

  const TABS: { id: TabId; label: string; icon: typeof FileCode2 }[] = [
    { id: 'list', label: t('meta_tab_list' as never), icon: FileCode2 },
    { id: 'coverage', label: t('meta_tab_coverage' as never), icon: PieChart },
    { id: 'graph', label: t('meta_tab_graph' as never), icon: GitBranch },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-100 flex items-center gap-2">
            <FileCode2 className="text-violet-400" size={22} />
            {t('meta_title' as never)}
          </h2>
          <p className="text-sm text-gray-500 mt-1">{t('meta_desc' as never)}</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={handleBatchAnalyze}
            className="flex items-center gap-2 rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-500 transition-colors">
            <Zap size={14} />
            {t('meta_batch' as never)}
          </button>
          <button onClick={handleIndex}
            className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 transition-colors">
            <Database size={14} />
            {t('meta_index' as never)}
          </button>
        </div>
      </div>

      {actionMsg && (
        <div className="rounded-lg bg-white/5 border border-white/10 px-4 py-2 text-sm text-violet-300">
          {actionMsg}
        </div>
      )}

      {/* Sub-tabs */}
      <div className="flex items-center gap-1 border-b border-white/10">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button key={id} onClick={() => setTab(id)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm border-b-2 transition-colors ${
              tab === id
                ? 'border-violet-500 text-violet-400 font-medium'
                : 'border-transparent text-gray-500 hover:text-gray-300'
            }`}>
            <Icon size={14} />
            {label}
          </button>
        ))}
        <div className="ml-auto text-sm text-gray-500">
          {t('meta_count' as never)}: <span className="text-violet-400 font-medium">{metas.length}</span>
        </div>
      </div>

      {/* Tab content */}
      {tab === 'list' && (
        <MetaListTab metas={metas} loading={loading} onRefresh={loadMetas} setActionMsg={setActionMsg} />
      )}
      {tab === 'coverage' && <CoverageTab />}
      {tab === 'graph' && <GraphTab />}
    </div>
  );
}

/* ──────────────── Tab 1: Meta List ──────────────── */

function MetaListTab({
  metas,
  loading,
  onRefresh,
  setActionMsg,
}: {
  metas: MetaInfo[];
  loading: boolean;
  onRefresh: () => void;
  setActionMsg: (msg: string) => void;
}) {
  const [search, setSearch] = useState('');
  const [expanded, setExpanded] = useState<string | null>(null);
  const [singlePath, setSinglePath] = useState('');

  const filtered = useMemo(() => {
    if (!search.trim()) return metas;
    const q = search.toLowerCase();
    return metas.filter(
      (m) =>
        m.file_path.toLowerCase().includes(q) ||
        m.purpose.toLowerCase().includes(q) ||
        m.decisions.some((d) => d.toLowerCase().includes(q)) ||
        m.dependencies.some((d) => d.toLowerCase().includes(q)),
    );
  }, [metas, search]);

  const handleSingleAnalyze = async () => {
    if (!singlePath.trim()) return;
    setActionMsg('Analyzing single file...');
    try {
      const result = await api.analyzeMeta(singlePath.trim());
      if (result.meta) {
        setActionMsg(`Generated: ${result.meta.purpose.slice(0, 60)}`);
        onRefresh();
      } else {
        setActionMsg('Analysis failed or unsupported file type');
      }
    } catch {
      setActionMsg('Single analysis failed');
    }
    setSinglePath('');
  };

  const handleDelete = async (filePath: string) => {
    if (!confirm(t('meta_delete_confirm' as never))) return;
    await api.deleteMeta(filePath);
    onRefresh();
  };

  return (
    <div className="space-y-4">
      {/* Search + Single analyze */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t('meta_search_ph' as never)}
            className="w-full rounded-lg border border-white/10 bg-white/5 pl-10 pr-4 py-2 text-sm text-gray-200 outline-none focus:border-violet-500/50 placeholder:text-gray-600"
          />
        </div>
        <input
          value={singlePath}
          onChange={(e) => setSinglePath(e.target.value)}
          placeholder={t('meta_single_ph' as never)}
          onKeyDown={(e) => e.key === 'Enter' && handleSingleAnalyze()}
          className="w-80 rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm text-gray-200 outline-none focus:border-violet-500/50 placeholder:text-gray-600"
        />
        <button onClick={handleSingleAnalyze}
          className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 transition-colors">
          {t('meta_single_btn' as never)}
        </button>
      </div>

      {loading ? (
        <div className="text-gray-500 text-center py-12">Loading...</div>
      ) : filtered.length === 0 ? (
        <div className="text-gray-500 text-center py-12">
          {search ? `No results for "${search}"` : t('meta_no_data' as never)}
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((m) => (
            <MetaCard
              key={m.file_path}
              meta={m}
              isExpanded={expanded === m.file_path}
              onToggle={() => setExpanded(expanded === m.file_path ? null : m.file_path)}
              onDelete={() => handleDelete(m.file_path)}
              onRefresh={onRefresh}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/* ──────────────── Meta Card (with edit) ──────────────── */

function MetaCard({
  meta,
  isExpanded,
  onToggle,
  onDelete,
  onRefresh,
}: {
  meta: MetaInfo;
  isExpanded: boolean;
  onToggle: () => void;
  onDelete: () => void;
  onRefresh: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({
    purpose: meta.purpose,
    decisions: meta.decisions.join('\n'),
    alternatives: meta.alternatives.join('\n'),
  });

  const fileName = meta.file_path.split(/[\\/]/).pop() ?? meta.file_path;

  const handleSave = async () => {
    await api.updateMeta(meta.file_path, {
      purpose: form.purpose,
      decisions: form.decisions.split('\n').filter(Boolean),
      alternatives: form.alternatives.split('\n').filter(Boolean),
    });
    setEditing(false);
    onRefresh();
  };

  return (
    <div className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
      <button onClick={onToggle}
        className="w-full flex items-center justify-between px-5 py-3 hover:bg-white/5 transition-colors text-left">
        <div className="flex items-center gap-3 min-w-0">
          <FileCode2 size={16} className="text-violet-400 shrink-0" />
          <div className="min-w-0">
            <p className="text-sm font-medium text-gray-200">{fileName}</p>
            <p className="text-xs text-gray-500 mt-0.5 truncate">{meta.purpose}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {meta.dependencies.length > 0 && (
            <span className="text-[10px] text-gray-500 bg-white/5 rounded-full px-2 py-0.5">
              {meta.dependencies.length} deps
            </span>
          )}
          {isExpanded ? <ChevronUp size={16} className="text-gray-500" /> : <ChevronDown size={16} className="text-gray-500" />}
        </div>
      </button>

      {isExpanded && (
        <div className="border-t border-white/5 px-5 py-4 space-y-3 text-sm">
          {editing ? (
            <EditForm form={form} setForm={setForm} onSave={handleSave} onCancel={() => setEditing(false)} />
          ) : (
            <>
              <DetailSection label={t('meta_purpose' as never)} items={[meta.purpose]} />
              {meta.decisions.length > 0 && (
                <DetailSection label={t('meta_decisions' as never)} items={meta.decisions} />
              )}
              {meta.alternatives.length > 0 && (
                <DetailSection label={t('meta_alternatives' as never)} items={meta.alternatives} />
              )}
              {meta.constraints.length > 0 && (
                <DetailSection label={t('meta_constraints' as never)} items={meta.constraints} />
              )}
              {meta.dependencies.length > 0 && (
                <DetailSection label={t('meta_deps' as never)} items={meta.dependencies} />
              )}
              <div className="flex items-center justify-between pt-2 border-t border-white/5">
                <p className="text-xs text-gray-600">
                  {meta.author} &middot; {new Date(meta.created_at).toLocaleString()}
                </p>
                <div className="flex items-center gap-2">
                  <button onClick={() => setEditing(true)}
                    className="flex items-center gap-1 rounded-md border border-white/10 px-2.5 py-1 text-xs text-gray-400 hover:text-violet-400 hover:border-violet-500/30 transition-colors">
                    <Pencil size={11} /> {t('meta_edit' as never)}
                  </button>
                  <button onClick={onDelete}
                    className="flex items-center gap-1 rounded-md border border-white/10 px-2.5 py-1 text-xs text-gray-400 hover:text-red-400 hover:border-red-500/30 transition-colors">
                    <Trash2 size={11} /> {t('meta_delete' as never)}
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

function EditForm({
  form,
  setForm,
  onSave,
  onCancel,
}: {
  form: { purpose: string; decisions: string; alternatives: string };
  setForm: (f: { purpose: string; decisions: string; alternatives: string }) => void;
  onSave: () => void;
  onCancel: () => void;
}) {
  return (
    <div className="space-y-3">
      <div>
        <label className="text-xs text-gray-400 mb-1 block">{t('meta_purpose' as never)}</label>
        <input value={form.purpose} onChange={(e) => setForm({ ...form, purpose: e.target.value })}
          className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-gray-200 outline-none focus:border-violet-500" />
      </div>
      <div>
        <label className="text-xs text-gray-400 mb-1 block">{t('meta_decisions' as never)}</label>
        <textarea value={form.decisions} onChange={(e) => setForm({ ...form, decisions: e.target.value })} rows={3}
          className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-gray-200 outline-none focus:border-violet-500 resize-none"
          placeholder="One decision per line" />
      </div>
      <div>
        <label className="text-xs text-gray-400 mb-1 block">{t('meta_alternatives' as never)}</label>
        <textarea value={form.alternatives} onChange={(e) => setForm({ ...form, alternatives: e.target.value })} rows={2}
          className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-gray-200 outline-none focus:border-violet-500 resize-none"
          placeholder="One alternative per line" />
      </div>
      <div className="flex items-center gap-2">
        <button onClick={onSave}
          className="flex items-center gap-1 rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-500 transition-colors">
          <Check size={14} /> {t('meta_save' as never)}
        </button>
        <button onClick={onCancel}
          className="flex items-center gap-1 rounded-lg border border-white/10 px-4 py-2 text-sm text-gray-400 hover:text-gray-200 transition-colors">
          <X size={14} /> {t('meta_cancel' as never)}
        </button>
      </div>
    </div>
  );
}

/* ──────────────── Tab 2: Coverage ──────────────── */

function CoverageTab() {
  const [data, setData] = useState<MetaCoverage | null>(null);

  useEffect(() => {
    api.getMetaCoverage().then(setData).catch(() => {});
  }, []);

  if (!data) return <div className="text-gray-500 text-center py-12">Loading...</div>;

  const rateColor = data.coverage_rate >= 70 ? 'text-emerald-400' : data.coverage_rate >= 40 ? 'text-amber-400' : 'text-red-400';
  const barColor = data.coverage_rate >= 70 ? 'bg-emerald-500' : data.coverage_rate >= 40 ? 'bg-amber-500' : 'bg-red-500';

  return (
    <div className="space-y-6">
      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <p className="text-xs text-gray-500">{t('meta_coverage' as never)}</p>
          <p className={`text-3xl font-bold mt-1 ${rateColor}`}>{data.coverage_rate}%</p>
          <ProgressBar value={data.coverage_rate} color={barColor} className="mt-3" />
        </Card>
        <Card>
          <p className="text-xs text-gray-500">Source Files</p>
          <p className="text-3xl font-bold text-gray-100 mt-1">{data.total_source_files}</p>
        </Card>
        <Card>
          <p className="text-xs text-gray-500">{t('meta_covered' as never)}</p>
          <p className="text-3xl font-bold text-emerald-400 mt-1">{data.covered}</p>
        </Card>
        <Card>
          <p className="text-xs text-gray-500">{t('meta_uncovered' as never)}</p>
          <p className="text-3xl font-bold text-red-400 mt-1">{data.uncovered}</p>
        </Card>
      </div>

      {/* Uncovered files */}
      {data.uncovered_files.length > 0 && (
        <Card>
          <CardTitle>{t('meta_uncovered_files' as never)}</CardTitle>
          <div className="mt-3 space-y-1.5">
            {data.uncovered_files.map((f) => (
              <div key={f} className="flex items-center gap-2 text-sm text-gray-400">
                <FileQuestion size={14} className="text-red-400/60 shrink-0" />
                <span className="font-mono text-xs">{f}</span>
              </div>
            ))}
          </div>
          {data.uncovered > data.uncovered_files.length && (
            <p className="text-xs text-gray-600 mt-2">
              ... and {data.uncovered - data.uncovered_files.length} more
            </p>
          )}
        </Card>
      )}

      {data.uncovered === 0 && (
        <Card>
          <div className="text-center py-8">
            <Check size={32} className="text-emerald-400 mx-auto mb-2" />
            <p className="text-sm text-gray-300">All source files have meta coverage!</p>
          </div>
        </Card>
      )}
    </div>
  );
}

/* ──────────────── Tab 3: Dependency Graph ──────────────── */

function GraphTab() {
  const [data, setData] = useState<DepGraph | null>(null);
  const [filterNode, setFilterNode] = useState('');

  useEffect(() => {
    api.getMetaDepGraph().then(setData).catch(() => {});
  }, []);

  if (!data) return <div className="text-gray-500 text-center py-12">Loading...</div>;

  const filteredEdges = filterNode
    ? data.edges.filter(
        (e) =>
          e.from.toLowerCase().includes(filterNode.toLowerCase()) ||
          e.to.toLowerCase().includes(filterNode.toLowerCase()),
      )
    : data.edges;

  const filteredNodes = filterNode
    ? data.nodes.filter((n) => n.id.toLowerCase().includes(filterNode.toLowerCase()))
    : data.nodes;

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <div className="flex items-center gap-3">
            <CircleDot size={18} className="text-violet-400" />
            <div>
              <p className="text-2xl font-bold text-gray-100">{data.total_nodes}</p>
              <p className="text-xs text-gray-500">{t('meta_dep_nodes' as never)}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <ArrowRight size={18} className="text-indigo-400" />
            <div>
              <p className="text-2xl font-bold text-gray-100">{data.total_edges}</p>
              <p className="text-xs text-gray-500">{t('meta_dep_edges' as never)}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Filter */}
      <div className="relative">
        <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
        <input
          value={filterNode}
          onChange={(e) => setFilterNode(e.target.value)}
          placeholder="Filter nodes..."
          className="w-full rounded-lg border border-white/10 bg-white/5 pl-10 pr-4 py-2 text-sm text-gray-200 outline-none focus:border-violet-500/50 placeholder:text-gray-600"
        />
      </div>

      {/* Node list */}
      <Card>
        <CardTitle>{t('meta_dep_nodes' as never)} ({filteredNodes.length})</CardTitle>
        <div className="mt-3 space-y-2 max-h-64 overflow-y-auto">
          {filteredNodes.map((n) => (
            <div key={n.id}
              className="flex items-center justify-between rounded-lg bg-white/[0.02] border border-white/5 px-4 py-2.5">
              <div className="flex items-center gap-2">
                <CircleDot size={12} className={n.dep_count > 3 ? 'text-amber-400' : 'text-violet-400'} />
                <span className="text-sm font-mono text-gray-200">{n.id}</span>
              </div>
              <div className="flex items-center gap-3">
                {n.purpose && (
                  <span className="text-xs text-gray-500 max-w-xs truncate">{n.purpose}</span>
                )}
                <span className="text-[10px] text-gray-600 bg-white/5 rounded-full px-2 py-0.5">
                  {n.dep_count} deps
                </span>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Edge table */}
      <Card>
        <CardTitle>{t('meta_dep_edges' as never)} ({filteredEdges.length})</CardTitle>
        <div className="mt-3 overflow-x-auto max-h-80 overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-[#1e1e2e]">
              <tr className="text-gray-500 text-xs border-b border-white/5">
                <th className="py-2 text-left pl-4">{t('meta_dep_from' as never)}</th>
                <th className="py-2 text-center w-8"></th>
                <th className="py-2 text-left">{t('meta_dep_to' as never)}</th>
                <th className="py-2 text-left pr-4">{t('meta_dep_module' as never)}</th>
              </tr>
            </thead>
            <tbody>
              {filteredEdges.slice(0, 100).map((e, i) => (
                <tr key={i} className="border-b border-white/5 hover:bg-white/[0.02]">
                  <td className="py-2 pl-4 font-mono text-violet-400 text-xs">{e.from}</td>
                  <td className="py-2 text-center">
                    <ArrowRight size={12} className="text-gray-600 mx-auto" />
                  </td>
                  <td className="py-2 font-mono text-indigo-400 text-xs">{e.to}</td>
                  <td className="py-2 pr-4 text-xs text-gray-500">{e.module}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {filteredEdges.length > 100 && (
            <p className="text-xs text-gray-600 text-center py-2">
              Showing 100 of {filteredEdges.length} edges
            </p>
          )}
        </div>
      </Card>
    </div>
  );
}

/* ──────────────── Shared ──────────────── */

function DetailSection({ label, items }: { label: string; items: string[] }) {
  return (
    <div>
      <p className="text-xs font-medium text-gray-400 mb-1">{label}</p>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className="text-gray-300 text-xs pl-3 border-l border-violet-500/30">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
