"""CodeMemory CLI — thin argparse shell delegating to handlers."""

import argparse
import sys

from .core import configure_logging, get_root_dir
from .handlers import (
    handle_changelog,
    handle_create,
    handle_focus,
    handle_import,
    handle_log,
    handle_orphans,
    handle_overview,
    handle_reindex,
    handle_resolve,
    handle_search,
    handle_skeletonize,
    handle_snapshot,
    handle_suggest_deps,
    handle_update,
    handle_validate,
    handle_wander,
)


def _add_logging_flags(subparser):
    """Add --verbose / --quiet flags to a subparser."""
    subparser.add_argument("--verbose", "-v", action="store_true", help="Show INFO-level log messages")
    subparser.add_argument("--quiet", action="store_true", help="Suppress log messages below ERROR")


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="CodeMemory — memory atomization protocol")
    parser.add_argument("--root", help="Root directory for memory data")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create
    p = subparsers.add_parser("create", help="Create a new memory")
    _add_logging_flags(p)
    p.add_argument("--type", default="atom", choices=["atom", "schema"], help="Memory type (default: atom)")
    p.add_argument("--id", required=True)
    p.add_argument("--schema")
    p.add_argument("--intensity", type=int, default=5, help="Relevance score 1-10 (default: 5)")
    p.add_argument("--dry-run", action="store_true", help="Preview without creating file")
    p.add_argument("--tags", help="Comma-separated tags")
    p.add_argument("--maturity", choices=["draft", "verified", "proven"], default="draft",
                   help="Initial maturity (default: draft)")
    p.add_argument("--cache-stable", action="store_true", dest="cache_stable",
                   help="Mark as suitable for LLM cache prefix")

    # update
    p = subparsers.add_parser("update", help="Update an existing memory")
    _add_logging_flags(p)
    p.add_argument("id", help="Memory ID to update")
    p.add_argument("--change-note", required=True)
    p.add_argument("--body")
    p.add_argument("--summary")
    p.add_argument("--status", choices=["active", "archived", "superseded", "draft"])
    p.add_argument("--import-required", nargs="*")
    p.add_argument("--import-recommended", nargs="*")
    p.add_argument("--import-related", nargs="*")

    # resolve
    p = subparsers.add_parser("resolve", help="Resolve and print memory context")
    _add_logging_flags(p)
    p.add_argument("id", help="Memory ID to resolve")
    p.add_argument("--depth", choices=["required", "recommended", "full"], default="required")
    p.add_argument("--budget", type=int)
    p.add_argument("--focus", help="Keep full text only for nodes matching this semantic type tag")

    # reindex
    p = subparsers.add_parser("reindex", help="Rebuild index.json")
    _add_logging_flags(p)

    # validate
    p = subparsers.add_parser("validate", help="Run integrity checks")
    _add_logging_flags(p)

    # search (uses -q for --query, so different flag handling)
    p = subparsers.add_parser("search", help="Search memories")
    p.add_argument("--verbose", "-v", action="store_true")
    p.add_argument("--quiet", action="store_true")
    p.add_argument("--query", "-q", help="Substring match against summary")
    p.add_argument("--tags", "-t", nargs="*", help="Filter by tags (AND logic)")
    p.add_argument("--type", "-T", dest="type_", choices=["atom", "schema"])
    p.add_argument("--status", "-s", choices=["active", "archived", "superseded", "draft"])
    p.add_argument("--maturity", "-m", choices=["draft", "verified", "proven", "superseded"])
    p.add_argument("--semantic-type", dest="semantic_type", help="Filter by semantic type tag (e.g. decision, model, guideline)")
    p.add_argument("--has-imports", action="store_true", help="Filter to memories with non-empty imports")
    p.add_argument("--has-schema", action="store_true", help="Filter to memories with a schema reference")

    # focus
    p = subparsers.add_parser("focus", help="Focus on a memory")
    _add_logging_flags(p)
    p.add_argument("id", help="Memory ID")
    p.add_argument("--level", choices=["full", "summary"], default="full")
    p.add_argument("--content", help="Body content (in-context zoom)")
    p.add_argument("--summary", dest="summary_override", help="Summary text (in-context zoom)")
    p.add_argument("--resolve", action="store_true", help="Auto-resolve before focusing")

    # overview
    p = subparsers.add_parser("overview", help="Overview of top memories")
    _add_logging_flags(p)
    p.add_argument("--tags", nargs="*")
    p.add_argument("--limit", type=int, default=5)
    p.add_argument("--format", choices=["default", "inject"], default="default")
    p.add_argument("--status", default=None)
    p.add_argument("--with-recall", action="store_true")

    # wander
    p = subparsers.add_parser("wander", help="Random walk through memories")
    _add_logging_flags(p)
    p.add_argument("--tags", nargs="*")
    p.add_argument("--mode", choices=["cool", "random"], default="cool")
    p.add_argument("--inject", action="store_true", help="Compact [recall] format")

    # orphans
    p = subparsers.add_parser("orphans", help="Find orphaned memories")
    _add_logging_flags(p)
    p.add_argument("--type", "-T", dest="type_", choices=["atom", "schema"])
    p.add_argument("--min-intensity", type=int)

    # snapshot
    p = subparsers.add_parser("snapshot", help="Persist a transient context snapshot")
    _add_logging_flags(p)
    p.add_argument("id", help="Snapshot identifier")
    p.add_argument("--target")
    p.add_argument("--budget", type=int)
    p.add_argument("--from-dag")

    # changelog
    p = subparsers.add_parser("changelog", help="View change history for a memory")
    _add_logging_flags(p)
    p.add_argument("id", help="Memory ID")

    # log
    p = subparsers.add_parser("log", help="View global operation log")
    _add_logging_flags(p)
    p.add_argument("--limit", type=int, default=20, help="Max entries (default: 20)")

    # import
    p = subparsers.add_parser("import", help="Import memories from text (cold start)")
    _add_logging_flags(p)
    p.add_argument("--file", help="Path to input file")
    p.add_argument("--stdin", action="store_true", help="Read from stdin")
    p.add_argument("--extract", help="Comma-separated tags for extracted memories")

    # suggest-deps
    p = subparsers.add_parser("suggest-deps", help="Suggest dependency imports for a memory")
    _add_logging_flags(p)
    p.add_argument("id", help="Target memory ID")
    p.add_argument("--min-score", type=int, default=3,
                   help="Minimum score threshold (default: 3)")
    p.add_argument("--forward-only", action="store_true",
                   help="Show only forward candidates (target should import them)")
    p.add_argument("--retroactive-only", dest="retroactive_only", action="store_true",
                   help="Show only retroactive candidates (they should import the target)")

    # skeletonize
    p = subparsers.add_parser("skeletonize", help="Import structured memories from Markdown/code files")
    _add_logging_flags(p)
    p.add_argument("source", help=".md/.py/.js/.ts file or directory")
    p.add_argument("--min-intensity", type=int, default=5,
                   help="Sections below this intensity are truncated (default: 5)")
    p.add_argument("--dry-run", action="store_true",
                   help="Preview without writing files")
    p.add_argument("--tags", help="Comma-separated tags for generated memories")
    p.add_argument("--format", dest="output_format", choices=["memory", "html"],
                   default="memory",
                   help="Output format: memory (default, write to DAG) or html (self-contained HTML)")
    p.add_argument("--output-dir", help="Output directory for HTML files (required with --format html)")
    p.add_argument("--mode", choices=["file", "module"], default="file",
                   help="Code skeletonization mode: file (intensity-based) or module (zero-config, signatures only)")
    p.add_argument("--config", help="Path to .codememory/skeletonize.yaml (auto-detected from cwd by default)")

    args = parser.parse_args(argv)

    configure_logging(verbose=args.verbose, quiet=args.quiet)

    root = get_root_dir(args.root)
    cmd = args.command

    if cmd == "create":
        tags_list = None
        if args.tags:
            tags_list = [t.strip() for t in args.tags.split(",") if t.strip()]
        print(handle_create(root, args.type, args.id, schema=args.schema,
                            intensity=args.intensity, tags=tags_list, dry_run=args.dry_run,
                            maturity=args.maturity, cache_stable=args.cache_stable))
    elif cmd == "update":
        print(handle_update(root, args.id, body=args.body, summary=args.summary,
                            change_note=args.change_note, status=args.status,
                            import_required=args.import_required,
                            import_recommended=args.import_recommended,
                            import_related=args.import_related))
    elif cmd == "reindex":
        handle_reindex(root)
    elif cmd == "resolve":
        print(handle_resolve(root, args.id, depth=args.depth, budget=args.budget,
                            focus=args.focus))
    elif cmd == "validate":
        errors = handle_validate(root)
        if errors > 0:
            sys.exit(1)
    elif cmd == "search":
        print(handle_search(root, query=args.query, tags=args.tags, type_=args.type_,
                            status=args.status, maturity=args.maturity,
                            semantic_type=args.semantic_type,
                            has_imports=args.has_imports, has_schema=args.has_schema))
    elif cmd == "focus":
        print(handle_focus(root, args.id, level=args.level, content=args.content,
                           summary_override=args.summary_override, resolve_flag=args.resolve))
    elif cmd == "overview":
        print(handle_overview(root, tags=args.tags, limit=args.limit,
                              format_mode=args.format, status=args.status,
                              with_recall=args.with_recall))
    elif cmd == "wander":
        print(handle_wander(root, tags=args.tags, mode=args.mode, inject=args.inject))
    elif cmd == "orphans":
        print(handle_orphans(root, type_=args.type_, min_intensity=args.min_intensity))
    elif cmd == "snapshot":
        print(handle_snapshot(root, args.id, target=args.target,
                              budget=args.budget, from_dag=args.from_dag))
    elif cmd == "changelog":
        print(handle_changelog(root, args.id))
    elif cmd == "log":
        print(handle_log(root, limit=args.limit))
    elif cmd == "import":
        if args.stdin:
            text = sys.stdin.read()
        elif args.file:
            text = Path(args.file).read_text(encoding="utf-8")
        else:
            parser.error("import requires --stdin or --file")
        extract_types = None
        if args.extract:
            extract_types = [t.strip() for t in args.extract.split(",") if t.strip()]
        print(handle_import(root, text, extract_types=extract_types))
    elif cmd == "suggest-deps":
        print(handle_suggest_deps(
            root, args.id,
            min_score=args.min_score,
            forward_only=args.forward_only,
            retroactive_only=args.retroactive_only,
        ))
    elif cmd == "skeletonize":
        tags_list = None
        if args.tags:
            tags_list = [t.strip() for t in args.tags.split(",") if t.strip()]
        print(handle_skeletonize(
            root, args.source,
            min_intensity=args.min_intensity,
            dry_run=args.dry_run,
            tags=tags_list,
            output_format=args.output_format,
            output_dir=args.output_dir,
            mode=args.mode,
            config=args.config,
        ))


if __name__ == "__main__":
    main()
