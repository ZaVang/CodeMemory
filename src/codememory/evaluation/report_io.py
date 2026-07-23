"""Safe final-write helpers for evaluation reports."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4


def preflight_output_path(output: str | Path, *, overwrite: bool) -> Path:
    """Resolve and validate an explicit output target without writing."""

    target = Path(output).expanduser().resolve()
    if not target.parent.is_dir():
        raise FileNotFoundError(
            f"Evaluation report parent directory does not exist: {target.parent}"
        )
    if target.exists():
        if target.is_dir():
            raise IsADirectoryError(f"Evaluation report output is a directory: {target}")
        if not overwrite:
            raise FileExistsError(
                f"Evaluation report already exists: {target}; use --overwrite to replace it"
            )
    return target


def write_report_atomic(target: Path, text: str, *, overwrite: bool) -> None:
    """Publish complete UTF-8 bytes atomically.

    Without overwrite, a hard-link publish preserves the no-clobber guarantee
    even if another process creates the target after preflight.
    """

    temp = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
    try:
        with temp.open("xb") as handle:
            handle.write(text.encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        if overwrite:
            os.replace(temp, target)
        else:
            os.link(temp, target)
            temp.unlink()
    finally:
        if temp.exists():
            temp.unlink()
