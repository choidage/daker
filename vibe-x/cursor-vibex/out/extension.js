"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const apiClient_1 = require("./apiClient");
const sidebarProvider_1 = require("./sidebarProvider");
const gateDiagnostics_1 = require("./gateDiagnostics");
const PACTD_TEMPLATE = `## PACT-D Prompt Template

**P (Purpose):** [이 코드가 해결하는 문제]

**A (Architecture):** [기존 패턴 / ADR 참조]

**C (Constraints):** [코딩 규칙, 성능 요구사항]

**T (Test):** [테스트 전략 및 검증 방법]

**D (Dependency):** [관련 모듈, 팀원 작업 영역]
`;
let diagnostics;
function activate(context) {
    diagnostics = new gateDiagnostics_1.GateDiagnostics();
    const sidebarProvider = new sidebarProvider_1.SidebarProvider(context.extensionUri);
    context.subscriptions.push(vscode.window.registerWebviewViewProvider('vibex.sidebarView', sidebarProvider));
    context.subscriptions.push(vscode.commands.registerCommand('vibex.gateCheck', () => runGateCheck()), vscode.commands.registerCommand('vibex.pipeline', () => runPipeline()), vscode.commands.registerCommand('vibex.ragSearch', () => showRagSearch()), vscode.commands.registerCommand('vibex.declareZone', () => declareWorkZone()), vscode.commands.registerCommand('vibex.insertPactd', () => insertPactd()), vscode.commands.registerCommand('vibex.openDashboard', () => openDashboard()));
    context.subscriptions.push(diagnostics);
    vscode.window.showInformationMessage('VIBE-X activated');
}
function deactivate() {
    diagnostics?.dispose();
}
async function runGateCheck() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('VIBE-X: No active file');
        return;
    }
    const filePath = editor.document.uri.fsPath;
    await vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'VIBE-X: Running Gate Check...' }, async () => {
        try {
            const result = await apiClient_1.vibexApi.gateCheck(filePath);
            diagnostics.updateFromPipeline(editor.document.uri, result.gates);
            showGateResultMessage(result);
        }
        catch (err) {
            vscode.window.showErrorMessage(`VIBE-X Gate Check failed: ${err}`);
        }
    });
}
async function runPipeline() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('VIBE-X: No active file');
        return;
    }
    const filePath = editor.document.uri.fsPath;
    await vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'VIBE-X: Running 6-Gate Pipeline...' }, async () => {
        try {
            const result = await apiClient_1.vibexApi.pipeline(filePath);
            diagnostics.updateFromPipeline(editor.document.uri, result.gates);
            showGateResultMessage(result);
        }
        catch (err) {
            vscode.window.showErrorMessage(`VIBE-X Pipeline failed: ${err}`);
        }
    });
}
function showGateResultMessage(result) {
    const passed = result.gates.filter((g) => g.status === 'passed').length;
    const total = result.gates.length;
    const icon = result.overall_status === 'passed' ? '✓' : result.overall_status === 'warning' ? '⚠' : '✗';
    const summary = result.gates
        .map((g) => `G${g.gate}:${g.status === 'passed' ? '✓' : g.status === 'warning' ? '⚠' : '✗'}`)
        .join(' ');
    if (result.overall_status === 'passed') {
        vscode.window.showInformationMessage(`${icon} VIBE-X: ${passed}/${total} gates passed — ${summary}`);
    }
    else if (result.overall_status === 'warning') {
        vscode.window.showWarningMessage(`${icon} VIBE-X: ${passed}/${total} passed — ${summary}`);
    }
    else {
        vscode.window.showErrorMessage(`${icon} VIBE-X: ${passed}/${total} passed — ${summary}`);
    }
}
async function showRagSearch() {
    const query = await vscode.window.showInputBox({
        prompt: 'VIBE-X RAG Search — 자연어로 코드 검색',
        placeHolder: '예: 인증 처리 함수, Gate 검증 로직',
    });
    if (!query) {
        return;
    }
    await vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'VIBE-X: Searching...' }, async () => {
        try {
            const data = await apiClient_1.vibexApi.search(query);
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
        }
        catch (err) {
            vscode.window.showErrorMessage(`VIBE-X Search failed: ${err}`);
        }
    });
}
async function declareWorkZone() {
    const editor = vscode.window.activeTextEditor;
    const currentFile = editor?.document.uri.fsPath || '';
    const filesInput = await vscode.window.showInputBox({
        prompt: 'Work Zone 파일 목록 (쉼표 구분)',
        value: currentFile,
        placeHolder: 'file1.py, file2.py',
    });
    if (!filesInput) {
        return;
    }
    const desc = await vscode.window.showInputBox({
        prompt: '작업 설명 (선택)',
        placeHolder: 'Gate 검증 로직 리팩토링',
    }) || '';
    try {
        const files = filesInput.split(',').map((f) => f.trim()).filter(Boolean);
        const res = await apiClient_1.vibexApi.declareZone(files, desc);
        if (res.conflicts?.length) {
            vscode.window.showWarningMessage(`VIBE-X: Work Zone declared with conflicts!\n${res.conflicts.join('\n')}`);
        }
        else {
            vscode.window.showInformationMessage('VIBE-X: Work Zone declared successfully');
        }
    }
    catch (err) {
        vscode.window.showErrorMessage(`VIBE-X: ${err}`);
    }
}
function insertPactd() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        return;
    }
    editor.edit((editBuilder) => {
        editBuilder.insert(editor.selection.active, PACTD_TEMPLATE);
    });
}
function openDashboard() {
    const url = vscode.workspace.getConfiguration('vibex').get('apiUrl') || 'http://127.0.0.1:8000';
    vscode.env.openExternal(vscode.Uri.parse(url));
}
//# sourceMappingURL=extension.js.map