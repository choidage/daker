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
exports.GateDiagnostics = void 0;
const vscode = __importStar(require("vscode"));
const LINE_PATTERN = /L(\d+):/;
class GateDiagnostics {
    constructor() {
        this.collection = vscode.languages.createDiagnosticCollection('vibex');
    }
    updateFromPipeline(uri, gates) {
        const diags = [];
        for (const gate of gates) {
            if (gate.status === 'passed') {
                continue;
            }
            for (const detail of gate.details) {
                const lineMatch = LINE_PATTERN.exec(detail);
                const line = lineMatch ? parseInt(lineMatch[1], 10) - 1 : 0;
                const range = new vscode.Range(line, 0, line, 200);
                const severity = gate.status === 'failed'
                    ? vscode.DiagnosticSeverity.Error
                    : vscode.DiagnosticSeverity.Warning;
                const diag = new vscode.Diagnostic(range, `[VIBE-X G${gate.gate}] ${detail}`, severity);
                diag.source = `VIBE-X Gate ${gate.gate}: ${gate.name}`;
                diags.push(diag);
            }
            if (gate.details.length === 0 && gate.status !== 'passed') {
                const range = new vscode.Range(0, 0, 0, 0);
                const severity = gate.status === 'failed'
                    ? vscode.DiagnosticSeverity.Error
                    : vscode.DiagnosticSeverity.Warning;
                const diag = new vscode.Diagnostic(range, `[VIBE-X G${gate.gate}] ${gate.message}`, severity);
                diag.source = `VIBE-X Gate ${gate.gate}: ${gate.name}`;
                diags.push(diag);
            }
        }
        this.collection.set(uri, diags);
    }
    clear(uri) {
        if (uri) {
            this.collection.delete(uri);
        }
        else {
            this.collection.clear();
        }
    }
    dispose() {
        this.collection.dispose();
    }
}
exports.GateDiagnostics = GateDiagnostics;
//# sourceMappingURL=gateDiagnostics.js.map