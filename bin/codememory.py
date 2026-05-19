#!/usr/bin/env python3
"""CodeMemory local launcher.

This is the only checked-in launcher under ``bin/``.

Usage:
    python bin/codememory.py <codememory-cli-args>
    python bin/codememory.py dev [--backend-port 8000] [--frontend-port 5300]

For normal installed usage, prefer the console scripts from ``pip install -e .``:
    codememory <command>
    codememory-mcp
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Ensure src/ is on the path so codememory package is importable
_root = Path(__file__).resolve().parent.parent
_script_dir = Path(__file__).resolve().parent
_src = _root / "src"
sys.path = [p for p in sys.path if Path(p or ".").resolve() != _script_dir]
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))


def _dev(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="python bin/codememory.py dev",
        description="Start the local FastAPI backend and Vite frontend.",
    )
    parser.add_argument("--backend-port", type=int, default=int(os.environ.get("BACKEND_PORT", "8000")))
    parser.add_argument("--frontend-port", type=int, default=int(os.environ.get("FRONTEND_PORT", "5300")))
    parser.add_argument("--host", default=os.environ.get("DEV_HOST", "127.0.0.1"))
    args = parser.parse_args(argv)

    frontend_dir = _root / "frontend"
    npx = shutil.which("npx.cmd" if os.name == "nt" else "npx") or shutil.which("npx")
    if npx is None:
        raise SystemExit("npx not found. Install Node.js dependencies before running dev mode.")

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{_src}{os.pathsep}{env.get('PYTHONPATH', '')}"
    env["BACKEND_PORT"] = str(args.backend_port)

    backend_cmd = [sys.executable, str(_root / "backend" / "server.py")]
    frontend_cmd = [npx, "vite", "--host", args.host, "--port", str(args.frontend_port)]

    print("===========================================")
    print("  CodeMemory — Starting Services")
    print("===========================================")
    print(f"[backend]  http://{args.host}:{args.backend_port}")
    print(f"[frontend] http://{args.host}:{args.frontend_port}")
    print(f"[docs]     http://{args.host}:{args.backend_port}/docs")
    print("Press Ctrl+C to stop all services.")
    print("===========================================")

    processes: list[subprocess.Popen] = []
    try:
        processes.append(subprocess.Popen(backend_cmd, cwd=_root, env=env))
        time.sleep(1)
        processes.append(subprocess.Popen(frontend_cmd, cwd=frontend_dir, env=env))

        while True:
            for proc in processes:
                code = proc.poll()
                if code is not None:
                    return code
            time.sleep(0.25)
    except KeyboardInterrupt:
        print("\nShutting down...")
        return 0
    finally:
        for proc in processes:
            if proc.poll() is None:
                proc.terminate()
        for proc in processes:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


def _cli(argv: list[str]) -> int | None:
    from codememory.cli import main

    sys.argv = [sys.argv[0], *argv]
    return main()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        raise SystemExit(_dev(sys.argv[2:]))
    result = _cli(sys.argv[1:])
    raise SystemExit(0 if result is None else result)
