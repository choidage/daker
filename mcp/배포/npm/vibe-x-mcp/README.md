# vibe-x-mcp

VIBE-X AI Code Quality & Team Collaboration MCP Server for Cursor / Claude.

## Requirements

- **Node.js** >= 18
- **Python** >= 3.10

## Quick Start

```bash
npx vibe-x-mcp --project-root /path/to/your/project
```

## Cursor IDE Setup

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "vibe-x": {
      "command": "npx",
      "args": ["-y", "vibe-x-mcp", "--project-root", "/path/to/your/project"]
    }
  }
}
```

## 21 MCP Tools

| Category | Tools |
|----------|-------|
| Quality | `gate_check`, `pipeline`, `security_review`, `architecture_check` |
| RAG | `code_search`, `index_codebase` |
| Collab | `work_zone`, `extract_decisions` |
| Meta | `meta_analyze`, `meta_batch`, `meta_coverage`, `meta_dependency_graph` |
| Analysis | `feedback_analysis`, `integration_test` |
| E2E | `e2e_verify_url`, `e2e_verify_selector` |
| Ops | `project_status`, `onboarding_qa`, `get_alerts`, `acknowledge_alerts`, `health_breakdown` |

## Features

- **6-Gate Pipeline**: Syntax, Rules, Integration, Security, Architecture, Collision
- **RAG Code Search**: Semantic search over your codebase via ChromaDB
- **Hidden Intent (.meta.json)**: Auto-extract code intent with AST analysis
- **E2E Verification**: URL accessibility check, Playwright-based selector verification
- **Team Collaboration**: Work Zone conflict prevention, Decision Extractor
- **Alert & Feedback**: Failure pattern analysis, threshold-based alerts

## License

MIT
