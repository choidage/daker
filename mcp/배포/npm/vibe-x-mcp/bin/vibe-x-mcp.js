#!/usr/bin/env node
/**
 * VIBE-X MCP Server — npm wrapper.
 *
 * Spawns the bundled Python MCP server.
 * Requires Python >= 3.10 installed on the system.
 *
 * Usage:
 *   npx vibe-x-mcp --project-root /path/to/project
 */

const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

const PYTHON_DIR = path.join(__dirname, "..", "python");
const ENTRY_POINT = path.join(PYTHON_DIR, "__main__.py");

function findPython() {
  const candidates = process.platform === "win32"
    ? ["python", "python3", "py"]
    : ["python3", "python"];

  for (const cmd of candidates) {
    try {
      const result = require("child_process").execSync(
        `${cmd} --version 2>&1`,
        { encoding: "utf-8", timeout: 5000 }
      );
      if (result.includes("Python 3.")) {
        return cmd;
      }
    } catch {}
  }
  return null;
}

function checkDependencies(python) {
  try {
    require("child_process").execSync(
      `${python} -c "import mcp; import chromadb"`,
      { encoding: "utf-8", timeout: 10000, stdio: "ignore" }
    );
    return true;
  } catch {
    return false;
  }
}

function installDependencies(python) {
  const reqPath = path.join(PYTHON_DIR, "requirements.txt");
  if (!fs.existsSync(reqPath)) {
    console.error("[vibe-x-mcp] requirements.txt not found.");
    process.exit(1);
  }

  console.error("[vibe-x-mcp] Installing Python dependencies...");
  try {
    require("child_process").execSync(
      `${python} -m pip install -r "${reqPath}" --quiet`,
      { encoding: "utf-8", stdio: "inherit", timeout: 300000 }
    );
  } catch (e) {
    console.error("[vibe-x-mcp] Failed to install dependencies:", e.message);
    process.exit(1);
  }
}

function main() {
  const python = findPython();
  if (!python) {
    console.error("[vibe-x-mcp] Python 3.10+ is required but not found.");
    console.error("Install Python from https://www.python.org/downloads/");
    process.exit(1);
  }

  if (!checkDependencies(python)) {
    installDependencies(python);
  }

  const args = [ENTRY_POINT, ...process.argv.slice(2)];

  const child = spawn(python, args, {
    stdio: "inherit",
    env: {
      ...process.env,
      PYTHONIOENCODING: "utf-8",
      VIBE_X_NO_WRAP_STDOUT: "1",
      PYTHONPATH: PYTHON_DIR,
    },
  });

  child.on("error", (err) => {
    console.error("[vibe-x-mcp] Failed to start:", err.message);
    process.exit(1);
  });

  child.on("exit", (code) => {
    process.exit(code || 0);
  });
}

main();
