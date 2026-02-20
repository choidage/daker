/**
 * Status Bar Manager - 하단 상태바에 VIBE-X 상태를 표시한다.
 */

import * as vscode from "vscode";

export class StatusBarManager {
  private item: vscode.StatusBarItem;

  constructor() {
    this.item = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Left,
      100
    );
    this.item.command = "vibe-x.runGatesOnFile";
    this.item.show();
  }

  showReady(): void {
    this.item.text = "$(shield) VIBE-X";
    this.item.tooltip = "Click to run Quality Gates on current file";
    this.item.backgroundColor = undefined;
  }

  showRunning(message: string): void {
    this.item.text = `$(sync~spin) VIBE-X: ${message}`;
    this.item.tooltip = "Running quality checks...";
  }

  showResult(issueCount: number): void {
    if (issueCount === 0) {
      this.item.text = "$(check) VIBE-X: All Passed";
      this.item.backgroundColor = undefined;
    } else {
      this.item.text = `$(warning) VIBE-X: ${issueCount} issues`;
      this.item.backgroundColor = new vscode.ThemeColor(
        "statusBarItem.warningBackground"
      );
    }

    // 5초 후 기본 상태로 복원
    setTimeout(() => this.showReady(), 5000);
  }

  dispose(): void {
    this.item.dispose();
  }
}
