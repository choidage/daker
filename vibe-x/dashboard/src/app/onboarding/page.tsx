'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { t } from '@/lib/i18n';
import { Card, CardTitle } from '@/components/ui/Card';
import { MessageSquare, BookOpen, FolderOpen, Terminal } from 'lucide-react';

export default function OnboardingPage() {
  const [answer, setAnswer] = useState('');
  const [question, setQuestion] = useState('');
  const [codeRefs, setCodeRefs] = useState<Array<{ file: string; lines: string; score: number; name: string }>>([]);
  const [asking, setAsking] = useState(false);
  const [briefing, setBriefing] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    api.getOnboarding().then(setBriefing).catch(() => {});
  }, []);

  async function ask() {
    if (!question.trim()) return;
    setAsking(true);
    setAnswer('');
    setCodeRefs([]);
    try {
      const data = await api.askQuestion(question.trim());
      setAnswer(data.answer);
      setCodeRefs(data.code_references || []);
    } catch (err) {
      setAnswer(err instanceof Error ? err.message : 'Error');
    }
    setAsking(false);
  }

  return (
    <div className="space-y-6">
      {/* Q&A */}
      <Card>
        <CardTitle>{t('qa_title')}</CardTitle>
        <div className="flex gap-3 mt-3">
          <div className="relative flex-1">
            <MessageSquare size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder={t('qa_placeholder')}
              onKeyDown={(e) => e.key === 'Enter' && ask()}
              className="w-full rounded-lg border border-white/10 bg-white/5 pl-11 pr-4 py-2.5 text-sm text-gray-200 outline-none focus:border-violet-500/50 transition-colors placeholder:text-gray-500"
            />
          </div>
          <button onClick={ask} disabled={asking}
            className="rounded-lg bg-violet-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-violet-500 disabled:opacity-50 transition-colors">
            {asking ? '...' : t('qa_ask_btn')}
          </button>
        </div>

        {answer && (
          <div className="mt-4 rounded-lg border border-white/5 bg-white/[0.02] p-5">
            <div className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap"
              dangerouslySetInnerHTML={{
                __html: answer
                  .replace(/`([^`]+)`/g, '<code class="rounded bg-violet-500/10 px-1.5 py-0.5 text-xs text-violet-400 font-mono">$1</code>')
                  .replace(/\*\*([^*]+)\*\*/g, '<strong class="text-gray-200">$1</strong>')
                  .replace(/\n/g, '<br/>'),
              }}
            />
            {codeRefs.length > 0 && (
              <div className="mt-4 border-t border-white/5 pt-3">
                <p className="text-xs text-gray-500 mb-2">Code References:</p>
                {codeRefs.map((ref, i) => (
                  <div key={i} className="text-xs text-gray-400 py-0.5 font-mono">
                    {ref.file}:{ref.lines} {ref.name && `(${ref.name})`} — {(ref.score * 100).toFixed(0)}%
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Briefing */}
      {briefing && (
        <>
          <Card>
            <CardTitle>{t('onboarding_guide')}</CardTitle>
            <p className="text-sm text-gray-400 mt-2 leading-relaxed">{t('ob_project_desc')}</p>
            <ArchitectureLayers />
          </Card>

          <div className="grid grid-cols-2 gap-6">
            <Card>
              <CardTitle>{t('ob_modules')}</CardTitle>
              <ModuleList briefing={briefing} />
            </Card>
            <Card>
              <CardTitle>{t('ob_quickstart')}</CardTitle>
              <QuickStart />
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

function ArchitectureLayers() {
  const layers = [
    { num: 5, name: 'Team Intelligence Dashboard', color: 'from-violet-500/20 to-violet-500/5', border: 'border-violet-500/20' },
    { num: 4, name: 'Collaboration Orchestrator', color: 'from-blue-500/20 to-blue-500/5', border: 'border-blue-500/20' },
    { num: 3, name: 'Multi-Agent Quality Gate', color: 'from-emerald-500/20 to-emerald-500/5', border: 'border-emerald-500/20' },
    { num: 2, name: 'RAG Memory Engine', color: 'from-yellow-500/20 to-yellow-500/5', border: 'border-yellow-500/20' },
    { num: 1, name: 'Structured Prompts (PACT-D)', color: 'from-red-500/20 to-red-500/5', border: 'border-red-500/20' },
  ];
  return (
    <div className="mt-4 space-y-2">
      {layers.map((l) => (
        <div key={l.num} className={`rounded-lg border ${l.border} bg-gradient-to-r ${l.color} px-4 py-2.5 flex items-center gap-3`}>
          <span className="text-xs font-bold text-gray-400 w-6">L{l.num}</span>
          <span className="text-sm text-gray-300">{l.name}</span>
        </div>
      ))}
    </div>
  );
}

function ModuleList({ briefing }: { briefing: Record<string, unknown> }) {
  const modules = (briefing.key_modules as Array<{ layer: string; files: string[]; count: number }>) ?? [];
  return (
    <div className="mt-3 space-y-2">
      {modules.map((m) => (
        <div key={m.layer} className="flex items-center gap-3 text-sm">
          <FolderOpen size={14} className="text-violet-400" />
          <span className="text-gray-300 font-mono text-xs">{m.layer}</span>
          <span className="ml-auto text-xs text-gray-500">{m.count} files</span>
        </div>
      ))}
    </div>
  );
}

function QuickStart() {
  const steps = [
    'Python 3.10+ 환경 확인',
    'pip install -r requirements.txt',
    'python cli.py index . (코드베이스 인덱싱)',
    'python cli.py pipeline <파일> (6-Gate 실행)',
    'python server.py (대시보드 서버 시작)',
  ];
  return (
    <div className="mt-3 space-y-2">
      {steps.map((s, i) => (
        <div key={i} className="flex items-start gap-3 text-sm">
          <Terminal size={14} className="text-gray-500 mt-0.5 shrink-0" />
          <span className="text-gray-400 text-xs font-mono">{s}</span>
        </div>
      ))}
    </div>
  );
}
