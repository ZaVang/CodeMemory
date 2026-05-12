"""codememory diff — track what changed between reindex runs.

Uses ``summary_hash`` from index.json to detect content changes.
Compares the current index against a previous snapshot or the last
recorded state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def _load_index_data(root: Path) -> dict:
    import json
    idx_path = root / '.codememory' / 'index.json'
    if not idx_path.is_file():
        return {}
    with open(idx_path, encoding='utf-8') as f:
        data = json.load(f)
    return data.get('memories', {})


def _load_previous_snapshot(root: Path, snapshot_file: str | None = None) -> dict:
    """Load a previous index snapshot for comparison.

    If *snapshot_file* is given, load that file. Otherwise load the
    last saved snapshot from ``.codememory/index_snapshot.json``.
    """
    import json

    if snapshot_file:
        path = Path(snapshot_file)
    else:
        path = root / '.codememory' / 'index_snapshot.json'

    if not path.is_file():
        return {}
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    return data.get('memories', {})


def _save_snapshot(root: Path) -> str:
    """Save current index as a snapshot for future diff. Returns snapshot path."""
    import json, shutil

    src = root / '.codememory' / 'index.json'
    dst = root / '.codememory' / 'index_snapshot.json'
    if src.is_file():
        shutil.copy2(src, dst)
    return str(dst)


def diff(root: Path, snapshot: str | None = None) -> str:
    """Compare current index against a previous snapshot.

    Returns a formatted report of changes.
    """
    current = _load_index_data(root)
    previous = _load_previous_snapshot(root, snapshot)

    if not previous:
        # No previous snapshot — save one and report baseline
        _save_snapshot(root)
        return (
            f"No previous snapshot found. Saved current index as baseline.\n"
            f"Snapshot: {root / '.codememory' / 'index_snapshot.json'}\n"
            f"Run 'codememory diff' again after next reindex to see changes."
        )

    changed: list[str] = []
    added: list[str] = []
    removed: list[str] = []
    lifecycle_changes: list[str] = []

    current_ids = set(current.keys())
    previous_ids = set(previous.keys())

    for mid in sorted(current_ids - previous_ids):
        added.append(mid)

    for mid in sorted(previous_ids - current_ids):
        removed.append(mid)

    for mid in sorted(current_ids & previous_ids):
        cur = current[mid]
        prev = previous[mid]
        cur_hash = cur.get('summary_hash', '')
        prev_hash = prev.get('summary_hash', '')
        if cur_hash != prev_hash:
            changed.append(mid)
        # Track lifecycle transitions
        cur_lc = cur.get('lifecycle', 'permanent')
        prev_lc = prev.get('lifecycle', 'permanent')
        if cur_lc != prev_lc:
            lifecycle_changes.append(f'{mid}: {prev_lc} → {cur_lc}')
        # Track cache_stable transitions
        cur_cs = cur.get('cache_stable', False)
        prev_cs = prev.get('cache_stable', False)
        if cur_cs and not prev_cs:
            changed.append(f'{mid} [auto cache_stable]')

    lines: list[str] = []
    lines.append(f"# codememory diff — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

    if added:
        lines.append(f'\n## Added ({len(added)})')
        for mid in added:
            lines.append(f'  + {mid}')

    if removed:
        lines.append(f'\n## Removed ({len(removed)})')
        for mid in removed:
            lines.append(f'  - {mid}')

    if changed:
        lines.append(f'\n## Changed ({len(changed)})')
        for mid in changed:
            lines.append(f'  ~ {mid}')

    if lifecycle_changes:
        lines.append(f'\n## Lifecycle Transitions ({len(lifecycle_changes)})')
        for lc in lifecycle_changes:
            lines.append(f'  ↻ {lc}')

    if not added and not removed and not changed and not lifecycle_changes:
        lines.append('\nNo changes since last snapshot.')

    # Save new snapshot after reporting
    snap_path = _save_snapshot(root)
    lines.append(f'\nSnapshot saved: {snap_path}')

    return '\n'.join(lines)
