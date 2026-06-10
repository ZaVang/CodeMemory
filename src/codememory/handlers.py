"""Shared command handlers — single source of truth for CLI and Sandbox tools.

Each handler takes a root directory plus keyword arguments and returns a
string result.  Error conditions raise ``codememory`` errors (the callers
decide whether to print to stderr, sys.exit, or return an error dict).
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from .compiler.materialize import materialize_review_set
from .compiler.propose import compile_markdown_corpus
from .compiler.review import load_review_set, save_review_set, set_all_decisions
from .build import build_context_pack, render_context_pack
from .core import compute_body_hash as _cbh
from .core import get_memory_path, parse_frontmatter as _pfm
from .create import create
from .import_cmd import import_text
from .index import load_index, reindex
from .log import show_log
from .orphans import find_orphans
from .resolve import resolve
from .search import search
from .snapshot import snapshot_dag
from .skeletonize.markdown import skeletonize_markdown
from .skeletonize.code import skeletonize_code, skeletonize_module
from .sources import (
    SourceKind,
    add_source_artifact,
    check_source_artifact,
    check_source_registry,
    expand_source_artifact,
    get_source_artifact,
    list_source_artifacts,
)
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
    tags: list[str] | None = None,
    dry_run: bool = False,
    maturity: str = "draft",
    cache_stable: bool = False,
    lifecycle: str = "permanent",
    propose: bool = False,
) -> str:
    """Create a new memory.  Returns path string or dry-run preview."""
    file_path = create(
        root,
        memory_type,
        memory_id,
        schema=schema,
        tags=tags,
        dry_run=dry_run,
        maturity=maturity,
        cache_stable=cache_stable,
        lifecycle=lifecycle,
        propose=propose,
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
    source_ref: str | None = None,
    source_ref_summary: str | None = None,
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
        source_ref=source_ref,
        source_ref_summary=source_ref_summary,
    )
    return str(file_path)


def handle_test(
    root: Path,
    memory_id: str,
    depth: str = "recommended",
    budget: int | None = None,
) -> str:
    """Export the entry's golden questions plus assembled context as JSON."""
    import json as _json

    from .test_contract import export_test_bundle

    bundle = export_test_bundle(root, memory_id, depth=depth, budget=budget)
    return _json.dumps(bundle.model_dump(mode="json"), ensure_ascii=False, indent=2)


def handle_test_report(root: Path, memory_id: str, results_path: str) -> str:
    """Record a runner's golden-question results into the audit log."""
    import json as _json

    from .test_contract import record_test_report

    results = _json.loads(Path(results_path).read_text(encoding="utf-8"))
    return record_test_report(root, memory_id, results)


def handle_merge(root: Path, memory_id: str) -> str:
    """Merge a proposed memory into the canonical graph. Returns path string."""
    from .update import merge

    return str(merge(root, memory_id))


def handle_reject(root: Path, memory_id: str) -> str:
    """Reject a proposal (patch-queue id or proposed atom). Returns status string."""
    from .update import reject

    result = reject(root, memory_id)
    return str(result) if result is not None else f"rejected {memory_id}"


def handle_propose(
    root: Path,
    target_id: str,
    reason: str,
    summary: str | None = None,
    body: str | None = None,
    import_required: list[str] | None = None,
    import_recommended: list[str] | None = None,
    import_related: list[str] | None = None,
    source_ref: str | None = None,
) -> str:
    """Queue a modification proposal against an existing atom."""
    from .proposals import create_proposal

    proposal = create_proposal(
        root,
        target_id,
        reason=reason,
        summary=summary,
        body=body,
        import_required=import_required,
        import_recommended=import_recommended,
        import_related=import_related,
        source_ref=source_ref,
    )
    return proposal.proposal_id


def handle_proposals(root: Path) -> str:
    """List the pending modification-proposal queue."""
    from .proposals import list_proposals

    proposals = list_proposals(root)
    if not proposals:
        return "(no pending proposals)"
    lines = []
    for p in proposals:
        fields = [name for name in ("summary", "body", "import_required",
                                    "import_recommended", "import_related", "source_ref")
                  if getattr(p.patch, name) is not None]
        lines.append(f"{p.proposal_id}  ->  {p.target_id}  [{', '.join(fields)}]  {p.reason}")
    return "\n".join(lines)


def handle_resolve(
    root: Path,
    memory_id: str,
    depth: str = "required",
    budget: int | None = None,
    focus: str | None = None,
) -> str:
    """Resolve a memory context via DAG. Returns assembled text."""
    return resolve(root, memory_id, depth=depth, budget=budget, focus=focus)


def handle_build(
    root: Path,
    memory_id: str,
    depth: str = "recommended",
    budget: int | None = None,
    focus: str | None = None,
    task_goal: str | None = None,
    output_format: str = "xml-markdown",
) -> str:
    """Run the unified assembly pipeline and render it (primary verb)."""
    pack = build_context_pack(
        root,
        memory_id,
        depth=depth,
        budget=budget,
        focus=focus,
        task_goal=task_goal,
    )
    return render_context_pack(pack, output_format)  # type: ignore[arg-type]


def handle_context_pack(
    root: Path,
    memory_id: str,
    depth: str = "recommended",
    budget: int | None = None,
    focus: str | None = None,
    task_goal: str | None = None,
    output_format: str = "xml-markdown",
) -> str:
    """Compatibility alias for handle_build (same pipeline, same output)."""
    return handle_build(
        root,
        memory_id,
        depth=depth,
        budget=budget,
        focus=focus,
        task_goal=task_goal,
        output_format=output_format,
    )


def handle_reindex(root: Path) -> str:
    """Rebuild index from disk. reindex() prints its own status; return ''."""
    reindex(root)
    return ""


def handle_validate(root: Path) -> int:
    """Run integrity checks. Prints report, returns error count for exit code."""
    errors, _warnings = validate(root)
    return errors


def handle_source_add(
    root: Path,
    uri: str,
    source_id: str | None = None,
    kind: SourceKind | None = None,
    summary: str = "",
) -> str:
    """Register a Source Artifact."""

    artifact = add_source_artifact(
        root,
        uri=uri,
        source_id=source_id,
        kind=kind,
        summary=summary,
    )
    return (
        f"source added: {artifact.id}\n"
        f"kind: {artifact.kind}\n"
        f"uri: {artifact.uri}\n"
        f"sha256: {artifact.sha256}\n"
        f"status: {artifact.status}"
    )


def handle_source_list(root: Path) -> str:
    """List registered Source Artifacts."""

    artifacts = list_source_artifacts(root)
    if not artifacts:
        return "(no source artifacts)"
    return "\n".join(
        f"{artifact.id:32s} {artifact.kind:9s} {artifact.status:8s} {artifact.uri}  {artifact.summary}"
        for artifact in artifacts
    )


def handle_source_get(root: Path, source_id: str) -> str:
    """Return a Source Artifact as JSON."""

    artifact = get_source_artifact(root, source_id)
    if artifact is None:
        return f"Error: Source Artifact '{source_id}' not found."
    return json.dumps(artifact.model_dump(mode="json"), indent=2, ensure_ascii=False)


def handle_source_check(root: Path, source_id: str | None = None) -> str:
    """Check one or all Source Artifacts for missing/stale state."""

    if source_id:
        artifact = get_source_artifact(root, source_id)
        if artifact is None:
            return f"Error: Source Artifact '{source_id}' not found."
        results = [check_source_artifact(root, artifact)]
    else:
        results = check_source_registry(root)
    if not results:
        return "(no source artifacts)"
    return "\n".join(
        f"{result.artifact_id:32s} {result.state:8s} {result.uri}  {result.message}"
        for result in results
    )


def handle_source_expand(
    root: Path,
    source_id: str,
    start: int | None = None,
    end: int | None = None,
    max_chars: int | None = None,
) -> str:
    """Expand a Source Artifact as machine-readable JSON."""

    expansion = expand_source_artifact(
        root,
        source_id,
        start=start,
        end=end,
        max_chars=max_chars,
    )
    return json.dumps(expansion.model_dump(mode="json"), indent=2, ensure_ascii=False)


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


def handle_orphans(
    root: Path,
    type_: str | None = None,
) -> str:
    """Find orphaned memories. Returns formatted listing."""
    orphans = find_orphans(root, type_=type_)
    if not orphans:
        return "(no orphaned memories)"
    lines: list[str] = []
    for o in orphans:
        ann = f"[{o['annotation']}]"
        last = o.get("last_access") or "never"
        lines.append(
            f"{o['id']:45s} {o['type']:9s} "
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


def _write_skeleton_memory(
    root: Path,
    memory_id: str,
    summary: str,
    body_text: str,
    weight: int,
    tags: list[str],
    rel: Path,
    dry_run: bool,
    created: list[str],
) -> None:
    """Write a single skeletonized memory to disk (or print preview in dry-run)."""
    frontmatter = {
        'type': 'atom',
        'id': memory_id,
        'summary': summary,
        'status': 'active',
        'created': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        'updated': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        'version': 1,
        'tags': tags + ['skeletonized'],
        'weight': weight,
        'maturity': 'draft',
        'source': {
            'platform': 'skeletonize',
            'created_by': 'codememory skeletonize',
            'original_file': str(rel),
        },
    }

    frontmatter['summary_hash'] = _cbh(body_text)

    import yaml
    yaml_str = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)
    content = f'---\n{yaml_str}---\n{body_text}\n'

    if dry_run:
        print(f'[{memory_id}] (weight={weight})')
        preview = body_text[:200] + ('...' if len(body_text) > 200 else '')
        print(preview)
        print()
        created.append(f'[dry-run] {memory_id}')
    else:
        file_path = get_memory_path(root, memory_id)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        print(f'Skeletonized: {file_path} (weight={weight})')
        created.append(str(file_path))


def handle_compile_md(
    root: Path,
    source: str,
    review_id: str | None = None,
    tags: list[str] | None = None,
    namespace: str = "user/imports",
) -> str:
    """Compile Markdown corpus into a reviewable draft proposal graph."""
    source_path = Path(source)
    if review_id is None:
        review_id = datetime.now(timezone.utc).strftime("compile-%Y%m%d-%H%M%S")

    review = compile_markdown_corpus(
        source_root=source_path,
        review_id=review_id,
        tags=tags,
        namespace=namespace,
    )
    path = save_review_set(root, review)
    return (
        f"Review set saved: {path}\n"
        f"sources: {len(review.sources)}\n"
        f"segments: {len(review.segments)}\n"
        f"proposals: {len(review.proposals)}"
    )


def handle_materialize_review(
    root: Path,
    review_id: str,
    accept_all: bool = False,
) -> str:
    """Materialize accepted proposals from a compiler review set."""
    review = load_review_set(root, review_id)
    if accept_all:
        review = set_all_decisions(review, "accepted")
        save_review_set(root, review)

    result = materialize_review_set(root, review, accept_all=False)
    lines = [
        f"written: {len(result.written)}",
        f"skipped: {len(result.skipped)}",
        f"errors: {len(result.errors)}",
    ]
    if result.errors:
        lines.append("error details:")
        lines.extend(f"- {err}" for err in result.errors)
    return "\n".join(lines)

def handle_skeletonize(
    root: Path,
    source: str,
    min_weight: int = 5,
    dry_run: bool = False,
    tags: list[str] | None = None,
    output_format: str = "memory",
    output_dir: str | None = None,
    mode: str = "file",
    config: str | None = None,
) -> str:
    """Skeletonize Markdown/code files into CodeMemory memories or HTML.

    Reads .md/.py/.js/.ts/... files from *source* (file or directory),
    splits each into sections, applies weight-based truncation, and
    either writes each section as a memory atom in *root* (--format memory)
    or generates self-contained HTML files (--format html).

    *mode* controls code skeletonization depth:
      ``"file"`` — function/class-level, respects @weight annotations
      ``"module"`` — all bodies replaced, preserves imports + signatures only
    """
    import re

    from .skeletonize.common import slugify as _slug
    from .skeletonize.common import extract_first_sentence as _first_sent
    from .skeletonize.common import render_to_html as _render_html

    source_path = Path(source).resolve()
    if not source_path.exists():
        return f"Error: source not found: {source}"

    if output_format == "html" and not output_dir and not dry_run:
        return "Error: --output-dir is required for --format html"

    output_path = Path(output_dir).resolve() if output_dir else None
    if output_path and output_format == "html" and not dry_run:
        output_path.mkdir(parents=True, exist_ok=True)

    # Collect .md files
    CODE_EXTS = {'.py', '.js', '.ts', '.jsx', '.tsx', '.mjs', '.cjs',
                 '.go', '.rs', '.java'}

    # Collect input files
    input_files: list[Path] = []
    if source_path.is_file():
        ext = source_path.suffix.lower()
        if ext == '.md' or ext in CODE_EXTS:
            input_files = [source_path]
        else:
            return f"Error: unsupported file type: {source_path.suffix}"
    else:
        input_files = sorted(source_path.rglob('*.md'))
        for ext in CODE_EXTS:
            input_files.extend(sorted(source_path.rglob(f'*{ext}')))

    if not input_files:
        return f"No supported files found in: {source}"

    tags = tags or []

    # Load skeletonize config for glob-matched weight defaults
    from .skeletonize.config import resolve_weight as _resolve_cfg_weight
    config_root: Path | None = None
    if config:
        config_root = Path(config).resolve()
    else:
        # Auto-detect: look for .codememory/skeletonize.yaml from cwd upward
        probe = Path.cwd()
        for _ in range(8):
            if (probe / '.codememory' / 'skeletonize.yaml').is_file():
                config_root = probe
                break
            if probe.parent == probe:
                break
            probe = probe.parent

    total_sections = 0
    created: list[str] = []

    for source_file in input_files:
        try:
            text = source_file.read_text(encoding='utf-8')
        except Exception as e:
            _logger.warning("Skipping %s: %s", source_file, e)
            continue

        ext = source_file.suffix.lower()

        # Build ID prefix from relative path
        try:
            rel = source_file.relative_to(source_path) if source_path.is_dir() else Path(source_file.name)
        except ValueError:
            rel = Path(source_file.name)
        parts = list(rel.parts[:-1]) + [rel.stem]
        clean_parts = [re.sub(r'[^\w-]', '-', p.lower()).strip('-')[:30] for p in parts]
        prefix = '/'.join(p for p in clean_parts if p)

        if ext == '.md':
            # Markdown: split into sections
            sections = skeletonize_markdown(text, min_weight=min_weight)
            total_sections += len(sections)

            if output_format == 'html':
                html = _render_html(
                    sections, str(source_file),
                    metadata={'tags': tags, 'weight': min_weight,
                              'min_weight': min_weight},
                )
                if dry_run:
                    created.append(f'[DRY-RUN] HTML: {source_file} ({len(sections)} sections)')
                else:
                    stem = source_file.stem or 'index'
                    out_file = output_path / f'{stem}.html'
                    out_file.write_text(html, encoding='utf-8')
                    created.append(str(out_file))
            else:
                for i, section in enumerate(sections):
                    heading_slug = _slug(section.heading) if section.heading else f'section-{i}'
                    memory_id = f'user/imports/{prefix}/{heading_slug}'
                    summary = _first_sent(section.body, max_chars=100) if section.body else (section.heading or 'Untitled')
                    body_text = f'# {section.heading}\n\n{section.body}' if section.heading else section.body
                    _write_skeleton_memory(
                        root, memory_id, summary, body_text, section.weight,
                        tags, rel, dry_run, created,
                    )
        else:
            # Code file: skeletonize whole file, one memory per file
            skel_func = skeletonize_module if mode == 'module' else skeletonize_code
            skel_kwargs: dict = {'text': text, 'file_ext': ext}
            if mode == 'file':
                skel_kwargs['min_weight'] = min_weight
            # Resolve per-file config weight
            if config_root is not None:
                cfg_weight = _resolve_cfg_weight(str(source_file), config_root)
                if cfg_weight is not None:
                    skel_kwargs['config_weight'] = cfg_weight
            skeletonized = skel_func(**skel_kwargs)
            heading_slug = _slug(source_file.stem)
            memory_id = f'user/imports/{prefix}/{heading_slug}'
            summary = _first_sent(text, max_chars=100) or source_file.stem
            body_text = f'# {source_file.stem}\n\n```{ext[1:]}\n{skeletonized}\n```\n'

            if output_format == 'html':
                from .skeletonize.markdown import Section
                sec = Section(level=1, heading=source_file.stem, body=skeletonized,
                             weight=5, raw=text)
                html = _render_html(
                    [sec], str(source_file),
                    metadata={'tags': tags + ['code'], 'weight': 5,
                              'min_weight': min_weight},
                )
                if dry_run:
                    created.append(f'[DRY-RUN] HTML: {source_file}')
                else:
                    stem = source_file.stem or 'index'
                    out_file = output_path / f'{stem}.html'
                    out_file.write_text(html, encoding='utf-8')
                    created.append(str(out_file))
            else:
                _write_skeleton_memory(
                    root, memory_id, summary, body_text, 5,
                    tags + ['code'], rel, dry_run, created,
                )
            total_sections += 1

    if not dry_run and output_format == 'memory' and created:
        from .index import reindex as _reindex
        _reindex(root)
        try:
            from .log import append_log as _append_log
            _append_log(root, 'skeletonize', f'{len(created)} memories from {len(input_files)} file(s)')
        except ImportError:
            pass

    if output_format == 'html':
        return (
            f'Skeletonized {total_sections} section(s) to HTML from {len(input_files)} file(s)\n'
            + ('\n'.join(created))
        )

    return (
        f'Skeletonized {total_sections} section(s) from {len(input_files)} file(s)\n'
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


def handle_diff(
    root: Path,
    since: str | None = None,
) -> str:
    """Show what changed since a previous index snapshot."""
    from .diff import diff as _diff
    return _diff(root, since)
