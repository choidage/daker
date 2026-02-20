'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { t } from '@/lib/i18n';
import { Card, CardTitle } from '@/components/ui/Card';
import { Users, FileText, AlertTriangle } from 'lucide-react';

interface WorkZone {
  author: string;
  files: string[];
  description: string;
  declared_at: string;
}

export default function CollabPage() {
  const [zones, setZones] = useState<WorkZone[]>([]);
  const [author, setAuthor] = useState('');
  const [files, setFiles] = useState('');
  const [desc, setDesc] = useState('');
  const [conflicts, setConflicts] = useState<string[]>([]);

  const [deText, setDeText] = useState('');
  const [autoSave, setAutoSave] = useState(false);
  const [decisions, setDecisions] = useState<Array<Record<string, unknown>>>([]);
  const [deLoading, setDeLoading] = useState(false);

  useEffect(() => { fetchZones(); }, []);

  async function fetchZones() {
    try {
      const data = await api.getWorkZones();
      setZones(data.zones || []);
    } catch { /* silent */ }
  }

  async function declare() {
    if (!author.trim() || !files.trim()) return;
    setConflicts([]);
    try {
      const res = await api.declareWorkZone(
        author.trim(),
        files.split(',').map((f) => f.trim()).filter(Boolean),
        desc.trim(),
      );
      if (res.conflicts?.length) setConflicts(res.conflicts);
      setFiles('');
      setDesc('');
      fetchZones();
    } catch { /* silent */ }
  }

  async function release(name: string) {
    try {
      await api.releaseWorkZone(name);
      fetchZones();
    } catch { /* silent */ }
  }

  async function extractDecisions() {
    if (!deText.trim()) return;
    setDeLoading(true);
    try {
      const data = await api.extractDecisions(deText, autoSave);
      setDecisions(data.decisions || []);
    } catch { /* silent */ }
    setDeLoading(false);
  }

  return (
    <div className="space-y-6">
      {/* Work Zone */}
      <Card>
        <CardTitle>{t('wz_title')}</CardTitle>
        <div className="flex gap-3 mt-3">
          <input value={author} onChange={(e) => setAuthor(e.target.value)} placeholder={t('wz_author_ph')}
            className="w-40 rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-gray-200 outline-none focus:border-violet-500/50 placeholder:text-gray-500" />
          <input value={files} onChange={(e) => setFiles(e.target.value)} placeholder={t('wz_files_ph')}
            className="flex-1 rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-gray-200 outline-none focus:border-violet-500/50 placeholder:text-gray-500" />
          <input value={desc} onChange={(e) => setDesc(e.target.value)} placeholder={t('wz_desc_ph')}
            className="w-48 rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-gray-200 outline-none focus:border-violet-500/50 placeholder:text-gray-500" />
          <button onClick={declare}
            className="rounded-lg bg-violet-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-violet-500 transition-colors">
            {t('wz_declare_btn')}
          </button>
        </div>

        {conflicts.length > 0 && (
          <div className="mt-3 flex items-start gap-2 rounded-lg border border-red-500/20 bg-red-500/5 p-3">
            <AlertTriangle size={16} className="text-red-400 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-medium text-red-400">{t('wz_conflict_warn')}</p>
              {conflicts.map((c, i) => <p key={i} className="text-xs text-red-300/70 mt-0.5">{c}</p>)}
            </div>
          </div>
        )}

        <div className="mt-4 space-y-2">
          {zones.length === 0 && <p className="text-sm text-gray-500 py-4 text-center">{t('wz_empty')}</p>}
          {zones.map((z) => (
            <div key={z.author} className="flex items-center gap-4 rounded-lg border border-white/5 bg-white/[0.02] p-4">
              <Users size={18} className="text-violet-400 shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-gray-200">{z.author}</div>
                <div className="text-xs text-gray-500 mt-0.5 truncate">
                  {z.files.join(', ')}
                  {z.description && ` — ${z.description}`}
                </div>
              </div>
              <span className="text-xs text-gray-500">{new Date(z.declared_at).toLocaleTimeString()}</span>
              <button onClick={() => release(z.author)}
                className="rounded-md border border-white/10 px-3 py-1 text-xs text-gray-400 hover:text-red-400 hover:border-red-500/30 transition-colors">
                {t('wz_release')}
              </button>
            </div>
          ))}
        </div>
      </Card>

      {/* Decision Extractor */}
      <Card>
        <CardTitle>{t('de_title')}</CardTitle>
        <textarea
          value={deText}
          onChange={(e) => setDeText(e.target.value)}
          placeholder={t('de_placeholder')}
          rows={5}
          className="w-full mt-3 rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-gray-200 outline-none focus:border-violet-500/50 resize-none placeholder:text-gray-500"
        />
        <div className="flex items-center gap-4 mt-3">
          <button onClick={extractDecisions} disabled={deLoading}
            className="rounded-lg bg-violet-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-violet-500 disabled:opacity-50 transition-colors">
            {deLoading ? '...' : t('de_extract_btn')}
          </button>
          <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
            <input type="checkbox" checked={autoSave} onChange={(e) => setAutoSave(e.target.checked)}
              className="rounded border-white/20 bg-white/5 text-violet-500 focus:ring-violet-500/50" />
            {t('de_auto_save')}
          </label>
        </div>

        {decisions.length > 0 && (
          <div className="mt-4 border-t border-white/5 pt-4 space-y-3">
            {decisions.map((d, i) => (
              <div key={i} className="rounded-lg border border-white/5 bg-white/[0.02] p-4">
                <div className="flex items-center gap-2">
                  <FileText size={14} className="text-violet-400" />
                  <span className="text-sm font-medium text-gray-200">{String(d.title ?? '')}</span>
                  {d.confidence != null && (
                    <span className="ml-auto text-xs text-gray-500">{Math.round(Number(d.confidence) * 100)}%</span>
                  )}
                </div>
                {d.content != null && <p className="text-xs text-gray-400 mt-2">{String(d.content)}</p>}
                {d.adr_path != null && <p className="text-xs text-emerald-400 mt-1">{t('de_saved_adr')}: {String(d.adr_path)}</p>}
              </div>
            ))}
          </div>
        )}
        {decisions.length === 0 && deText && !deLoading && (
          <p className="text-sm text-gray-500 mt-3">{t('de_no_decisions')}</p>
        )}
      </Card>
    </div>
  );
}
