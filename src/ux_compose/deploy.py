"""uxcompose deploy — generate deploy configs for product ASGI apps.

Does not upload secrets/cloud. Prepares Dockerfile / fly / render / railway / vps.
Default ASGI entry: ``app:asgi`` (uxcompose create-app composition root).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Optional

Provider = Literal["docker", "fly", "render", "railway", "vps", "checklist"]


@dataclass
class DeployResult:
    root: Path
    provider: str
    files_written: list[str] = field(default_factory=list)
    instructions: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": str(self.root),
            "provider": self.provider,
            "files_written": self.files_written,
            "instructions": self.instructions,
            "notes": self.notes,
        }


def _find_app_root(start: Optional[Path] = None) -> Path:
    cur = (start or Path.cwd()).resolve()
    for p in [cur, *cur.parents]:
        if (p / "app.py").is_file():
            return p
        if p == p.parent:
            break
    raise FileNotFoundError(
        "no product app found (expected app.py from uxcompose create-app)."
    )


def _write(path: Path, content: str, *, force: bool) -> bool:
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8")
    return True


_DOCKERFILE = """\
# ux-compose product ASGI image
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PORT=8080

COPY requirements.txt .
RUN pip install --no-cache-dir -U pip \\
    && pip install --no-cache-dir -r requirements.txt \\
    && pip install --no-cache-dir "uvicorn[standard]" fastapi ux-compose ux-dom ux-behavior

COPY . .

# CSS: run `uxcompose build` before `docker build` so output.css is in COPY.
# Or compile in the image (uncomment):
# RUN pip install --no-cache-dir pytailwindcss \\
#  && uxcompose build --skip-import

EXPOSE 8080
CMD ["sh", "-c", "uvicorn app:asgi --host 0.0.0.0 --port ${PORT:-8080}"]
"""

_DOCKERIGNORE = """\
.venv
__pycache__
*.pyc
.git
.env
.pytest_cache
*.egg-info
"""

_FLY = """\
app = "{app_name}"
primary_region = "iad"

[build]

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = "stop"
  auto_start_machines = true
  min_machines_running = 0

[[vm]]
  memory = "512mb"
  cpu_kind = "shared"
  cpus = 1
"""

_RENDER = """\
services:
  - type: web
    name: {app_name}
    runtime: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app:asgi --host 0.0.0.0 --port $PORT
    envVars:
      - key: DEBUG
        value: "false"
"""

_RAILWAY = """\
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": { "builder": "NIXPACKS" },
  "deploy": {
    "startCommand": "uvicorn app:asgi --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE"
  }
}
"""

_SYSTEMD = """\
[Unit]
Description=ux-compose {app_name}
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/{app_name}
Environment=PORT=8080
ExecStart=/var/www/{app_name}/.venv/bin/uvicorn app:asgi --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
"""


def prepare_deploy(
    provider: Provider = "docker",
    *,
    cwd: Optional[Path] = None,
    force: bool = False,
    app_name: Optional[str] = None,
) -> DeployResult:
    root = _find_app_root(cwd)
    name = app_name or root.name.replace("_", "-").lower()
    result = DeployResult(root=root, provider=provider)

    result.notes.append("uxcompose deploy prepares config only — does not upload.")
    result.notes.append("ASGI entry: uvicorn app:asgi --host 0.0.0.0 --port $PORT")
    result.notes.append("Compile CSS first: uxcompose build  (output.css on disk before the image).")

    if provider == "checklist":
        result.instructions = [
            "1. uxcompose build",
            "2. uxcompose doctor .",
            "3. Set secrets / DEBUG=false on host",
            "4. uvicorn app:asgi --host 0.0.0.0 --port 8080",
            "5. TLS reverse proxy in front",
        ]
        return result

    if provider == "docker":
        if _write(root / "Dockerfile", _DOCKERFILE, force=force):
            result.files_written.append("Dockerfile")
        if _write(root / ".dockerignore", _DOCKERIGNORE, force=force):
            result.files_written.append(".dockerignore")
        result.instructions = [
            f"docker build -t {name} .",
            f"docker run --rm -p 8080:8080 {name}",
        ]
    elif provider == "fly":
        if not (root / "Dockerfile").exists():
            _write(root / "Dockerfile", _DOCKERFILE, force=True)
            result.files_written.append("Dockerfile")
        if _write(root / "fly.toml", _FLY.format(app_name=name), force=force):
            result.files_written.append("fly.toml")
        result.instructions = ["fly auth login", f"fly apps create {name}", "fly deploy"]
    elif provider == "render":
        if _write(root / "render.yaml", _RENDER.format(app_name=name), force=force):
            result.files_written.append("render.yaml")
        result.instructions = ["Push repo → Render Blueprint with render.yaml"]
    elif provider == "railway":
        if _write(root / "railway.json", _RAILWAY, force=force):
            result.files_written.append("railway.json")
        result.instructions = ["railway login", "railway init && railway up"]
    elif provider == "vps":
        unit = f"deploy/{name}.service"
        if _write(root / unit, _SYSTEMD.format(app_name=name), force=force):
            result.files_written.append(unit)
        result.instructions = [
            f"rsync to /var/www/{name}",
            "python -m venv .venv && pip install -r requirements.txt",
            f"sudo cp {unit} /etc/systemd/system/ && systemctl enable --now {name}",
        ]
    else:
        raise ValueError(f"unknown provider {provider!r}")

    return result


def format_deploy_result(result: DeployResult) -> str:
    lines = [
        "uxcompose deploy prepare",
        f"provider: {result.provider}",
        f"root: {result.root}",
        "=" * 40,
    ]
    if result.files_written:
        lines.append("wrote:")
        for f in result.files_written:
            lines.append(f"  + {f}")
    else:
        lines.append("wrote: (no new files)")
    for n in result.notes:
        lines.append(f"  · {n}")
    lines.append("next:")
    for i in result.instructions:
        lines.append(f"  $ {i}")
    lines.append("=" * 40)
    return "\n".join(lines)
