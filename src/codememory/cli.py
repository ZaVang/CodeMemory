"""CodeMemory CLI — thin argparse shell delegating to package modules."""

import argparse
import sys

from .core import get_root_dir
from .create import create
from .index import reindex
from .resolve import resolve
from .search import search
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

    # focus (Layer 0: 注视)
    p_focus = subparsers.add_parser("focus", help="Focus on a memory with adjustable resolution")
    p_focus.add_argument("id", help="Memory ID to focus on")
    p_focus.add_argument(
        "--level",
        choices=["full", "summary"],
        default="full",
        help="Resolution level",
    )

    # overview (Layer 0: 扫视)
    p_overview = subparsers.add_parser("overview", help="Overview of top relevant memories")
    p_overview.add_argument("--tags", nargs="*", help="Filter by tags")
    p_overview.add_argument("--limit", type=int, default=5, help="Max results (default: 5)")

    # wander (Layer 0: 触景生情)
    p_wander = subparsers.add_parser("wander", help="Random walk through memories")
    p_wander.add_argument("--tags", nargs="*", help="Filter by tags")

    # snapshot (Layer 0: 残留)
    p_snapshot = subparsers.add_parser("snapshot", help="Persist a transient context snapshot")
    p_snapshot.add_argument("id", help="Snapshot identifier")

    args = parser.parse_args(argv)

    root = get_root_dir(args.root)

    if args.command == "create":
        if args.type == "instance" and not args.schema:
            parser.error("--schema is required when type is 'instance'")
        create(root, args.type, args.id, schema=args.schema, intensity=args.intensity)

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
        results = search(root, query=args.query, tags=args.tags, type_=args.type_)
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
        # Focus: print a single memory at the requested resolution
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
        # Overview: list top memories by dependency count
        results = search(root, tags=args.tags)
        for r in results[: args.limit]:
            print(
                f"{r['id']:40s}  {r['type']:9s}  "
                f"deps:{r['dependents']:3d}"
            )
            if r.get("summary"):
                print(f"    {r['summary']}")

    elif args.command == "wander":
        # Wander: random memory exploration
        import random

        from .index import load_index

        index = load_index(root)
        candidates = list(index["memories"].items())
        if args.tags:
            candidates = [
                (mid, entry)
                for mid, entry in candidates
                if all(t in entry.get("tags", []) for t in args.tags)
            ]
        if not candidates:
            print("(no matching memories)")
            return
        mid, entry = random.choice(candidates)
        tags_str = ", ".join(entry.get("tags", []))
        print(f"# Random Memory: {mid}  [{tags_str}]\n")
        if entry.get("summary"):
            print(f"> {entry['summary']}")
        print(f"Type: {entry.get('type')}, Status: {entry.get('status', 'active')}")

    elif args.command == "snapshot":
        # Snapshot: placeholder for transient context persistence
        print(f"Snapshot '{args.id}' recorded (placeholder, full persistence TBD).")


if __name__ == "__main__":
    main()
