"""codememory diff — track what changed between reindex runs.

Uses ``summary_hash`` from index.json to detect content changes.
Supports snapshot rotation and semantic time references.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import re
import shutil

_MAX_SNAPSHOTS = 10


def _load_index_data(root: Path) -> dict:
    idx_path = root / '.codememory' / 'index.json'
    if not idx_path.is_file():
        return {}
    with open(idx_path, encoding='utf-8') as f:
        data = json.load(f)
    return data.get('memories', {})


def _snapshot_dir(root: Path) -> Path:
    d = root / '.codememory' / 'snapshots'
    d.mkdir(parents=True, exist_ok=True)
    return d


def _list_snapshots(root: Path) -> list[Path]:
    """Return snapshots sorted oldest-first."""
    sd = _snapshot_dir(root)
    return sorted(sd.glob('index_*.json'))


def _parse_since(since: str) -> datetime | None:
    """Parse a semantic time reference like '2 days ago' or '1 hour ago'."""
    m = re.match(r'(\d+)\s+(minute|hour|day|week)s?\s+ago', since.strip())
    if not m:
        return None
    n = int(m.group(1))
    unit = m.group(2)
    delta = {
        'minute': timedelta(minutes=n),
        'hour': timedelta(hours=n),
        'day': timedelta(days=n),
        'week': timedelta(weeks=n),
    }[unit]
    return datetime.now(timezone.utc) - delta


def _find_snapshot(root: Path, since: str | None) -> Path | None:
    """Find the snapshot to compare against.

    If *since* is a file path, use that file.
    If *since* is a semantic time reference, find the closest snapshot before that time.
    If *since* is None, use the latest snapshot.
    """
    snapshots = _list_snapshots(root)

    if since is None:
        return snapshots[-1] if snapshots else None

    since_path = Path(since)
    if since_path.is_file():
        return since_path

    since_dt = _parse_since(since)
    if since_dt is not None and snapshots:
        # Find the snapshot closest to (but before) the target time
        best: Path | None = None
        for sp in snapshots:
            # Parse timestamp from filename: index_YYYYMMDD_HHMMSS.json
            try:
                ts = sp.stem.replace('index_', '')
                dt = datetime.strptime(ts, '%Y%m%d_%H%M%S').replace(tzinfo=timezone.utc)
                if dt <= since_dt:
                    best = sp
            except ValueError:
                pass
        return best

    return None


def _save_snapshot(root: Path) -> Path:
    """Save current index as a timestamped snapshot. Rotates old ones."""
    src = root / '.codememory' / 'index.json'
    if not src.is_file():
        raise FileNotFoundError(f"No index found at {src}. Run 'codememory reindex' first.")

    ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    dst = _snapshot_dir(root) / f'index_{ts}.json'
    shutil.copy2(src, dst)

    # Rotate: keep only the most recent N snapshots
    all_snaps = sorted(_snapshot_dir(root).glob('index_*.json'))
    for old in all_snaps[:-_MAX_SNAPSHOTS]:
        old.unlink()

    return dst


def _short_diff(old_val: str, new_val: str, max_len: int = 80) -> str:
    """Produce a one-line summary of a change."""
    if old_val == new_val:
        return '(no change)'
    if not old_val:
        return f'(added) {new_val[:max_len]}'
    if not new_val:
        return f'(removed) {old_val[:max_len]}'
    # Show first differing portion
    for i, (a, b) in enumerate(zip(old_val, new_val)):
        if a != b:
            ctx = old_val[max(0, i - 10):i + 30]
            return f'"{ctx[:max_len]}..." → "...{new_val[max(0, i - 10):i + 30]}..."'
    # Length difference only
    return f'({len(old_val)}→{len(new_val)} chars)'


def diff(root: Path, since: str | None = None) -> str:
    """Compare current index against a previous snapshot.

    Returns a formatted report of changes.
    """
    current = _load_index_data(root)
    previous_path = _find_snapshot(root, since)

    if previous_path is None or not previous_path.is_file():
        # No previous snapshot — save one and report baseline
        snap_path = _save_snapshot(root)
        all_snaps = _list_snapshots(root)
        return (
            f"No previous snapshot found. Saved current index as baseline.\n"
            f"Snapshot: {snap_path}\n"
            f"Tracked snapshots: {len(all_snaps)} (max {_MAX_SNAPSHOTS})\n"
            f"Run 'codememory diff' again after next reindex to see changes."
        )

    with open(previous_path, encoding='utf-8') as f:
        previous = json.load(f).get('memories', {})

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
            cur_summary = cur.get('summary', '')
            prev_summary = prev.get('summary', '')
            detail = _short_diff(prev_summary, cur_summary)
            changed.append(f'{mid} — {detail}')
        cur_lc = cur.get('lifecycle', 'permanent')
        prev_lc = prev.get('lifecycle', 'permanent')
        if cur_lc != prev_lc:
            lifecycle_changes.append(f'{mid}: {prev_lc} → {cur_lc}')
        cur_cs = cur.get('cache_stable', False)
        prev_cs = prev.get('cache_stable', False)
        if cur_cs and not prev_cs:
            changed.append(f'{mid} [auto cache_stable]')

    lines: list[str] = []
    lines.append(f"# codememory diff — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"Baseline: {previous_path.name}")

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

    # Save new snapshot
    snap_path = _save_snapshot(root)
    all_snaps = _list_snapshots(root)
    lines.append(f'\nSnapshot saved: {snap_path.name} ({len(all_snaps)}/{_MAX_SNAPSHOTS} tracked)')

    return '\n'.join(lines)
