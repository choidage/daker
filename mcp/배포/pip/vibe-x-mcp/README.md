# vibe-x-mcp

VIBE-X AI Code Quality & Team Collaboration MCP Server for Cursor / Claude.

## Features

- **6-Gate Pipeline**: Syntax, Rules, Integration, Security, Architecture, Collision
- **RAG Code Search**: Semantic search over your codebase via ChromaDB
- **Hidden Intent (.meta.json)**: Auto-extract code intent with AST analysis
- **Team Collaboration**: Work Zone conflict prevention, Decision Extractor
- **Alert & Feedback**: Failure pattern analysis, threshold-based alerts
- **Onboarding Q&A**: RAG-based project Q&A for new team members

## 19 MCP Tools

| Category | Tools |
|----------|-------|
| Quality | `gate_check`, `pipeline`, `security_review`, `architecture_check` |
| RAG | `code_search`, `index_codebase` |
| Collab | `work_zone`, `extract_decisions` |
| Meta | `meta_analyze`, `meta_batch`, `meta_coverage`, `meta_dependency_graph` |
| Analysis | `feedback_analysis`, `integration_test` |
| Ops | `project_status`, `onboarding_qa`, `get_alerts`, `acknowledge_alerts`, `health_breakdown` |

## Install

```bash
pip install vibe-x-mcp
```

## Usage

### Cursor IDE

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "vibe-x": {
      "command": "vibe-x-mcp",
      "args": ["--project-root", "/path/to/your/project"],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

### CLI

```bash
vibe-x-mcp --project-root /path/to/your/project
vibe-x-mcp --project-root . --transport sse
```

### uvx (no install)

```bash
uvx vibe-x-mcp --project-root /path/to/your/project
```

## Requirements

- Python >= 3.10
- Project with source code to analyze

## License

MIT
