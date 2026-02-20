import * as https from 'http';
import * as vscode from 'vscode';

function getApiUrl(): string {
  return vscode.workspace.getConfiguration('vibex').get<string>('apiUrl') || 'http://127.0.0.1:8000';
}

function getAuthor(): string {
  return vscode.workspace.getConfiguration('vibex').get<string>('author') || 'anonymous';
}

async function request<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const baseUrl = getApiUrl();
  const url = `${baseUrl}${path}`;

  const options: RequestInit = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) {
    options.body = JSON.stringify(body);
  }

  const res = await fetch(url, options);
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export interface GateResult {
  gate: number;
  name: string;
  status: string;
  message: string;
  details: string[];
}

export interface PipelineResult {
  file_path: string;
  overall_status: string;
  gates: GateResult[];
}

export interface SearchResultItem {
  file_path: string;
  start_line: number;
  end_line: number;
  content: string;
  relevance_score: number;
  metadata: Record<string, string>;
}

export interface WorkZone {
  author: string;
  files: string[];
  description: string;
  declared_at: string;
}

export interface AlertItem {
  alert_id: string;
  level: string;
  title: string;
  message: string;
}

export const vibexApi = {
  gateCheck: (filePath: string) =>
    request<PipelineResult>('/api/pipeline', 'POST', { file_path: filePath, author: getAuthor(), bypass: true }),

  pipeline: (filePath: string) =>
    request<PipelineResult>('/api/pipeline', 'POST', { file_path: filePath, author: getAuthor() }),

  search: (query: string) =>
    request<{ results: SearchResultItem[]; total: number }>('/api/search', 'POST', { query, top_k: 8 }),

  getWorkZones: () =>
    request<{ zones: WorkZone[] }>('/api/work-zone/list'),

  declareZone: (files: string[], description: string) =>
    request<{ status: string; conflicts?: string[] }>('/api/work-zone/declare', 'POST', {
      author: getAuthor(),
      files,
      description,
    }),

  releaseZone: () =>
    request<{ status: string }>('/api/work-zone/release', 'POST', { author: getAuthor() }),

  getAlerts: () =>
    request<{ alerts: AlertItem[] }>('/api/alerts?active_only=true'),

  getHealth: () =>
    request<{ overall: number; gate_pass_rate: number; architecture_consistency: number; code_quality: number }>('/api/health'),

  askQuestion: (question: string) =>
    request<{ answer: string; code_references: Array<{ file: string; lines: string; score: number }> }>('/api/onboarding/qa', 'POST', { question }),
};
