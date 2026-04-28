"""Global append-only log: records key events to .codememory/log.md."""

from datetime import datetime
from pathlib import Path


def append_log(root_dir: Path, action: str, detail: str) -> None:
    """Append one line to .codememory/log.md.

    Args:
        root_dir: The memory root directory.
        action: Action category (create, update, snapshot, maturity).
        detail: Human-readable detail line.
    """
    log_dir = root_dir / ".codememory"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "log.md"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"| {timestamp} | {action:12s} | {detail}\n"

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line)


def show_log(root_dir: Path, limit: int = 20) -> str:
    """Return the last N lines from .codememory/log.md.

    Args:
        root_dir: The memory root directory.
        limit: Max number of recent entries to show.

    Returns:
        Formatted log string.
    """
    log_path = root_dir / ".codememory" / "log.md"
    if not log_path.exists():
        return "(no log entries)"

    lines = log_path.read_text(encoding="utf-8").strip().split("\n")
    if not lines:
        return "(no log entries)"

    header = "| Timestamp           | Action       | Detail"
    separator = "|---------------------|--------------|--------"

    recent = lines[-limit:] if len(lines) > limit else lines
    return header + "\n" + separator + "\n" + "\n".join(recent)
