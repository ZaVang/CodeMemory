"""CodeMemory CLI — thin argparse shell delegating to package modules."""

import argparse
import sys
from pathlib import Path

from .core import get_root_dir
from .create import create
from .index import reindex
from .orphans import find_orphans
from .resolve import resolve
from .search import search
from .update import update
from .validate import validate


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="CodeMemory — memory atomization protocol",
    )
    parser.add_argument(
        "--root",
        help="Root directory for memory data (defaults to CODEMEMORY_ROOT env or CWD)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = subparsers.add_parser("create", help="Create a new memory")
    p_create.add_argument(
        "--type",
        required=True,
        choices=["atom", "schema", "instance", "composite"],
    )
    p_create.add_argument("--id", required=True)
    p_create.add_argument("--schema", help="Schema ID (required if type=instance)")
    p_create.add_argument(
        "--intensity",
        type=int,
        default=5,
        help="Relevance score 1-10 (default: 5)",
    )
    p_create.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview frontmatter and body without creating file",
    )
    p_create.add_argument(
        "--tags",
        help="Comma-separated tags (e.g. 'a,b,c'), default: ['untagged']",
    )

    # update
    p_update = subparsers.add_parser("update", help="Update an existing memory with version control")
    p_update.add_argument("id", help="Memory ID to update")
    p_update.add_argument("--change-note", required=True, help="Explanation of what changed and why")
    p_update.add_argument("--body", help="New body text")
    p_update.add_argument("--summary", help="New summary")
    p_update.add_argument("--status", choices=["active", "archived", "superseded", "draft"], help="New status")
    p_update.add_argument("--import-required", nargs="*", help="Replacement required imports")
    p_update.add_argument("--import-recommended", nargs="*", help="Replacement recommended imports")
    p_update.add_argument("--import-related", nargs="*", help="Replacement related imports")

    # resolve
    p_resolve = subparsers.add_parser("resolve", help="Resolve and print memory context")
    p_resolve.add_argument("id", help="Memory ID to resolve")
    p_resolve.add_argument(
        "--depth",
        choices=["required", "recommended", "full"],
        default="required",
    )
    p_resolve.add_argument("--budget", type=int, help="Token budget (chars)")

    # reindex
    p_reindex = subparsers.add_parser("reindex", help="Rebuild index.json")

    # validate
    p_validate = subparsers.add_parser("validate", help="Run integrity checks")

    # search
    p_search = subparsers.add_parser("search", help="Search memories")
    p_search.add_argument("--query", "-q", help="Substring match against summary")
    p_search.add_argument("--tags", "-t", nargs="*", help="Filter by tags (AND logic)")
    p_search.add_argument(
        "--type",
        "-T",
        dest="type_",
        choices=["atom", "schema", "instance", "composite"],
        help="Filter by memory type",
    )
    p_search.add_argument(
        "--status",
        "-s",
        choices=["active", "archived", "superseded", "draft"],
        help="Filter by memory status",
    )

    # focus (Layer 0: 注视)
    p_focus = subparsers.add_parser("focus", help="Focus on a memory with adjustable resolution")
    p_focus.add_argument("id", help="Memory ID to focus on")
    p_focus.add_argument(
        "--level",
        choices=["full", "summary"],
        default="full",
        help="Resolution level",
    )
    p_focus.add_argument(
        "--content",
        help="Body content (skip disk read, in-context zoom)",
    )
    p_focus.add_argument(
        "--summary",
        dest="summary_override",
        help="Summary text (skip disk read, in-context zoom)",
    )
    p_focus.add_argument(
        "--resolve",
        action="store_true",
        help="Auto-resolve dependency subgraph before focusing",
    )

    # overview (Layer 0: 扫视)
    p_overview = subparsers.add_parser("overview", help="Overview of top relevant memories")
    p_overview.add_argument("--tags", nargs="*", help="Filter by tags")
    p_overview.add_argument("--limit", type=int, default=5, help="Max results (default: 5)")
    p_overview.add_argument(
        "--format",
        choices=["default", "inject"],
        default="default",
        help="Output format: 'inject' for compact system-prompt injection",
    )
    p_overview.add_argument(
        "--status",
        default=None,
        help="Filter by status. Default: exclude archived. Use 'all' to show all.",
    )
    p_overview.add_argument(
        "--with-recall",
        action="store_true",
        help="Append a wander recall line at the end",
    )

    # wander (Layer 0: 触景生情)
    p_wander = subparsers.add_parser("wander", help="Random walk through memories")
    p_wander.add_argument("--tags", nargs="*", help="Filter by tags")
    p_wander.add_argument(
        "--mode",
        choices=["cool", "random"],
        default="cool",
        help="Selection mode: cool biases toward cold memories (default), random is equal probability",
    )
    p_wander.add_argument(
        "--inject",
        action="store_true",
        help="Output compact [recall] format for system prompt injection",
    )

    # orphans
    p_orphans = subparsers.add_parser("orphans", help="Find orphaned memories (in-degree zero)")
    p_orphans.add_argument(
        "--type",
        "-T",
        dest="type_",
        choices=["atom", "schema", "instance", "composite"],
        help="Filter by memory type",
    )
    p_orphans.add_argument(
        "--min-intensity",
        type=int,
        help="Minimum intensity filter",
    )

    # snapshot (Layer 0: 残留)
    p_snapshot = subparsers.add_parser("snapshot", help="Persist a transient context snapshot")
    p_snapshot.add_argument("id", help="Snapshot identifier")
    p_snapshot.add_argument(
        "--target",
        help="Memory ID to resolve and snapshot (defaults to snapshot id)",
    )
    p_snapshot.add_argument("--budget", type=int, help="Token budget")
    p_snapshot.add_argument(
        "--from-dag",
        help="Path to JSON file containing a serialized TransientDAG (from dag.to_dict())",
    )

    args = parser.parse_args(argv)

    root = get_root_dir(args.root)

    if args.command == "create":
        if args.type == "instance" and not args.schema:
            parser.error("--schema is required when type is 'instance'")
        tags_list = None
        if args.tags:
            tags_list = [t.strip() for t in args.tags.split(",") if t.strip()]
        create(
            root,
            args.type,
            args.id,
            schema=args.schema,
            intensity=args.intensity,
            tags=tags_list,
            dry_run=args.dry_run,
        )

    elif args.command == "update":
        update(
            root,
            args.id,
            body=args.body,
            summary=args.summary,
            change_note=args.change_note,
            status=args.status,
            import_required=args.import_required,
            import_recommended=args.import_recommended,
            import_related=args.import_related,
        )

    elif args.command == "reindex":
        reindex(root)

    elif args.command == "resolve":
        output = resolve(root, args.id, depth=args.depth, budget=args.budget)
        print(output)

    elif args.command == "validate":
        errors, _warnings = validate(root)
        if errors > 0:
            sys.exit(1)

    elif args.command == "search":
        results = search(root, query=args.query, tags=args.tags, type_=args.type_, status=args.status)
        if not results:
            print("(no results)")
        for r in results:
            tags_str = ", ".join(r.get("tags", []))
            print(
                f"{r['id']:40s}  {r['type']:9s}  "
                f"deps:{r['dependents']:3d}  [{tags_str}]"
            )
            if r.get("summary"):
                print(f"    {r['summary']}")

    elif args.command == "focus":
        # Focus: print a single memory at the requested resolution.
        # Supports --content/--summary for in-context zoom (no disk read).
        # Supports --resolve for auto-resolving dependency subgraph first.

        # --resolve: auto-resolve dependency subgraph before focusing
        if getattr(args, "resolve", False):
            output = resolve(root, args.id, depth="recommended")
            print(output)
            return

        content_override = getattr(args, "content", None)
        summary_override = getattr(args, "summary_override", None)

        # In-context zoom: use provided content/summary, skip disk read
        if content_override is not None and summary_override is not None:
            if args.level == "summary":
                print(f"# {args.id}\n\n> {summary_override}")
            else:
                print(content_override)
            return

        # Default: read from disk (backward compatible)
        from .index import load_index
        from .core import parse_frontmatter

        index = load_index(root)
        if args.id not in index["memories"]:
            print(
                f"Error: Memory '{args.id}' not found in index. Did you reindex?",
                file=sys.stderr,
            )
            sys.exit(1)
        entry = index["memories"][args.id]
        file_path = root / entry["path"]
        _meta, body = parse_frontmatter(file_path)

        if args.level == "summary":
            print(f"# {args.id}\n\n> {entry['summary']}")
        else:
            print(body)

    elif args.command == "overview":
        # Overview: list top memories with heat score, status, stale detection
        from .core import parse_frontmatter as _pfm, compute_body_hash as _cbh

        results = search(root, tags=args.tags)

        # Filter by status: exclude archived by default
        status_filter = getattr(args, "status", None)
        if status_filter and status_filter != "all":
            results = [r for r in results if r.get("status") == status_filter]
        elif not status_filter or status_filter != "all":
            results = [r for r in results if r.get("status") != "archived"]

        format_mode = getattr(args, "format", "default")

        for r in results[: args.limit]:
            mid = r["id"]
            mem_type = r["type"]
            deps = r.get("dependents", 0)
            access = r.get("access_count", 0)
            heat = deps * 10 + access
            status = r.get("status", "active")
            tags_str = ", ".join(r.get("tags", []))
            summary = r.get("summary", "")

            # Stale detection: compare stored summary_hash vs actual body hash
            stale = False
            file_path = root / r["path"]
            if file_path.exists():
                meta, body = _pfm(file_path)
                stored_hash = meta.get("summary_hash", "")
                if stored_hash:
                    actual_hash = _cbh(body)
                    if stored_hash != actual_hash:
                        stale = True

            stale_mark = " [stale]" if stale else ""
            status_mark = f"[{status}]"

            if format_mode == "inject":
                # Compact format: [id](type, heat:N, status)[tags] summary
                line = (
                    f"[{mid}]({mem_type}, heat:{heat}, {status})"
                    f"[{tags_str}] {summary}{stale_mark}"
                )
                if len(line) > 120:
                    line = line[:117] + "..."
                print(line)
            else:
                print(
                    f"{mid:45s} {mem_type:9s} heat:{heat:3d} "
                    f"{status_mark}{stale_mark}  [{tags_str}]"
                )
                if summary:
                    print(f"    {summary}")

        # --with-recall: append a wander inject line at the end
        if getattr(args, "with_recall", False):
            import random as _random

            from .index import load_index as _load_index

            _index = _load_index(root)
            _all_mems = _index["memories"]
            _candidates = [
                (_mid, _e)
                for _mid, _e in _all_mems.items()
                if _e.get("intensity", 5) < 8
            ]
            if _candidates:
                _candidates.sort(key=lambda x: x[1].get("access_count", 0))
                _cutoff = max(1, len(_candidates) // 3)
                _pool = _candidates[:_cutoff]
                _mid, _entry = _random.choice(_pool)
                _tags_str = ", ".join(_entry.get("tags", []))
                print(
                    f"[recall] {_mid} — {_entry.get('summary', '')}"
                    f"（tags: {_tags_str}）"
                )

    elif args.command == "wander":
        # Wander: random memory exploration
        import random

        from .index import load_index

        index = load_index(root)
        memories = index["memories"]
        candidates = list(memories.items())
        if args.tags:
            candidates = [
                (mid, entry)
                for mid, entry in candidates
                if all(t in entry.get("tags", []) for t in args.tags)
            ]
        if not candidates:
            print("(no matching memories)")
            return

        mode = args.mode if hasattr(args, "mode") else "cool"
        inject_mode = getattr(args, "inject", False)

        if mode == "cool":
            # Bias toward cold memories: select from lowest 1/3 by access_count,
            # excluding protected (intensity >= 8)
            cool_candidates = [
                (mid, entry)
                for mid, entry in candidates
                if entry.get("intensity", 5) < 8
            ]
            if not cool_candidates:
                # Fallback to all candidates if all are protected
                cool_candidates = candidates

            # Sort by access_count ascending, take lowest 1/3
            cool_candidates.sort(key=lambda x: x[1].get("access_count", 0))
            cutoff = max(1, len(cool_candidates) // 3)
            pool = cool_candidates[:cutoff]
            mid, entry = random.choice(pool)
            mode_label = "[cool]"
        else:
            mid, entry = random.choice(candidates)
            mode_label = "[random]"

        tags_str = ", ".join(entry.get("tags", []))

        # --inject: single-line [recall] format for system prompt injection
        if inject_mode:
            print(
                f"[recall] {mid} — {entry.get('summary', '')}"
                f"（tags: {tags_str}）"
            )
            return

        print(f"# Wander {mode_label}: {mid}  [{tags_str}]\n")
        if entry.get("summary"):
            print(f"> {entry['summary']}")
        print(
            f"Type: {entry.get('type')}, "
            f"Status: {entry.get('status', 'active')}, "
            f"Intensity: {entry.get('intensity', 5)}, "
            f"Access: {entry.get('access_count', 0)}"
        )

        # Show neighbors: forward deps (imports) and reverse deps (who references this)
        imports_dict = entry.get("imports", {})
        if isinstance(imports_dict, dict):
            all_imports = (
                imports_dict.get("required", [])
                + imports_dict.get("recommended", [])
                + imports_dict.get("related", [])
            )
            if all_imports:
                print(f"\nForward deps (imports):")
                for ref in all_imports:
                    ref_id = ref if isinstance(ref, str) else ref.get("id", "?")
                    print(f"  -> {ref_id}")

        # Reverse deps: which memories reference this one?
        reverse_deps = []
        for other_id, other_entry in memories.items():
            if other_id == mid:
                continue
            other_imports = other_entry.get("imports", {})
            if not isinstance(other_imports, dict):
                continue
            all_refs = (
                other_imports.get("required", [])
                + other_imports.get("recommended", [])
                + other_imports.get("related", [])
            )
            for ref in all_refs:
                ref_id = ref if isinstance(ref, str) else ref.get("id", "")
                if ref_id == mid:
                    reverse_deps.append(other_id)
                    break

        if reverse_deps:
            print(f"\nReverse deps (referenced by):")
            for dep_id in reverse_deps:
                print(f"  <- {dep_id}")
        elif mode == "cool":
            print(f"\n(orphaned -- no other memory references this one)")

    elif args.command == "orphans":
        orphans = find_orphans(root, type_=args.type_, min_intensity=args.min_intensity)
        if not orphans:
            print("(no orphaned memories)")
        for o in orphans:
            ann = f"[{o['annotation']}]"
            last = o.get("last_access") or "never"
            print(
                f"{o['id']:45s} {o['type']:9s} "
                f"intensity:{o['intensity']:2d}  "
                f"access:{o['access_count']:3d}  "
                f"last:{last}  {ann}"
            )

    elif args.command == "snapshot":
        if args.from_dag:
            # Load TransientDAG from JSON file
            import json
            from .transient import TransientDAG

            dag_path = Path(args.from_dag)
            if not dag_path.exists():
                print(
                    f"Error: DAG file not found: {args.from_dag}",
                    file=sys.stderr,
                )
                sys.exit(1)
            dag_data = json.loads(dag_path.read_text(encoding="utf-8"))
            dag = TransientDAG.from_dict(dag_data)

            from .snapshot import snapshot_dag
            snapshot_dag(root, dag, args.id)
        else:
            target = args.target or args.id
            output = resolve(
                root, target, depth="required", budget=args.budget
            )
            snap_dir = root / ".codememory" / "snapshots"
            snap_dir.mkdir(parents=True, exist_ok=True)
            snap_path = snap_dir / f"{args.id}.md"
            snap_path.write_text(output, encoding="utf-8")
            print(f"Snapshot '{args.id}' saved to {snap_path} ({len(output)} chars)")


if __name__ == "__main__":
    main()
