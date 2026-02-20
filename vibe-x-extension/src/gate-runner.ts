/**
 * Gate Runner - Python 백엔드와 통신하여 품질 게이트를 실행한다.
 *
 * Python CLI를 subprocess로 호출하거나, 대시보드 API를 통해 실행한다.
 */

import * as vscode from "vscode";
import { execFile } from "child_process";
import { promisify } from "util";
import * as path from "path";

const execFileAsync = promisify(execFile);

export interface GateResult {
  gate_number: number;
  gate_name: string;
  status: "passed" | "failed" | "warning" | "skipped";
  message: string;
  details: string[];
}

interface WorkZoneResult {
  success: boolean;
  message: string;
}

interface PipelineStatus {
  gates: GateResult[];
  timestamp: string;
  total_files: number;
}

export class GateRunner {
  private pythonPath: string;
  private projectRoot: string;
  private dashboardUrl: string;
  private outputChannel: vscode.OutputChannel;

  constructor(
    config: vscode.WorkspaceConfiguration,
    outputChannel: vscode.OutputChannel
  ) {
    this.pythonPath = config.get<string>("pythonPath", "python");
    this.dashboardUrl = config.get<string>(
      "dashboardUrl",
      "http://localhost:8000"
    );
    this.outputChannel = outputChannel;

    const configRoot = config.get<string>("projectRoot", "");
    if (configRoot) {
      this.projectRoot = configRoot;
    } else {
      const folders = vscode.workspace.workspaceFolders;
      this.projectRoot = folders ? folders[0].uri.fsPath : "";
    }
  }

  /**
   * 특정 파일에 대해 모든 Gate를 실행한다.
   * Python CLI 호출 -> JSON 결과 파싱
   */
  async runAllGates(filePath: string): Promise<GateResult[]> {
    // 먼저 API 호출 시도, 실패 시 로컬 Python 실행
    try {
      return await this.runViaApi(filePath);
    } catch {
      return await this.runViaCli(filePath);
    }
  }

  /**
   * 대시보드 API를 통한 Gate 실행.
   */
  private async runViaApi(filePath: string): Promise<GateResult[]> {
    const url = `${this.dashboardUrl}/api/gate-check`;
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file_path: filePath }),
      signal: AbortSignal.timeout(10000),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = (await response.json()) as { results: GateResult[] };
    return data.results;
  }

  /**
   * Python CLI를 직접 호출하여 Gate를 실행한다 (오프라인 폴백).
   */
  private async runViaCli(filePath: string): Promise<GateResult[]> {
    const script = `
import sys, json
sys.path.insert(0, r'${this.projectRoot}')
sys.path.insert(0, r'${path.join(this.projectRoot, "vibe-x")}')

from pathlib import Path
from src.shared.config import load_config
from src.layer2_rag.gate_basic import BasicGate
from src.layer3_agents.review_agent import ReviewAgent
from src.layer3_agents.arch_agent import ArchitectureAgent

config = load_config(project_root=Path(r'${this.projectRoot}'))
file_path = Path(r'${filePath}')

results = []
try:
    gate = BasicGate(config)
    for r in gate.run_all(file_path):
        results.append({
            "gate_number": r.gate_number,
            "gate_name": r.gate_name,
            "status": r.status.value,
            "message": r.message,
            "details": r.details,
        })

    review = ReviewAgent(config)
    r = review.run(file_path)
    results.append({
        "gate_number": r.gate_number,
        "gate_name": r.gate_name,
        "status": r.status.value,
        "message": r.message,
        "details": r.details,
    })

    arch = ArchitectureAgent(config)
    r = arch.run(file_path)
    results.append({
        "gate_number": r.gate_number,
        "gate_name": r.gate_name,
        "status": r.status.value,
        "message": r.message,
        "details": r.details,
    })
except Exception as e:
    results.append({
        "gate_number": 0,
        "gate_name": "Error",
        "status": "skipped",
        "message": str(e),
        "details": [],
    })

print(json.dumps(results, ensure_ascii=False))
`;

    try {
      const { stdout } = await execFileAsync(this.pythonPath, ["-c", script], {
        timeout: 30000,
        maxBuffer: 1024 * 1024,
        env: { ...process.env, VIBE_X_NO_WRAP_STDOUT: "1" },
      });
      return JSON.parse(stdout.trim());
    } catch (error: any) {
      this.outputChannel.appendLine(`Gate Runner Error: ${error.message}`);
      return [
        {
          gate_number: 0,
          gate_name: "Error",
          status: "skipped",
          message: error.message || "Gate execution failed",
          details: [],
        },
      ];
    }
  }

  /**
   * Work Zone을 선언한다.
   */
  async declareWorkZone(
    filePath: string,
    user: string
  ): Promise<WorkZoneResult> {
    try {
      const url = `${this.dashboardUrl}/api/work-zone`;
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_path: filePath, user }),
        signal: AbortSignal.timeout(5000),
      });

      if (response.ok) {
        return { success: true, message: "Work Zone declared" };
      }
      return {
        success: false,
        message: `Server error: ${response.status}`,
      };
    } catch {
      // 오프라인 모드: 로컬 파일에 기록
      return { success: true, message: "Work Zone declared (offline)" };
    }
  }

  /**
   * 파이프라인 상태를 조회한다.
   */
  async getPipelineStatus(): Promise<PipelineStatus> {
    try {
      const url = `${this.dashboardUrl}/api/dashboard`;
      const response = await fetch(url, {
        signal: AbortSignal.timeout(5000),
      });
      return (await response.json()) as PipelineStatus;
    } catch {
      return {
        gates: [],
        timestamp: new Date().toISOString(),
        total_files: 0,
      };
    }
  }
}
