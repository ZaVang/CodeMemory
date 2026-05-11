"""Shared command handlers — single source of truth for CLI and Sandbox tools.

Each handler takes a root directory plus keyword arguments and returns a
string result.  Error conditions raise ``codememory`` errors (the callers
decide whether to print to stderr, sys.exit, or return an error dict).
"""

from __future__ import annotations

import json
import logging
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

from .core import compute_body_hash as _cbh
from .core import compute_retrieval_probability as _retrieval_prob
from .core import get_memory_path, get_root_dir, parse_frontmatter as _pfm
from .create import create
from .import_cmd import import_text
from .index import load_index, reindex
from .log import show_log
from .orphans import find_orphans
from .resolve import resolve
from .search import search
from .snapshot import snapshot_dag
from .skeletonize.markdown import skeletonize_markdown
from .suggest_deps import suggest_deps
from .update import update
from .validate import validate

_logger = logging.getLogger("codememory")

# ── helpers ──────────────────────────────────────────────────────────────────

def _fmt_tags(entry: object) -> str:
    """Format tags, supporting both dict and MemoryEntry."""
    if isinstance(entry, dict):
        return ", ".join(entry.get("tags", []))
    return ", ".join(entry.tags)


def _resolve_import_ids(imports_dict: dict, strengths: tuple[str, ...] | None = None) -> list[str]:
    """Extract string ids from an imports block for specific import strengths."""
    if not isinstance(imports_dict, dict):
        return []
    strengths = strengths or ("required", "recommended", "related")
    result: list[str] = []
    for s in strengths:
        for ref in imports_dict.get(s, []):
            if isinstance(ref, str):
                result.append(ref)
            elif isinstance(ref, dict) and "id" in ref:
                result.append(ref["id"])
    return result


def _stale_check(root: Path, entry) -> bool:
    """Return True if the stored summary_hash does not match the actual body."""
    entry_path = getattr(entry, "path", None) or entry.get("path", "")
    file_path = root / entry_path
    if not file_path.exists():
        return False
    meta, body = _pfm(file_path)
    stored_hash = meta.get("summary_hash", "")
    if not stored_hash:
        return False
    return stored_hash != _cbh(body)


# ── command handlers ─────────────────────────────────────────────────────────

def handle_create(
    root: Path,
    memory_type: str,
    memory_id: str,
    schema: str | None = None,
    intensity: int = 5,
    tags: list[str] | None = None,
    dry_run: bool = False,
    maturity: str = "draft",
    stability: float | None = None,
) -> str:
    """Create a new memory.  Returns path string or dry-run preview."""
    file_path = create(
        root,
        memory_type,
        memory_id,
        schema=schema,
        intensity=intensity,
        tags=tags,
        dry_run=dry_run,
        maturity=maturity,
        stability=stability,
    )
    if file_path is None:
        return "dry-run: no file created"
    return str(file_path)


def handle_update(
    root: Path,
    memory_id: str,
    body: str | None = None,
    summary: str | None = None,
    change_note: str | None = None,
    status: str | None = None,
    import_required: list[str] | None = None,
    import_recommended: list[str] | None = None,
    import_related: list[str] | None = None,
) -> str:
    """Update a memory.  Returns path string."""
    file_path = update(
        root,
        memory_id,
        body=body,
        summary=summary,
        change_note=change_note,
        status=status,
        import_required=import_required,
        import_recommended=import_recommended,
        import_related=import_related,
    )
    return str(file_path)


def handle_resolve(
    root: Path,
    memory_id: str,
    depth: str = "required",
    budget: int | None = None,
    focus: str | None = None,
) -> str:
    """Resolve a memory context via DAG. Returns assembled text."""
    return resolve(root, memory_id, depth=depth, budget=budget, focus=focus)


def handle_reindex(root: Path) -> str:
    """Rebuild index from disk. reindex() prints its own status; return ''."""
    reindex(root)
    return ""


def handle_validate(root: Path) -> int:
    """Run integrity checks. Prints report, returns error count for exit code."""
    errors, _warnings = validate(root)
    return errors


def handle_search(
    root: Path,
    query: str | None = None,
    tags: list[str] | None = None,
    type_: str | None = None,
    status: str | None = None,
    maturity: str | None = None,
    semantic_type: str | None = None,
    has_imports: bool = False,
    has_schema: bool = False,
) -> str:
    """Search memories. Returns formatted result lines."""
    results = search(root, query=query, tags=tags, type_=type_, status=status,
                     maturity=maturity, semantic_type=semantic_type,
                     has_imports=has_imports, has_schema=has_schema)
    if not results:
        return "(no results)"
    lines: list[str] = []
    for r in results:
        tags_str = _fmt_tags(r)
        lines.append(
            f"{r['id']:40s}  {r['type']:9s}  "
            f"deps:{r['dependents']:3d}  [{tags_str}]"
        )
        if r.get("summary"):
            lines.append(f"    {r['summary']}")
    return "\n".join(lines)


def handle_focus(
    root: Path,
    memory_id: str,
    level: str = "full",
    content: str | None = None,
    summary_override: str | None = None,
    resolve_flag: bool = False,
) -> str:
    """Focus on a memory with adjustable resolution."""
    # --resolve: auto-resolve dependency subgraph before focusing
    if resolve_flag:
        return resolve(root, memory_id, depth="recommended")

    # In-context zoom
    if content is not None and summary_override is not None:
        if level == "summary":
            return f"# {memory_id}\n\n> {summary_override}"
        return content

    # Default: read from disk
    index = load_index(root)
    if memory_id not in index.memories:
        _logger.error("Memory '%s' not found in index. Did you reindex?", memory_id)
        sys.exit(1)
    entry = index.memories[memory_id]
    file_path = root / entry.path
    _meta, body = _pfm(file_path)

    if level == "summary":
        return f"# {memory_id}\n\n> {entry.summary}"
    return body


def handle_overview(
    root: Path,
    tags: list[str] | None = None,
    limit: int = 5,
    format_mode: str = "default",
    status: str | None = None,
    with_recall: bool = False,
) -> str:
    """Overview of top relevant memories with heat scores and stale detection."""
    results = search(root, tags=tags)

    # Filter by status: exclude archived by default
    if status and status != "all":
        results = [r for r in results if r.get("status") == status]
    elif not status or status != "all":
        results = [r for r in results if r.get("status") != "archived"]

    # Pre-compute cycle participants from required-imports DAG (R13-M2)
    index = load_index(root)
    all_graph: dict[str, list[str]] = {}
    for mid in index.memories:
        entry = index.memories[mid]
        imports_dict = entry.imports
        if isinstance(imports_dict, dict):
            all_graph[mid] = _resolve_import_ids(imports_dict, ("required",))
        else:
            all_graph[mid] = []
    from .resolve import find_cycle_participants as _fcp
    cycle_ids = set(_fcp(all_graph))

    lines: list[str] = []
    for r in results[:limit]:
        mid = r["id"]
        mem_type = r["type"]
        deps = r.get("dependents", 0)
        access = r.get("access_count", 0)

        # R13-M2: exclude cycle participants from dependents count
        if mid in cycle_ids:
            deps = 0

        # R13-M1/M3/M4: time-decay heat calculation using precomputed
        # days_since_last_access and per-memory stability (default 14.0).
        # Standard formula: decay = 0.5^(days / stability)
        # Access bonus = access_count * decay
        # Zero-access memories get minimal access bonus (10% weight).
        entry = index.memories.get(mid)
        stability = max(entry.stability, 0.1) if entry else 14.0  # C2: clamp to safe minimum
        # C1 fix: read days_since_last_access from MemoryEntry (not from search dict),
        # as search() previously did not include this field. Also apply C2 safety clamp.
        days_since = entry.days_since_last_access if entry else None
        if access > 0 and days_since is not None:
            days_since = max(0, days_since)
            decay = _retrieval_prob(days_since, stability)
            access_bonus = access * decay
        else:
            access_bonus = access * 0.1

        heat = int(deps * 10 + access_bonus)
        entry_status = r.get("status", "active")
        tags_str = _fmt_tags(r)
        summary = r.get("summary", "")

        stale = _stale_check(root, r)
        stale_mark = " [stale]" if stale else ""
        status_mark = f"[{entry_status}]"

        if format_mode == "inject":
            line = (
                f"[{mid}]({mem_type}, heat:{heat}, {entry_status})"
                f"[{tags_str}] {summary}{stale_mark}"
            )
            if len(line) > 120:
                line = line[:117] + "..."
            lines.append(line)
        else:
            lines.append(
                f"{mid:45s} {mem_type:9s} heat:{heat:3d} "
                f"{status_mark}{stale_mark}  [{tags_str}]"
            )
            if summary:
                lines.append(f"    {summary}")

    # --with-recall: append wander inject
    if with_recall:
        all_mems = index.memories
        candidates = [
            (mid, e) for mid, e in all_mems.items() if e.intensity < 8
        ]
        if candidates:
            # R13-M1: use unified decay formula for cool wander weighting
            candidates.sort(key=lambda x: x[1].access_count)
            cutoff = max(1, len(candidates) // 3)
            pool = candidates[:cutoff]
            mid, entry = random.choice(pool)
            tags_str = _fmt_tags(entry)
            lines.append(
                f"[recall] {mid} — {entry.summary}"
                f"（tags: {tags_str}）"
            )

    return "\n".join(lines)


def handle_wander(
    root: Path,
    tags: list[str] | None = None,
    mode: str = "cool",
    inject: bool = False,
) -> str:
    """Random walk through memories. Returns formatted output."""
    index = load_index(root)
    memories = index.memories
    candidates = list(memories.items())
    if tags:
        candidates = [
            (mid, entry)
            for mid, entry in candidates
            if all(t in entry.tags for t in tags)
        ]
    if not candidates:
        return "(no matching memories)"

    inject_mode = inject
    if mode == "cool":
        # Weighted random: lower decay-adjusted access -> higher weight (R13-M1)
        cool_candidates = [
            (mid, entry)
            for mid, entry in candidates
            if entry.intensity < 8
        ]
        if not cool_candidates:
            cool_candidates = candidates

        weights = []
        for _mid, entry in cool_candidates:
            stability = max(getattr(entry, 'stability', 14.0), 0.1)  # C2: clamp to safe minimum
            days_since = getattr(entry, 'days_since_last_access', None)
            if entry.access_count > 0 and days_since is not None:
                decay = _retrieval_prob(max(0, days_since), stability)
                weight = 1.0 / (entry.access_count * decay + 1)
            else:
                weight = 1.0  # Never accessed — maximally cool
            weights.append(weight)
        mid, entry = random.choices(cool_candidates, weights=weights, k=1)[0]
        mode_label = "[cool]"
    else:
        mid, entry = random.choice(candidates)
        mode_label = "[random]"

    tags_str = _fmt_tags(entry)

    if inject_mode:
        return (
            f"[recall] {mid} — {entry.summary}"
            f"（tags: {tags_str}）"
        )

    lines: list[str] = []
    lines.append(f"# Wander {mode_label}: {mid}  [{tags_str}]\n")
    if entry.summary:
        lines.append(f"> {entry.summary}")
    lines.append(
        f"Type: {entry.type}, "
        f"Status: {entry.status}, "
        f"Intensity: {entry.intensity}, "
        f"Access: {entry.access_count}"
    )

    # Forward deps
    imports_dict = entry.imports
    if isinstance(imports_dict, dict):
        all_imports = _resolve_import_ids(imports_dict)
        if all_imports:
            lines.append("\nForward deps (imports):")
            for ref in all_imports:
                lines.append(f"  -> {ref}")

    # Reverse deps
    reverse_deps: list[str] = []
    for other_id, other_entry in memories.items():
        if other_id == mid:
            continue
        other_imports = other_entry.imports
        if not isinstance(other_imports, dict):
            continue
        all_refs = _resolve_import_ids(other_imports)
        for ref_id in all_refs:
            if ref_id == mid:
                reverse_deps.append(other_id)
                break

    if reverse_deps:
        lines.append("\nReverse deps (referenced by):")
        for dep_id in reverse_deps:
            lines.append(f"  <- {dep_id}")
    elif mode == "cool":
        lines.append("\n(orphaned -- no other memory references this one)")

    return "\n".join(lines)


def handle_orphans(
    root: Path,
    type_: str | None = None,
    min_intensity: int | None = None,
) -> str:
    """Find orphaned memories. Returns formatted listing."""
    orphans = find_orphans(root, type_=type_, min_intensity=min_intensity)
    if not orphans:
        return "(no orphaned memories)"
    lines: list[str] = []
    for o in orphans:
        ann = f"[{o['annotation']}]"
        last = o.get("last_access") or "never"
        lines.append(
            f"{o['id']:45s} {o['type']:9s} "
            f"intensity:{o['intensity']:2d}  "
            f"access:{o['access_count']:3d}  "
            f"last:{last}  {ann}"
        )
    return "\n".join(lines)


def handle_snapshot(
    root: Path,
    snapshot_id: str,
    target: str | None = None,
    budget: int | None = None,
    from_dag: str | None = None,
) -> str:
    """Persist a snapshot. One of ``target`` or ``from_dag`` must be provided."""
    if from_dag:
        # Load TransientDAG from JSON file
        from .transient import TransientDAG

        dag_path = Path(from_dag)
        if not dag_path.exists():
            return f"Error: DAG file not found: {from_dag}"
        dag_data = json.loads(dag_path.read_text(encoding="utf-8"))
        dag = TransientDAG.from_dict(dag_data)
        snap_path = snapshot_dag(root, dag, snapshot_id)
        return f"Snapshot '{snapshot_id}' saved to {snap_path} ({snap_path.read_text(encoding='utf-8').__len__()} chars)"
    else:
        target_id = target or snapshot_id
        output = resolve(root, target_id, depth="required", budget=budget)
        snap_dir = root / "user" / "snapshots"
        snap_dir.mkdir(parents=True, exist_ok=True)
        from datetime import datetime as _dt
        today = _dt.now().strftime("%Y-%m-%d")
        snap_path = snap_dir / f"{today}-{snapshot_id}.md"
        snap_path.write_text(output, encoding="utf-8")
        # Auto-reindex after snapshot
        from .index import reindex as _reindex
        _reindex(root)
        return f"Snapshot '{snapshot_id}' saved to {snap_path} ({len(output)} chars)"


def handle_changelog(root: Path, memory_id: str) -> str:
    """View change history for a memory. Returns formatted changelog."""
    index = load_index(root)
    if memory_id not in index.memories:
        return f"Error: Memory '{memory_id}' not found in index. Did you reindex?"

    entry = index.memories[memory_id]
    file_path = root / entry.path
    meta, _body = _pfm(file_path)

    change_log = meta.get("change_log", [])
    if not isinstance(change_log, list) or not change_log:
        return f"No change history for '{memory_id}'."

    lines: list[str] = []
    lines.append(f"# Changelog for '{memory_id}'\n")
    for entry_log in change_log:
        if isinstance(entry_log, dict):
            ver = entry_log.get("version", "?")
            date = entry_log.get("date", "?")
            note = entry_log.get("note", "")
            lines.append(f"v{ver} ({date}): {note}")
        elif isinstance(entry_log, str):
            lines.append(f"- {entry_log}")
    return "\n".join(lines)


def handle_log(root: Path, limit: int = 20) -> str:
    """View global log entries. Returns formatted log."""
    return show_log(root, limit=limit)


def handle_import(
    root: Path,
    text: str,
    extract_types: list[str] | None = None,
) -> str:
    """Import memories from text. Returns summary of created files."""
    paths = import_text(root, text, extract_types=extract_types)
    if not paths:
        return "(no memories imported)"
    return "\n".join(str(p) for p in paths)


def handle_skeletonize(
    root: Path,
    source: str,
    min_intensity: int = 5,
    dry_run: bool = False,
    tags: list[str] | None = None,
) -> str:
    """Skeletonize Markdown files into CodeMemory memories.

    Reads .md files from *source* (file or directory), splits each into
    sections, applies intensity-based truncation, and writes each section
    as a memory atom in *root*.
    """
    import re
    import yaml

    from .skeletonize.common import slugify as _slug
    from .skeletonize.common import extract_first_sentence as _first_sent

    source_path = Path(source).resolve()
    if not source_path.exists():
        return f"Error: source not found: {source}"

    # Collect .md files
    md_files: list[Path] = []
    if source_path.is_file():
        if source_path.suffix == '.md':
            md_files = [source_path]
        else:
            return f"Error: not a .md file: {source}"
    else:
        md_files = sorted(source_path.rglob('*.md'))

    if not md_files:
        return f"No .md files found in: {source}"

    tags = tags or []
    total_sections = 0
    created: list[str] = []

    for md_file in md_files:
        try:
            text = md_file.read_text(encoding='utf-8')
        except Exception as e:
            _logger.warning("Skipping %s: %s", md_file, e)
            continue

        sections = skeletonize_markdown(text, min_intensity=min_intensity)

        # Build ID prefix from relative path
        try:
            rel = md_file.relative_to(source_path) if source_path.is_dir() else Path(md_file.name)
        except ValueError:
            rel = Path(md_file.name)
        # /-separated path parts with sanitized names
        parts = list(rel.parts[:-1]) + [rel.stem]
        clean_parts = [re.sub(r'[^\w-]', '-', p.lower()).strip('-')[:30] for p in parts]
        prefix = '/'.join(p for p in clean_parts if p)

        for i, section in enumerate(sections):
            heading_slug = _slug(section.heading) if section.heading else f'section-{i}'
            memory_id = f'user/imports/{prefix}/{heading_slug}'

            summary = _first_sent(section.body, max_chars=100) if section.body else (section.heading or 'Untitled')

            body_text = f'# {section.heading}\n\n{section.body}' if section.heading else section.body

            frontmatter = {
                'type': 'atom',
                'id': memory_id,
                'summary': summary,
                'status': 'active',
                'created': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                'updated': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                'version': 1,
                'tags': tags + ['skeletonized'],
                'intensity': section.intensity,
                'maturity': 'draft',
                'source': {
                    'platform': 'skeletonize',
                    'created_by': 'codememory skeletonize',
                    'original_file': str(rel),
                },
            }

            frontmatter['summary_hash'] = _cbh(body_text)

            yaml_str = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)
            content = f'---\n{yaml_str}---\n{body_text}\n'

            if dry_run:
                print(f'[{memory_id}] (intensity={section.intensity})')
                preview = body_text[:200] + ('...' if len(body_text) > 200 else '')
                print(preview)
                print()
                created.append(f'[dry-run] {memory_id}')
            else:
                file_path = get_memory_path(root, memory_id)
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content, encoding='utf-8')
                print(f'Skeletonized: {file_path} (intensity={section.intensity})')
                created.append(str(file_path))

            total_sections += 1

    if not dry_run and created:
        from .index import reindex as _reindex
        _reindex(root)
        try:
            from .log import append_log as _append_log
            _append_log(root, 'skeletonize', f'{len(created)} memories from {len(md_files)} file(s)')
        except ImportError:
            pass

    return (
        f'Skeletonized {total_sections} section(s) from {len(md_files)} file(s)\n'
        + '\n'.join(created)
    )


def handle_suggest_deps(
    root: Path,
    memory_id: str,
    min_score: int = 3,
    forward_only: bool = False,
    retroactive_only: bool = False,
) -> str:
    """Suggest dependencies for a memory via three-layer filtering."""
    return suggest_deps(
        root,
        memory_id,
        min_score=min_score,
        forward_only=forward_only,
        retroactive_only=retroactive_only,
    )
