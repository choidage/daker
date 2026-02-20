/**
 * VIBE-X VSCode/Cursor Extension
 *
 * 코드 품질 게이트, 아키텍처 검증, 보안 검사를 IDE에서 바로 실행한다.
 * 파일 저장 시 자동으로 Gate 1,2를 실행하고, 수동으로 전체 Gate를 실행할 수 있다.
 */

import * as vscode from "vscode";
import { GateRunner, GateResult } from "./gate-runner";
import { DashboardPanel } from "./dashboard-panel";
import { StatusBarManager } from "./statusbar";
import { I18n } from "./i18n";

let gateRunner: GateRunner;
let statusBar: StatusBarManager;
let diagnosticCollection: vscode.DiagnosticCollection;
let outputChannel: vscode.OutputChannel;

export function activate(context: vscode.ExtensionContext): void {
  const config = vscode.workspace.getConfiguration("vibe-x");
  const lang = config.get<string>("language", "ko");
  const i18n = new I18n(lang);

  outputChannel = vscode.window.createOutputChannel("VIBE-X");
  diagnosticCollection =
    vscode.languages.createDiagnosticCollection("vibe-x");
  gateRunner = new GateRunner(config, outputChannel);
  statusBar = new StatusBarManager();

  outputChannel.appendLine(i18n.t("activated"));

  // 1. Run Gates on Current File (Ctrl+Shift+G)
  const runGatesOnFile = vscode.commands.registerCommand(
    "vibe-x.runGatesOnFile",
    async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        vscode.window.showWarningMessage(i18n.t("no_file_open"));
        return;
      }
      await runGatesForFile(editor.document, i18n);
    }
  );

  // 2. Run All Gates (workspace-wide)
  const runGates = vscode.commands.registerCommand(
    "vibe-x.runGates",
    async () => {
      const files = await vscode.workspace.findFiles(
        "**/*.{py,ts,tsx,js,jsx}",
        "**/node_modules/**"
      );
      statusBar.showRunning(i18n.t("scanning", { count: files.length }));
      let totalIssues = 0;

      for (const file of files) {
        const doc = await vscode.workspace.openTextDocument(file);
        const results = await gateRunner.runAllGates(doc.uri.fsPath);
        const issues = applyDiagnostics(doc, results);
        totalIssues += issues;
      }

      statusBar.showResult(totalIssues);
      outputChannel.appendLine(
        i18n.t("scan_complete", {
          files: files.length,
          issues: totalIssues,
        })
      );
    }
  );

  // 3. Open Dashboard
  const openDashboard = vscode.commands.registerCommand(
    "vibe-x.openDashboard",
    () => {
      const url = config.get<string>("dashboardUrl", "http://localhost:8000");
      vscode.env.openExternal(vscode.Uri.parse(url));
    }
  );

  // 4. Declare Work Zone
  const declareWorkZone = vscode.commands.registerCommand(
    "vibe-x.declareWorkZone",
    async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        return;
      }
      const filePath = editor.document.uri.fsPath;
      const user = await vscode.window.showInputBox({
        prompt: i18n.t("enter_username"),
        placeHolder: "your-name",
      });
      if (!user) {
        return;
      }

      const result = await gateRunner.declareWorkZone(filePath, user);
      if (result.success) {
        vscode.window.showInformationMessage(
          i18n.t("zone_declared", { file: filePath, user })
        );
      } else {
        vscode.window.showWarningMessage(result.message);
      }
    }
  );

  // 5. Show Pipeline Status
  const showPipelineStatus = vscode.commands.registerCommand(
    "vibe-x.showPipelineStatus",
    async () => {
      const results = await gateRunner.getPipelineStatus();
      DashboardPanel.createOrShow(context.extensionUri, results, i18n);
    }
  );

  // Auto-run on save
  const onSave = vscode.workspace.onDidSaveTextDocument(async (doc) => {
    if (!config.get<boolean>("autoRunOnSave", true)) {
      return;
    }
    const supported = [".py", ".ts", ".tsx", ".js", ".jsx"];
    if (!supported.some((ext) => doc.fileName.endsWith(ext))) {
      return;
    }
    await runGatesForFile(doc, i18n);
  });

  context.subscriptions.push(
    runGatesOnFile,
    runGates,
    openDashboard,
    declareWorkZone,
    showPipelineStatus,
    onSave,
    diagnosticCollection,
    outputChannel
  );

  statusBar.showReady();
}

async function runGatesForFile(
  doc: vscode.TextDocument,
  i18n: I18n
): Promise<void> {
  statusBar.showRunning(i18n.t("checking_file"));
  outputChannel.appendLine(`\n--- ${doc.fileName} ---`);

  const results = await gateRunner.runAllGates(doc.uri.fsPath);
  const issueCount = applyDiagnostics(doc, results);

  for (const r of results) {
    const icon =
      r.status === "passed" ? "✅" : r.status === "failed" ? "❌" : "⚠️";
    outputChannel.appendLine(`  ${icon} Gate ${r.gate_number}: ${r.message}`);
    for (const detail of r.details) {
      outputChannel.appendLine(`     ${detail}`);
    }
  }

  statusBar.showResult(issueCount);

  if (issueCount === 0) {
    vscode.window.setStatusBarMessage(
      `$(check) VIBE-X: ${i18n.t("all_passed")}`,
      3000
    );
  }
}

function applyDiagnostics(
  doc: vscode.TextDocument,
  results: GateResult[]
): number {
  const diagnostics: vscode.Diagnostic[] = [];

  for (const result of results) {
    if (result.status === "passed") {
      continue;
    }

    for (const detail of result.details) {
      const lineMatch = detail.match(/L(\d+):/);
      const lineNum = lineMatch ? parseInt(lineMatch[1], 10) - 1 : 0;
      const line = Math.min(lineNum, doc.lineCount - 1);

      const severity =
        result.status === "failed"
          ? vscode.DiagnosticSeverity.Error
          : vscode.DiagnosticSeverity.Warning;

      const range = new vscode.Range(line, 0, line, 200);
      const diag = new vscode.Diagnostic(
        range,
        `[VIBE-X Gate ${result.gate_number}] ${detail}`,
        severity
      );
      diag.source = `vibe-x-gate${result.gate_number}`;
      diagnostics.push(diag);
    }
  }

  diagnosticCollection.set(doc.uri, diagnostics);
  return diagnostics.length;
}

export function deactivate(): void {
  diagnosticCollection?.dispose();
  outputChannel?.dispose();
}
