import * as vscode from 'vscode';

export class SidebarProvider implements vscode.WebviewViewProvider {
  private view?: vscode.WebviewView;

  constructor(private readonly extensionUri: vscode.Uri) {}

  resolveWebviewView(
    webviewView: vscode.WebviewView,
    _context: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken,
  ): void {
    this.view = webviewView;

    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this.extensionUri],
    };

    webviewView.webview.html = this.getHtml();

    webviewView.webview.onDidReceiveMessage(async (msg) => {
      switch (msg.type) {
        case 'gateCheck':
          vscode.commands.executeCommand('vibex.gateCheck');
          break;
        case 'pipeline':
          vscode.commands.executeCommand('vibex.pipeline');
          break;
        case 'ragSearch':
          vscode.commands.executeCommand('vibex.ragSearch');
          break;
        case 'declareZone':
          vscode.commands.executeCommand('vibex.declareZone');
          break;
        case 'pactd':
          vscode.commands.executeCommand('vibex.insertPactd');
          break;
        case 'openDashboard':
          vscode.commands.executeCommand('vibex.openDashboard');
          break;
        case 'refresh':
          this.refresh();
          break;
      }
    });

    this.refresh();
  }

  private async refresh(): Promise<void> {
    if (!this.view) { return; }
    try {
      const { vibexApi } = await import('./apiClient');
      const [health, alerts, zones] = await Promise.allSettled([
        vibexApi.getHealth(),
        vibexApi.getAlerts(),
        vibexApi.getWorkZones(),
      ]);

      this.view.webview.postMessage({
        type: 'state',
        health: health.status === 'fulfilled' ? health.value : null,
        alerts: alerts.status === 'fulfilled' ? alerts.value.alerts : [],
        zones: zones.status === 'fulfilled' ? zones.value.zones : [],
      });
    } catch {
      this.view.webview.postMessage({ type: 'state', health: null, alerts: [], zones: [] });
    }
  }

  private getHtml(): string {
    return `<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: var(--vscode-font-family);
    font-size: 12px;
    color: var(--vscode-foreground);
    background: var(--vscode-sideBar-background);
    padding: 12px;
  }

  .section { margin-bottom: 16px; }
  .section-title {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--vscode-descriptionForeground);
    margin-bottom: 8px;
  }

  .score-ring {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px;
    background: var(--vscode-editor-background);
    border-radius: 6px;
    margin-bottom: 8px;
  }
  .score-val {
    font-size: 28px;
    font-weight: 700;
  }
  .score-good { color: #34d399; }
  .score-warn { color: #fbbf24; }
  .score-bad { color: #f87171; }
  .score-label { font-size: 10px; color: var(--vscode-descriptionForeground); }
  .score-details { font-size: 10px; color: var(--vscode-descriptionForeground); }

  .bar-row { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
  .bar-label { width: 50px; font-size: 10px; color: var(--vscode-descriptionForeground); }
  .bar-track { flex: 1; height: 4px; background: rgba(255,255,255,0.06); border-radius: 2px; overflow: hidden; }
  .bar-fill { height: 100%; border-radius: 2px; transition: width .4s; }
  .bar-pct { width: 30px; text-align: right; font-size: 10px; }

  .btn {
    display: flex;
    align-items: center;
    gap: 6px;
    width: 100%;
    padding: 7px 10px;
    border: 1px solid var(--vscode-button-border, rgba(255,255,255,0.1));
    border-radius: 4px;
    background: var(--vscode-button-secondaryBackground, rgba(255,255,255,0.05));
    color: var(--vscode-button-secondaryForeground, var(--vscode-foreground));
    font-size: 11px;
    cursor: pointer;
    margin-bottom: 4px;
    text-align: left;
  }
  .btn:hover { background: var(--vscode-button-secondaryHoverBackground, rgba(255,255,255,0.1)); }
  .btn-primary {
    background: var(--vscode-button-background);
    color: var(--vscode-button-foreground);
    border: none;
  }
  .btn-primary:hover { background: var(--vscode-button-hoverBackground); }
  .btn-icon { font-size: 13px; width: 16px; text-align: center; }

  .alert-item {
    display: flex;
    align-items: flex-start;
    gap: 6px;
    padding: 6px 8px;
    background: var(--vscode-editor-background);
    border-radius: 4px;
    margin-bottom: 4px;
    font-size: 11px;
  }
  .alert-dot { width: 6px; height: 6px; border-radius: 50%; margin-top: 4px; flex-shrink: 0; }
  .dot-critical { background: #f87171; }
  .dot-warning { background: #fbbf24; }
  .dot-info { background: #60a5fa; }

  .zone-item {
    padding: 6px 8px;
    background: var(--vscode-editor-background);
    border-radius: 4px;
    margin-bottom: 4px;
  }
  .zone-author { font-weight: 600; font-size: 11px; }
  .zone-files { font-size: 10px; color: var(--vscode-descriptionForeground); margin-top: 2px; }

  .empty { color: var(--vscode-descriptionForeground); font-size: 11px; font-style: italic; padding: 8px 0; }

  .divider { border-top: 1px solid rgba(255,255,255,0.06); margin: 12px 0; }
</style>
</head>
<body>

<!-- Health Score -->
<div class="section">
  <div class="section-title">Project Health</div>
  <div class="score-ring">
    <div class="score-val" id="health-val">--</div>
    <div>
      <div class="score-label">Health Score</div>
      <div class="score-details" id="health-sub"></div>
    </div>
  </div>
  <div id="health-bars"></div>
</div>

<div class="divider"></div>

<!-- Actions -->
<div class="section">
  <div class="section-title">Actions</div>
  <button class="btn btn-primary" onclick="send('gateCheck')">
    <span class="btn-icon">🛡</span> Gate Check (G1-G2)
  </button>
  <button class="btn btn-primary" onclick="send('pipeline')">
    <span class="btn-icon">▶</span> Full Pipeline (G1-G6)
  </button>
  <button class="btn" onclick="send('ragSearch')">
    <span class="btn-icon">🔍</span> RAG Search
  </button>
  <button class="btn" onclick="send('declareZone')">
    <span class="btn-icon">📍</span> Declare Work Zone
  </button>
  <button class="btn" onclick="send('pactd')">
    <span class="btn-icon">📝</span> Insert PACT-D Template
  </button>
  <button class="btn" onclick="send('openDashboard')">
    <span class="btn-icon">📊</span> Open Dashboard
  </button>
</div>

<div class="divider"></div>

<!-- Alerts -->
<div class="section">
  <div class="section-title">Alerts</div>
  <div id="alerts-list"><div class="empty">No alerts</div></div>
</div>

<div class="divider"></div>

<!-- Work Zones -->
<div class="section">
  <div class="section-title">Active Work Zones</div>
  <div id="zones-list"><div class="empty">No active zones</div></div>
</div>

<script>
  const vscode = acquireVsCodeApi();
  function send(type) { vscode.postMessage({ type }); }

  window.addEventListener('message', (e) => {
    const msg = e.data;
    if (msg.type === 'state') {
      renderHealth(msg.health);
      renderAlerts(msg.alerts);
      renderZones(msg.zones);
    }
  });

  function renderHealth(h) {
    const el = document.getElementById('health-val');
    const sub = document.getElementById('health-sub');
    const bars = document.getElementById('health-bars');
    if (!h) {
      el.textContent = '--';
      el.className = 'score-val';
      sub.textContent = 'API unavailable';
      bars.innerHTML = '';
      return;
    }
    el.textContent = h.overall;
    el.className = 'score-val ' + (h.overall >= 70 ? 'score-good' : h.overall >= 40 ? 'score-warn' : 'score-bad');
    sub.textContent = 'Gate: ' + Math.round(h.gate_pass_rate) + '% | Arch: ' + Math.round(h.architecture_consistency) + '%';

    const items = [
      { label: 'Gate', value: h.gate_pass_rate, color: '#34d399' },
      { label: 'Arch', value: h.architecture_consistency, color: '#60a5fa' },
      { label: 'Quality', value: h.code_quality, color: '#a78bfa' },
    ];
    bars.innerHTML = items.map(i =>
      '<div class="bar-row"><span class="bar-label">' + i.label + '</span>' +
      '<div class="bar-track"><div class="bar-fill" style="width:' + Math.round(i.value || 0) + '%;background:' + i.color + '"></div></div>' +
      '<span class="bar-pct">' + Math.round(i.value || 0) + '%</span></div>'
    ).join('');
  }

  function renderAlerts(alerts) {
    const el = document.getElementById('alerts-list');
    if (!alerts || !alerts.length) {
      el.innerHTML = '<div class="empty">No alerts</div>';
      return;
    }
    el.innerHTML = alerts.map(a =>
      '<div class="alert-item"><div class="alert-dot dot-' + a.level + '"></div><div>' +
      '<div style="font-weight:600">' + a.title + '</div>' +
      '<div style="color:var(--vscode-descriptionForeground)">' + a.message + '</div>' +
      '</div></div>'
    ).join('');
  }

  function renderZones(zones) {
    const el = document.getElementById('zones-list');
    if (!zones || !zones.length) {
      el.innerHTML = '<div class="empty">No active zones</div>';
      return;
    }
    el.innerHTML = zones.map(z =>
      '<div class="zone-item"><div class="zone-author">' + z.author + '</div>' +
      '<div class="zone-files">' + z.files.join(', ') + '</div></div>'
    ).join('');
  }

  setInterval(() => send('refresh'), 30000);
</script>
</body>
</html>`;
  }
}
