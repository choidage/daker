import * as vscode from 'vscode';
import { vibexApi } from './apiClient';
import { SidebarProvider } from './sidebarProvider';
import { GateDiagnostics } from './gateDiagnostics';

const PACTD_TEMPLATE = `## PACT-D Prompt Template

**P (Purpose):** [이 코드가 해결하는 문제]

**A (Architecture):** [기존 패턴 / ADR 참조]

**C (Constraints):** [코딩 규칙, 성능 요구사항]

**T (Test):** [테스트 전략 및 검증 방법]

**D (Dependency):** [관련 모듈, 팀원 작업 영역]
`;

let diagnostics: GateDiagnostics;

export function activate(context: vscode.ExtensionContext): void {
  diagnostics = new GateDiagnostics();

  const sidebarProvider = new SidebarProvider(context.extensionUri);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider('vibex.sidebarView', sidebarProvider),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('vibex.gateCheck', () => runGateCheck()),
    vscode.commands.registerCommand('vibex.pipeline', () => runPipeline()),
    vscode.commands.registerCommand('vibex.ragSearch', () => showRagSearch()),
    vscode.commands.registerCommand('vibex.declareZone', () => declareWorkZone()),
    vscode.commands.registerCommand('vibex.insertPactd', () => insertPactd()),
    vscode.commands.registerCommand('vibex.openDashboard', () => openDashboard()),
  );

  context.subscriptions.push(diagnostics);

  vscode.window.showInformationMessage('VIBE-X activated');
}

export function deactivate(): void {
  diagnostics?.dispose();
}

async function runGateCheck(): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage('VIBE-X: No active file');
    return;
  }

  const filePath = editor.document.uri.fsPath;

  await vscode.window.withProgress(
    { location: vscode.ProgressLocation.Notification, title: 'VIBE-X: Running Gate Check...' },
    async () => {
      try {
        const result = await vibexApi.gateCheck(filePath);
        diagnostics.updateFromPipeline(editor.document.uri, result.gates);
        showGateResultMessage(result);
      } catch (err) {
        vscode.window.showErrorMessage(`VIBE-X Gate Check failed: ${err}`);
      }
    },
  );
}

async function runPipeline(): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage('VIBE-X: No active file');
    return;
  }

  const filePath = editor.document.uri.fsPath;

  await vscode.window.withProgress(
    { location: vscode.ProgressLocation.Notification, title: 'VIBE-X: Running 6-Gate Pipeline...' },
    async () => {
      try {
        const result = await vibexApi.pipeline(filePath);
        diagnostics.updateFromPipeline(editor.document.uri, result.gates);
        showGateResultMessage(result);
      } catch (err) {
        vscode.window.showErrorMessage(`VIBE-X Pipeline failed: ${err}`);
      }
    },
  );
}

function showGateResultMessage(result: { overall_status: string; gates: Array<{ gate: number; name: string; status: string }> }): void {
  const passed = result.gates.filter((g) => g.status === 'passed').length;
  const total = result.gates.length;
  const icon = result.overall_status === 'passed' ? '✓' : result.overall_status === 'warning' ? '⚠' : '✗';

  const summary = result.gates
    .map((g) => `G${g.gate}:${g.status === 'passed' ? '✓' : g.status === 'warning' ? '⚠' : '✗'}`)
    .join(' ');

  if (result.overall_status === 'passed') {
    vscode.window.showInformationMessage(`${icon} VIBE-X: ${passed}/${total} gates passed — ${summary}`);
  } else if (result.overall_status === 'warning') {
    vscode.window.showWarningMessage(`${icon} VIBE-X: ${passed}/${total} passed — ${summary}`);
  } else {
    vscode.window.showErrorMessage(`${icon} VIBE-X: ${passed}/${total} passed — ${summary}`);
  }
}

async function showRagSearch(): Promise<void> {
  const query = await vscode.window.showInputBox({
    prompt: 'VIBE-X RAG Search — 자연어로 코드 검색',
    placeHolder: '예: 인증 처리 함수, Gate 검증 로직',
  });
  if (!query) { return; }

  await vscode.window.withProgress(
    { location: vscode.ProgressLocation.Notification, title: 'VIBE-X: Searching...' },
    async () => {
      try {
        const data = await vibexApi.search(query);
        if (!data.results.length) {
          vscode.window.showInformationMessage('VIBE-X: No results found');
          return;
        }

        const items = data.results.map((r) => ({
          label: `$(file-code) ${r.file_path.split(/[/\\]/).pop()}`,
          description: `${r.start_line}-${r.end_line} | ${(r.relevance_score * 100).toFixed(0)}%`,
          detail: r.content.slice(0, 120).replace(/\n/g, ' '),
          result: r,
        }));

        const picked = await vscode.window.showQuickPick(items, {
          placeHolder: `${data.results.length} results for "${query}"`,
          matchOnDescription: true,
          matchOnDetail: true,
        });

        if (picked) {
          const doc = await vscode.workspace.openTextDocument(picked.result.file_path);
          const editor = await vscode.window.showTextDocument(doc);
          const pos = new vscode.Position(Math.max(0, picked.result.start_line - 1), 0);
          editor.revealRange(new vscode.Range(pos, pos), vscode.TextEditorRevealType.InCenter);
          editor.selection = new vscode.Selection(pos, pos);
        }
      } catch (err) {
        vscode.window.showErrorMessage(`VIBE-X Search failed: ${err}`);
      }
    },
  );
}

async function declareWorkZone(): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  const currentFile = editor?.document.uri.fsPath || '';

  const filesInput = await vscode.window.showInputBox({
    prompt: 'Work Zone 파일 목록 (쉼표 구분)',
    value: currentFile,
    placeHolder: 'file1.py, file2.py',
  });
  if (!filesInput) { return; }

  const desc = await vscode.window.showInputBox({
    prompt: '작업 설명 (선택)',
    placeHolder: 'Gate 검증 로직 리팩토링',
  }) || '';

  try {
    const files = filesInput.split(',').map((f) => f.trim()).filter(Boolean);
    const res = await vibexApi.declareZone(files, desc);

    if (res.conflicts?.length) {
      vscode.window.showWarningMessage(
        `VIBE-X: Work Zone declared with conflicts!\n${res.conflicts.join('\n')}`,
      );
    } else {
      vscode.window.showInformationMessage('VIBE-X: Work Zone declared successfully');
    }
  } catch (err) {
    vscode.window.showErrorMessage(`VIBE-X: ${err}`);
  }
}

function insertPactd(): void {
  const editor = vscode.window.activeTextEditor;
  if (!editor) { return; }

  editor.edit((editBuilder) => {
    editBuilder.insert(editor.selection.active, PACTD_TEMPLATE);
  });
}

function openDashboard(): void {
  const url = vscode.workspace.getConfiguration('vibex').get<string>('apiUrl') || 'http://127.0.0.1:8000';
  vscode.env.openExternal(vscode.Uri.parse(url));
}
