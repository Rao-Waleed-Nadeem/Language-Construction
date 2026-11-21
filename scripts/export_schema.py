"""Export OpenAPI schema and generate TypeScript client types.

Generates:
- openapi.json (root and backend/)
- frontend/src/api/schema.d.ts
"""

import json
from pathlib import Path
import subprocess
import sys

# Ensure backend is on sys.path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
sys.path.insert(0, str(backend_dir))

from api.main import app  # noqa: E402


def export_schemas() -> None:
    schema = app.openapi()
    schema_json = json.dumps(schema, indent=2)

    # 1. Write openapi.json
    root_openapi = root_dir / "openapi.json"
    backend_openapi = backend_dir / "openapi.json"
    root_openapi.write_text(schema_json + "\n", encoding="utf-8")
    backend_openapi.write_text(schema_json + "\n", encoding="utf-8")
    print(f"Exported OpenAPI schema to {root_openapi} and {backend_openapi}")

    # 2. Generate frontend/src/api/schema.d.ts
    frontend_api_dir = root_dir / "frontend" / "src" / "api"
    frontend_api_dir.mkdir(parents=True, exist_ok=True)
    ts_schema_path = frontend_api_dir / "schema.d.ts"

    # Use openapi-typescript via npx
    cmd = [
        "npx",
        "--yes",
        "openapi-typescript",
        str(root_openapi),
        "-o",
        str(ts_schema_path),
    ]
    print(f"Running: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=root_dir / "frontend", capture_output=True, text=True, shell=True, check=False)
    if res.returncode == 0:
        print(f"Generated TypeScript schema: {ts_schema_path}")
    else:
        print(f"openapi-typescript failed: {res.stderr}", file=sys.stderr)
        sys.exit(res.returncode)


if __name__ == "__main__":
    export_schemas()
