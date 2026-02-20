/**
 * Dashboard Panel - VSCode WebView에서 파이프라인 상태를 시각적으로 표시한다.
 */

import * as vscode from "vscode";
import { I18n } from "./i18n";

export class DashboardPanel {
  public static currentPanel: DashboardPanel | undefined;
  private readonly panel: vscode.WebviewPanel;
  private disposables: vscode.Disposable[] = [];

  private constructor(
    panel: vscode.WebviewPanel,
    data: any,
    i18n: I18n
  ) {
    this.panel = panel;
    this.panel.webview.html = this.getHtmlContent(data, i18n);

    this.panel.onDidDispose(
      () => {
        DashboardPanel.currentPanel = undefined;
        this.disposables.forEach((d) => d.dispose());
      },
      null,
      this.disposables
    );
  }

  static createOrShow(
    extensionUri: vscode.Uri,
    data: any,
    i18n: I18n
  ): void {
    const column = vscode.ViewColumn.Two;

    if (DashboardPanel.currentPanel) {
      DashboardPanel.currentPanel.panel.reveal(column);
      DashboardPanel.currentPanel.panel.webview.html =
        DashboardPanel.currentPanel.getHtmlContent(data, i18n);
      return;
    }

    const panel = vscode.window.createWebviewPanel(
      "vibeXDashboard",
      "VIBE-X Pipeline Status",
      column,
      { enableScripts: true }
    );

    DashboardPanel.currentPanel = new DashboardPanel(panel, data, i18n);
  }

  private getHtmlContent(data: any, i18n: I18n): string {
    const gates = data.gates || [];
    const gateRows = gates
      .map((g: any) => {
        const icon =
          g.status === "passed"
            ? "✅"
            : g.status === "failed"
            ? "❌"
            : g.status === "warning"
            ? "⚠️"
            : "⏭️";
        const bgColor =
          g.status === "passed"
            ? "#e8f5e9"
            : g.status === "failed"
            ? "#ffebee"
            : g.status === "warning"
            ? "#fff3e0"
            : "#f5f5f5";
        return `
        <div class="gate-card" style="background:${bgColor};">
          <div class="gate-icon">${icon}</div>
          <div class="gate-info">
            <strong>Gate ${g.gate_number}: ${g.gate_name}</strong>
            <p>${g.message}</p>
            ${g.details?.length ? `<ul>${g.details.map((d: string) => `<li>${d}</li>`).join("")}</ul>` : ""}
          </div>
        </div>`;
      })
      .join("");

    return `<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>VIBE-X Pipeline</title>
  <style>
    body {
      font-family: var(--vscode-font-family, 'Segoe UI', sans-serif);
      padding: 20px;
      color: var(--vscode-foreground);
      background: var(--vscode-editor-background);
    }
    h1 { font-size: 1.4rem; margin-bottom: 20px; }
    .gate-card {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 14px 18px;
      margin-bottom: 10px;
      border-radius: 8px;
      border: 1px solid var(--vscode-panel-border, #ddd);
    }
    .gate-icon { font-size: 1.6rem; }
    .gate-info strong { font-size: 1rem; }
    .gate-info p { margin: 4px 0; font-size: 0.9rem; opacity: 0.85; }
    .gate-info ul { margin: 6px 0; padding-left: 18px; font-size: 0.85rem; }
    .gate-info li { margin: 2px 0; }
    .timestamp {
      margin-top: 20px;
      font-size: 0.8rem;
      opacity: 0.6;
      text-align: right;
    }
    .empty {
      padding: 40px;
      text-align: center;
      opacity: 0.6;
      font-size: 1.1rem;
    }
  </style>
</head>
<body>
  <h1>VIBE-X 6-Gate Pipeline Status</h1>
  ${gateRows || '<div class="empty">No gate results available. Run quality gates first.</div>'}
  <div class="timestamp">${i18n.t("last_updated")}: ${data.timestamp || new Date().toISOString()}</div>
</body>
</html>`;
  }
}
