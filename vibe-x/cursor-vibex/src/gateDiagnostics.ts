import * as vscode from 'vscode';

interface GateInfo {
  gate: number;
  name: string;
  status: string;
  message: string;
  details: string[];
}

const LINE_PATTERN = /L(\d+):/;

export class GateDiagnostics implements vscode.Disposable {
  private readonly collection: vscode.DiagnosticCollection;

  constructor() {
    this.collection = vscode.languages.createDiagnosticCollection('vibex');
  }

  updateFromPipeline(uri: vscode.Uri, gates: GateInfo[]): void {
    const diags: vscode.Diagnostic[] = [];

    for (const gate of gates) {
      if (gate.status === 'passed') { continue; }

      for (const detail of gate.details) {
        const lineMatch = LINE_PATTERN.exec(detail);
        const line = lineMatch ? parseInt(lineMatch[1], 10) - 1 : 0;
        const range = new vscode.Range(line, 0, line, 200);

        const severity =
          gate.status === 'failed'
            ? vscode.DiagnosticSeverity.Error
            : vscode.DiagnosticSeverity.Warning;

        const diag = new vscode.Diagnostic(
          range,
          `[VIBE-X G${gate.gate}] ${detail}`,
          severity,
        );
        diag.source = `VIBE-X Gate ${gate.gate}: ${gate.name}`;
        diags.push(diag);
      }

      if (gate.details.length === 0 && gate.status !== 'passed') {
        const range = new vscode.Range(0, 0, 0, 0);
        const severity =
          gate.status === 'failed'
            ? vscode.DiagnosticSeverity.Error
            : vscode.DiagnosticSeverity.Warning;
        const diag = new vscode.Diagnostic(
          range,
          `[VIBE-X G${gate.gate}] ${gate.message}`,
          severity,
        );
        diag.source = `VIBE-X Gate ${gate.gate}: ${gate.name}`;
        diags.push(diag);
      }
    }

    this.collection.set(uri, diags);
  }

  clear(uri?: vscode.Uri): void {
    if (uri) {
      this.collection.delete(uri);
    } else {
      this.collection.clear();
    }
  }

  dispose(): void {
    this.collection.dispose();
  }
}
