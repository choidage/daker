const API_BASE = '';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
  return res.json();
}

export interface DashboardData {
  timestamp: string;
  today: {
    date: string;
    gate_runs: number;
    gate_passed: number;
    gate_failed: number;
    gate_warned: number;
    pass_rate: number;
    files_indexed: number;
    searches: number;
    decisions: number;
    ai_cost: number;
  };
  weekly_trend: Array<{
    date: string;
    gate_runs: number;
    passed: number;
    failed: number;
    cost: number;
    searches: number;
  }>;
  cumulative: {
    total_gate_runs: number;
    total_passed: number;
    overall_pass_rate: number;
    total_cost_usd: number;
    total_files_indexed: number;
    days_tracked: number;
  };
  recent_gates: Array<{
    gate: number;
    name: string;
    status: string;
    message: string;
    timestamp: string;
  }>;
  gate_pass_rates: number[];
  team: Array<{
    name: string;
    active_files: number;
    gate_runs: number;
    status: string;
    last_activity: string;
  }>;
  health_score: number;
}

export interface HealthBreakdown {
  overall: number;
  gate_pass_rate: number;
  architecture_consistency: number;
  code_quality: number;
  activity_index: number;
  tech_debt_items: Array<{
    gate: number;
    issue: string;
    count: number;
    suggestion: string;
    severity: string;
  }>;
}

export interface AlertData {
  alert_id: string;
  level: 'info' | 'warning' | 'critical';
  title: string;
  message: string;
  metric_name: string;
  current_value: number;
  threshold: number;
  created_at: string;
  acknowledged: boolean;
}

export interface AuthUser {
  username: string;
  role: 'admin' | 'lead' | 'developer' | 'viewer';
  display_name: string;
  email: string;
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

export interface LoginResponse {
  success: boolean;
  token?: string;
  user?: AuthUser;
  error?: string;
}

export interface MetaInfo {
  file_path: string;
  purpose: string;
  decisions: string[];
  alternatives: string[];
  constraints: string[];
  dependencies: string[];
  created_at: string;
  author: string;
}

export interface MetaCoverage {
  total_source_files: number;
  covered: number;
  uncovered: number;
  coverage_rate: number;
  uncovered_files: string[];
}

export interface DepGraph {
  nodes: Array<{ id: string; purpose: string; dep_count: number }>;
  edges: Array<{ from: string; to: string; module: string }>;
  total_nodes: number;
  total_edges: number;
}

export interface ProjectMember {
  username: string;
  project_role: 'owner' | 'maintainer' | 'developer' | 'viewer';
  joined_at: string;
}

export interface ProjectInfo {
  project_id: string;
  name: string;
  root_path: string;
  description: string;
  team: string[];
  members: ProjectMember[];
  created_at: string;
  is_active: boolean;
  tags: string[];
  health_score?: number;
  today_gate_runs?: number;
  today_pass_rate?: number;
  active_alerts?: number;
  team_size?: number;
}

export interface AggregateSummary {
  total_projects: number;
  total_team_members: number;
  projects: ProjectInfo[];
}

export interface PipelineResult {
  file_path: string;
  overall_status: string;
  gates: Array<{
    gate: number;
    name: string;
    status: string;
    message: string;
    details: string[];
  }>;
}

export interface SearchResult {
  file_path: string;
  start_line: number;
  end_line: number;
  content: string;
  relevance_score: number;
  metadata: Record<string, string>;
}

function getToken(): string {
  if (typeof window === 'undefined') return '';
  return localStorage.getItem('vibe-x-token') ?? '';
}

function authHeaders(): HeadersInit {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function authRequest<T>(path: string, options?: RequestInit): Promise<T> {
  return request<T>(path, {
    ...options,
    headers: { ...authHeaders(), ...options?.headers },
  });
}

export const api = {
  getDashboard: () => request<DashboardData>('/api/dashboard'),
  getHealth: () => request<HealthBreakdown>('/api/health'),
  getAlerts: (activeOnly = true) =>
    request<{ alerts: AlertData[] }>(`/api/alerts?active_only=${activeOnly}`),
  acknowledgeAlert: (alertId: string) =>
    request<{ success: boolean }>('/api/alerts/acknowledge', {
      method: 'POST',
      body: JSON.stringify({ alert_id: alertId }),
    }),
  evaluateAlerts: () =>
    request<{ new_alerts: number }>('/api/alerts/evaluate', { method: 'POST' }),

  runPipeline: (filePath: string, author: string) =>
    request<PipelineResult>('/api/pipeline', {
      method: 'POST',
      body: JSON.stringify({ file_path: filePath, author }),
    }),

  getOnboarding: () => request<Record<string, unknown>>('/api/onboarding'),
  askQuestion: (question: string) =>
    request<{
      question: string;
      answer: string;
      code_references: Array<{ file: string; lines: string; score: number; name: string }>;
      doc_sources: string[];
    }>('/api/onboarding/qa', {
      method: 'POST',
      body: JSON.stringify({ question }),
    }),

  getFeedback: () =>
    request<{
      total_failures: number;
      total_runs: number;
      failure_rate: number;
      patterns: Array<{ gate: string; count: number }>;
      top_messages: Array<{ message: string; count: number }>;
      suggestions: string[];
    }>('/api/feedback'),

  searchCode: (query: string) =>
    request<{ results: SearchResult[]; total: number }>('/api/search', {
      method: 'POST',
      body: JSON.stringify({ query, top_k: 10 }),
    }),
  getRagStats: () =>
    request<{ total_chunks: number; collection: string; status: string }>('/api/rag/stats'),
  reindex: () => request<{ indexed: number }>('/api/index', { method: 'POST' }),

  getWorkZones: () =>
    request<{ zones: Array<{ author: string; files: string[]; description: string; declared_at: string }> }>(
      '/api/work-zone/list',
    ),
  declareWorkZone: (author: string, files: string[], description: string) =>
    request<{ status: string; conflicts?: string[] }>('/api/work-zone/declare', {
      method: 'POST',
      body: JSON.stringify({ author, files, description }),
    }),
  releaseWorkZone: (author: string) =>
    request<{ status: string }>('/api/work-zone/release', {
      method: 'POST',
      body: JSON.stringify({ author }),
    }),

  extractDecisions: (text: string, autoSave: boolean) =>
    request<{ total: number; decisions: Array<Record<string, unknown>> }>('/api/decision/extract', {
      method: 'POST',
      body: JSON.stringify({ text, auto_save: autoSave }),
    }),

  login: (username: string, password: string) =>
    request<LoginResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),

  logout: () =>
    authRequest<{ success: boolean }>('/api/auth/logout', { method: 'POST' }),

  getMe: () =>
    authRequest<{ success: boolean; user?: AuthUser; error?: string }>('/api/auth/me'),

  getUsers: () =>
    authRequest<{ success: boolean; users?: AuthUser[]; error?: string }>('/api/auth/users'),

  registerUser: (data: { username: string; password: string; role: string; display_name: string; email: string }) =>
    authRequest<{ success: boolean; user?: AuthUser; error?: string }>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateRole: (username: string, role: string) =>
    authRequest<{ success: boolean; error?: string }>('/api/auth/role', {
      method: 'POST',
      body: JSON.stringify({ username, role }),
    }),

  deactivateUser: (username: string) =>
    authRequest<{ success: boolean; error?: string }>('/api/auth/deactivate', {
      method: 'POST',
      body: JSON.stringify({ username }),
    }),

  activateUser: (username: string) =>
    authRequest<{ success: boolean; error?: string }>('/api/auth/activate', {
      method: 'POST',
      body: JSON.stringify({ username }),
    }),

  deleteUser: (username: string) =>
    authRequest<{ success: boolean; error?: string }>('/api/auth/delete', {
      method: 'POST',
      body: JSON.stringify({ username }),
    }),

  resetPassword: (username: string, newPassword: string) =>
    authRequest<{ success: boolean; error?: string }>('/api/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({ username, new_password: newPassword }),
    }),

  getProjects: (activeOnly = true) =>
    request<{ projects: ProjectInfo[] }>(`/api/projects?active_only=${activeOnly}`),

  registerProject: (data: { project_id: string; name: string; root_path: string; description?: string; team?: string[]; tags?: string[] }) =>
    request<{ success: boolean; project?: ProjectInfo; error?: string }>('/api/projects/register', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  unregisterProject: (projectId: string) =>
    request<{ success: boolean }>(`/api/projects/${projectId}/unregister`, { method: 'POST' }),

  getAggregateSummary: () =>
    request<AggregateSummary>('/api/projects/summary/aggregate'),

  getProjectDashboard: (projectId: string) =>
    request<DashboardData>(`/api/projects/${projectId}/dashboard`),

  getProjectHealth: (projectId: string) =>
    request<HealthBreakdown>(`/api/projects/${projectId}/health`),

  getProjectAlerts: (projectId: string) =>
    request<{ alerts: AlertData[] }>(`/api/projects/${projectId}/alerts`),

  getProjectMembers: (projectId: string) =>
    request<{ members: ProjectMember[] }>(`/api/projects/${projectId}/members`),

  addProjectMember: (projectId: string, username: string, projectRole: string, requester: string) =>
    request<{ success: boolean; member?: ProjectMember; error?: string }>(
      `/api/projects/${projectId}/members/add`,
      {
        method: 'POST',
        body: JSON.stringify({ username, project_role: projectRole, requester }),
      },
    ),

  removeProjectMember: (projectId: string, username: string, requester: string) =>
    request<{ success: boolean; error?: string }>(
      `/api/projects/${projectId}/members/remove`,
      {
        method: 'POST',
        body: JSON.stringify({ username, requester }),
      },
    ),

  changeProjectMemberRole: (projectId: string, username: string, projectRole: string, requester: string) =>
    request<{ success: boolean; member?: ProjectMember; error?: string }>(
      `/api/projects/${projectId}/members/role`,
      {
        method: 'POST',
        body: JSON.stringify({ username, project_role: projectRole, requester }),
      },
    ),

  transferProjectOwnership: (projectId: string, newOwner: string, requester: string) =>
    request<{ success: boolean; new_owner?: ProjectMember; error?: string }>(
      `/api/projects/${projectId}/members/transfer`,
      {
        method: 'POST',
        body: JSON.stringify({ new_owner: newOwner, requester }),
      },
    ),

  getMetaList: () =>
    request<{ count: number; metas: MetaInfo[] }>('/api/meta'),

  analyzeMeta: (filePath: string) =>
    request<{ meta_path: string; meta: MetaInfo | null }>('/api/meta/analyze', {
      method: 'POST',
      body: JSON.stringify({ file_path: filePath }),
    }),

  batchAnalyzeMeta: (directory?: string) =>
    request<{ count: number; files: string[] }>('/api/meta/batch-analyze', {
      method: 'POST',
      body: JSON.stringify({ directory: directory ?? '' }),
    }),

  indexMetas: () =>
    request<{ indexed: number; message: string }>('/api/meta/index', {
      method: 'POST',
    }),

  getMetaCoverage: () =>
    request<MetaCoverage>('/api/meta/coverage'),

  getMetaDepGraph: () =>
    request<DepGraph>('/api/meta/dependency-graph'),

  updateMeta: (filePath: string, updates: Partial<Omit<MetaInfo, 'file_path' | 'created_at' | 'author'>>) =>
    request<{ success: boolean; meta?: MetaInfo; error?: string }>('/api/meta/update', {
      method: 'PUT',
      body: JSON.stringify({ file_path: filePath, ...updates }),
    }),

  deleteMeta: (filePath: string) =>
    request<{ success: boolean }>('/api/meta/delete', {
      method: 'DELETE',
      body: JSON.stringify({ file_path: filePath }),
    }),

  runIntegrationTest: (files: string[]) =>
    request<{
      gate_number: number;
      gate_name: string;
      status: string;
      message: string;
      details: string[];
    }>('/api/integration-test', {
      method: 'POST',
      body: JSON.stringify({ files }),
    }),
};
