"""CodeMemory CLI — thin argparse shell delegating to handlers."""

import argparse
import sys
from pathlib import Path

from .core import configure_logging, get_root_dir
from .handlers import (
    handle_build,
    handle_changelog,
    handle_compile_md,
    handle_context_pack,
    handle_create,
    handle_import,
    handle_log,
    handle_materialize_review,
    handle_merge,
    handle_orphans,
    handle_propose,
    handle_proposals,
    handle_reindex,
    handle_reject,
    handle_resolve,
    handle_search,
    handle_source_add,
    handle_source_check,
    handle_source_expand,
    handle_source_get,
    handle_source_list,
    handle_skeletonize,
    handle_test,
    handle_test_report,
    handle_snapshot,
    handle_diff,
    handle_suggest_deps,
    handle_update,
    handle_validate,
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
    p.add_argument("--dry-run", action="store_true", help="Preview without creating file")
    p.add_argument("--tags", help="Comma-separated tags")
    p.add_argument("--maturity", choices=["draft", "verified", "proven"], default="draft",
                   help="Initial maturity (default: draft)")
    p.add_argument("--cache-stable", action="store_true", dest="cache_stable",
                   help="Mark as suitable for LLM cache prefix")
    p.add_argument("--lifecycle", choices=["permanent", "stable", "ephemeral"], default="permanent",
                   help="Lifecycle: permanent (never auto-archive), stable (auto-upgrade), ephemeral (auto-archive when unused)")
    p.add_argument("--propose", action="store_true",
                   help="Create as a proposal (status: proposed); excluded from default build/search until merged")

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
    p.add_argument("--source-ref", dest="source_ref",
                   help="Asset artifact_id to append to source_refs")
    p.add_argument("--source-ref-summary", dest="source_ref_summary",
                   help="Optional summary for the appended source ref")

    # test
    p = subparsers.add_parser("test", help="Export golden questions with assembled context (agent is the runner)")
    _add_logging_flags(p)
    p.add_argument("target", help="Entry memory ID, or 'report' to record runner results")
    p.add_argument("subtarget", nargs="?", help="Entry memory ID (report mode)")
    p.add_argument("--results", help="Path to results JSON file (report mode)")
    p.add_argument("--depth", choices=["required", "recommended", "full"], default="recommended")
    p.add_argument("--budget", type=int)

    # merge
    p = subparsers.add_parser("merge", help="Merge a proposal (patch-queue id or proposed memory id)")
    _add_logging_flags(p)
    p.add_argument("id", help="Proposal ID or memory ID to merge")

    # reject
    p = subparsers.add_parser("reject", help="Reject a proposal (patch-queue id or proposed memory id)")
    _add_logging_flags(p)
    p.add_argument("id", help="Proposal ID or memory ID to reject")

    # propose (modification-class proposal against an existing atom)
    p = subparsers.add_parser("propose", help="Queue a modification proposal against an existing atom")
    _add_logging_flags(p)
    p.add_argument("id", help="Target memory ID")
    p.add_argument("--reason", required=True, help="Why this change should happen")
    p.add_argument("--summary")
    p.add_argument("--body")
    p.add_argument("--import-required", nargs="*")
    p.add_argument("--import-recommended", nargs="*")
    p.add_argument("--import-related", nargs="*")
    p.add_argument("--source-ref", dest="source_ref")

    # proposals (list the pending queue)
    p = subparsers.add_parser("proposals", help="List pending modification proposals")
    _add_logging_flags(p)

    # resolve
    p = subparsers.add_parser("resolve", help="Resolve and print memory context")
    _add_logging_flags(p)
    p.add_argument("id", help="Memory ID to resolve")
    p.add_argument("--depth", choices=["required", "recommended", "full"], default="required")
    p.add_argument("--budget", type=int)
    p.add_argument("--focus", help="Keep full text only for nodes matching this semantic type tag")

    # build (primary assembly verb; resolve/context-pack are aliases of the same pipeline)
    p = subparsers.add_parser("build", help="Assemble context from an entry memory (unified pipeline)")
    _add_logging_flags(p)
    p.add_argument("id", help="Entry memory ID to build context from")
    p.add_argument("--depth", choices=["required", "recommended", "full"], default="recommended")
    p.add_argument("--budget", type=int)
    p.add_argument("--focus", help="Keep full text only for nodes matching this semantic type tag")
    p.add_argument("--task-goal", help="Optional task goal to embed in the output")
    p.add_argument("--format", dest="output_format", choices=["xml-markdown", "markdown", "plain-markdown", "json"],
                   default="xml-markdown")

    # context-pack
    p = subparsers.add_parser("context-pack", help="Build a structured agent handoff context pack")
    _add_logging_flags(p)
    p.add_argument("id", help="Memory ID to resolve into a context pack")
    p.add_argument("--depth", choices=["required", "recommended", "full"], default="recommended")
    p.add_argument("--budget", type=int)
    p.add_argument("--focus", help="Keep full text only for nodes matching this semantic type tag")
    p.add_argument("--task-goal", help="Optional task goal to embed in the context pack")
    p.add_argument("--format", dest="output_format", choices=["xml-markdown", "markdown", "plain-markdown", "json"],
                   default="xml-markdown")

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
    p.add_argument("--status", "-s", choices=["active", "proposed", "archived", "superseded", "draft"])
    p.add_argument("--maturity", "-m", choices=["draft", "verified", "proven", "superseded"])
    p.add_argument("--semantic-type", dest="semantic_type", help="Filter by semantic type tag (e.g. decision, model, guideline)")
    p.add_argument("--has-imports", action="store_true", help="Filter to memories with non-empty imports")
    p.add_argument("--has-schema", action="store_true", help="Filter to memories with a schema reference")

    # source
    p = subparsers.add_parser("source", help="Manage Source Artifact registry")
    _add_logging_flags(p)
    source_subparsers = p.add_subparsers(dest="source_command", required=True)

    sp = source_subparsers.add_parser("add", help="Register a Source Artifact")
    sp.add_argument("uri", help="Local path or external URI")
    sp.add_argument("--id", dest="source_id", help="Stable Source Artifact ID")
    sp.add_argument("--kind", choices=["markdown", "code", "text", "pdf", "url", "external"])
    sp.add_argument("--summary", default="")

    sp = source_subparsers.add_parser("list", help="List Source Artifacts")

    sp = source_subparsers.add_parser("get", help="Show one Source Artifact as JSON")
    sp.add_argument("id", help="Source Artifact ID")

    sp = source_subparsers.add_parser("check", help="Check Source Artifacts for missing/stale state")
    sp.add_argument("id", nargs="?", help="Optional Source Artifact ID")

    sp = source_subparsers.add_parser("expand", help="Expand a Source Artifact as JSON")
    sp.add_argument("id", help="Source Artifact ID")
    sp.add_argument("--start", type=int, help="Optional character start offset")
    sp.add_argument("--end", type=int, help="Optional character end offset")
    sp.add_argument("--max-chars", dest="max_chars", type=int, help="Maximum characters to return")

    # orphans
    p = subparsers.add_parser("orphans", help="Find orphaned memories")
    _add_logging_flags(p)
    p.add_argument("--type", "-T", dest="type_", choices=["atom", "schema"])

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

    # diff
    p = subparsers.add_parser("diff", help="Show what changed since last index snapshot")
    _add_logging_flags(p)
    p.add_argument("--since", help="Path to snapshot or semantic time (e.g. '2 days ago', '1 hour ago')")

    # skeletonize
    p = subparsers.add_parser("skeletonize", help="Import structured memories from Markdown/code files")
    _add_logging_flags(p)
    p.add_argument("source", help=".md/.py/.js/.ts file or directory")
    p.add_argument("--min-weight", "--min-intensity", dest="min_weight", type=int, default=5,
                   help="Sections below this weight are truncated (default: 5); --min-intensity is a deprecated alias")
    p.add_argument("--dry-run", action="store_true",
                   help="Preview without writing files")
    p.add_argument("--tags", help="Comma-separated tags for generated memories")
    p.add_argument("--format", dest="output_format", choices=["memory", "html"],
                   default="memory",
                   help="Output format: memory (default, write to DAG) or html (self-contained HTML)")
    p.add_argument("--output-dir", help="Output directory for HTML files (required with --format html)")
    p.add_argument("--mode", choices=["file", "module"], default="file",
                   help="Code skeletonization mode: file (weight-based) or module (zero-config, signatures only)")
    p.add_argument("--config", help="Path to .codememory/skeletonize.yaml (auto-detected from cwd by default)")

    # compile-md
    p = subparsers.add_parser("compile-md", help="Compile Markdown corpus into a review set")
    _add_logging_flags(p)
    p.add_argument("source", help="Markdown file or directory to compile")
    p.add_argument("--review-id", help="Stable review ID; defaults to timestamp")
    p.add_argument("--tags", help="Comma-separated tags for generated proposals")
    p.add_argument("--namespace", default="user/imports", help="Memory ID namespace for proposals")

    # materialize-review
    p = subparsers.add_parser("materialize-review", help="Materialize accepted compiler proposals")
    _add_logging_flags(p)
    p.add_argument("review_id", help="Review ID from compile-md")
    p.add_argument("--accept-all", action="store_true", help="Accept all pending proposals before materializing")

    args = parser.parse_args(argv)

    configure_logging(verbose=args.verbose, quiet=args.quiet)

    root = get_root_dir(args.root)
    cmd = args.command

    if cmd == "create":
        tags_list = None
        if args.tags:
            tags_list = [t.strip() for t in args.tags.split(",") if t.strip()]
        print(handle_create(root, args.type, args.id, schema=args.schema,
                            tags=tags_list, dry_run=args.dry_run,
                            maturity=args.maturity, cache_stable=args.cache_stable,
                            lifecycle=args.lifecycle, propose=args.propose))
    elif cmd == "update":
        print(handle_update(root, args.id, body=args.body, summary=args.summary,
                            change_note=args.change_note, status=args.status,
                            import_required=args.import_required,
                            import_recommended=args.import_recommended,
                            import_related=args.import_related,
                            source_ref=args.source_ref,
                            source_ref_summary=args.source_ref_summary))
    elif cmd == "test":
        if args.target == "report":
            if not args.subtarget or not args.results:
                parser.error("test report requires <entry> and --results <file>")
            print(handle_test_report(root, args.subtarget, args.results))
        else:
            print(handle_test(root, args.target, depth=args.depth, budget=args.budget))
    elif cmd == "merge":
        print(handle_merge(root, args.id))
    elif cmd == "reject":
        print(handle_reject(root, args.id))
    elif cmd == "propose":
        print(handle_propose(root, args.id, reason=args.reason,
                             summary=args.summary, body=args.body,
                             import_required=args.import_required,
                             import_recommended=args.import_recommended,
                             import_related=args.import_related,
                             source_ref=args.source_ref))
    elif cmd == "proposals":
        print(handle_proposals(root))
    elif cmd == "reindex":
        handle_reindex(root)
    elif cmd == "resolve":
        print(handle_resolve(root, args.id, depth=args.depth, budget=args.budget,
                            focus=args.focus))
    elif cmd == "build":
        print(handle_build(
            root,
            args.id,
            depth=args.depth,
            budget=args.budget,
            focus=args.focus,
            task_goal=args.task_goal,
            output_format=args.output_format,
        ))
    elif cmd == "context-pack":
        print(handle_context_pack(
            root,
            args.id,
            depth=args.depth,
            budget=args.budget,
            focus=args.focus,
            task_goal=args.task_goal,
            output_format=args.output_format,
        ))
    elif cmd == "validate":
        errors = handle_validate(root)
        if errors > 0:
            sys.exit(1)
    elif cmd == "search":
        print(handle_search(root, query=args.query, tags=args.tags, type_=args.type_,
                            status=args.status, maturity=args.maturity,
                            semantic_type=args.semantic_type,
                            has_imports=args.has_imports, has_schema=args.has_schema))
    elif cmd == "source":
        if args.source_command == "add":
            print(handle_source_add(
                root,
                uri=args.uri,
                source_id=args.source_id,
                kind=args.kind,
                summary=args.summary,
            ))
        elif args.source_command == "list":
            print(handle_source_list(root))
        elif args.source_command == "get":
            print(handle_source_get(root, args.id))
        elif args.source_command == "check":
            print(handle_source_check(root, args.id))
        elif args.source_command == "expand":
            print(handle_source_expand(
                root,
                args.id,
                start=args.start,
                end=args.end,
                max_chars=args.max_chars,
            ))
    elif cmd == "orphans":
        print(handle_orphans(root, type_=args.type_))
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
    elif cmd == "diff":
        print(handle_diff(root, since=args.since))
    elif cmd == "skeletonize":
        tags_list = None
        if args.tags:
            tags_list = [t.strip() for t in args.tags.split(",") if t.strip()]
        print(handle_skeletonize(
            root, args.source,
            min_weight=args.min_weight,
            dry_run=args.dry_run,
            tags=tags_list,
            output_format=args.output_format,
            output_dir=args.output_dir,
            mode=args.mode,
            config=args.config,
        ))
    elif cmd == "compile-md":
        tags_list = None
        if args.tags:
            tags_list = [t.strip() for t in args.tags.split(",") if t.strip()]
        print(handle_compile_md(
            root,
            args.source,
            review_id=args.review_id,
            tags=tags_list,
            namespace=args.namespace,
        ))
    elif cmd == "materialize-review":
        print(handle_materialize_review(
            root,
            args.review_id,
            accept_all=args.accept_all,
        ))


if __name__ == "__main__":
    main()
