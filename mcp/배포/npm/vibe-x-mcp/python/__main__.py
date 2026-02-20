"""VIBE-X MCP Server entry point.

Usage:
    vibe-x-mcp --project-root /path/to/project
    python -m vibe_x_mcp --project-root .
"""

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="VIBE-X MCP Server")
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root directory (default: current directory)",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="MCP transport mode (default: stdio)",
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    if not project_root.exists():
        print(f"Error: Project root not found: {project_root}", file=sys.stderr)
        sys.exit(1)

    pkg_dir = Path(__file__).parent
    sys.path.insert(0, str(pkg_dir))

    import os
    os.environ["VIBE_X_NO_WRAP_STDOUT"] = "1"
    os.environ["VIBE_X_PROJECT_ROOT"] = str(project_root)

    from vibe_x_mcp.server import create_server

    mcp_server = create_server(project_root)
    mcp_server.run(transport=args.transport)


if __name__ == "__main__":
    main()
