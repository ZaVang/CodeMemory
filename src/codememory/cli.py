"""CodeMemory CLI — thin argparse shell delegating to handlers."""

import argparse
import asyncio
import sys
from pathlib import Path

from .core import configure_logging, get_root_dir
from .handlers import (
    handle_build,
    handle_capture,
    handle_changelog,
    handle_compile_md,
    handle_compile_md_llm,
    handle_context_pack,
    handle_create,
    handle_import,
    handle_init_personal,
    handle_log,
    handle_materialize_review,
    handle_maintenance_resume,
    handle_maintenance_run,
    handle_maintenance_status,
    handle_merge,
    handle_orphans,
    handle_periodic_review_prepare,
    handle_periodic_review_save,
    handle_propose,
    handle_proposals,
    handle_reindex,
    handle_read,
    handle_review_batch,
    handle_reject,
    handle_resolve,
    handle_search,
    handle_semantic_index,
    handle_semantic_status,
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
    handle_eval,
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

    # Personal Profile init (Git remains optional and is never initialized here)
    p = subparsers.add_parser("init", help="Initialize or validate a memory profile")
    _add_logging_flags(p)
    p.add_argument("path", help="Instance directory")
    p.add_argument("--profile", choices=["personal"], required=True)
    p.add_argument("--owner", default="owner")
    p.add_argument("--timezone", default="Asia/Hong_Kong")
    p.add_argument("--auto-commit", action="store_true")
    p.add_argument("--auto-push", action="store_true")
    p.add_argument("--remote", default="origin")
    p.add_argument("--branch", default="main")

    # append-only Personal Profile Capture
    p = subparsers.add_parser("capture", help="Append a Capture to a Personal Profile journal")
    _add_logging_flags(p)
    p.add_argument("text", nargs="?", help="Capture payload")
    p.add_argument("--stdin", action="store_true", help="Read the Capture payload from stdin")
    p.add_argument("--actor", help="Capture actor (defaults to profile owner)")

    p = subparsers.add_parser("read", help="Read a Capture or Topic revision by stable ID")
    _add_logging_flags(p)
    p.add_argument("id", help="Capture ID or Topic revision ID")

    p = subparsers.add_parser("maintenance", help="Run or inspect Personal Profile maintenance")
    _add_logging_flags(p)
    maintenance_subparsers = p.add_subparsers(dest="maintenance_command", required=True)
    maintenance_subparsers.add_parser("status", help="Show active run and unconsumed Captures")
    mp = maintenance_subparsers.add_parser("run", help="Apply a deterministic Topic changeset")
    mp.add_argument("--changeset", required=True, help="JSON changeset generated through the Personal Memory Skill")
    maintenance_subparsers.add_parser("resume", help="Resume the same pending or blocked run")

    p = subparsers.add_parser("review-batch", help="Apply promote/merge/delete Topic decisions")
    _add_logging_flags(p)
    p.add_argument("--file", required=True, help="JSON list of review decisions")

    p = subparsers.add_parser(
        "periodic-review",
        help="Prepare or explicitly persist a Personal monthly/yearly review",
    )
    _add_logging_flags(p)
    periodic_subparsers = p.add_subparsers(dest="periodic_review_command", required=True)
    pp = periodic_subparsers.add_parser("prepare", help="Build a deterministic review evidence bundle")
    pp.add_argument("--period", choices=["monthly", "yearly"], required=True)
    pp.add_argument("--anchor", required=True, help="YYYY-MM for monthly or YYYY for yearly")
    pp.add_argument("--output", help="Optional no-clobber JSON output path")
    ps = periodic_subparsers.add_parser("save", help="Persist one owner-requested review Markdown")
    ps.add_argument("--bundle", required=True, help="Prepared periodic review bundle JSON")
    ps.add_argument("--content", required=True, help="Authored Markdown body")
    ps.add_argument("--created-by", default="agent:codex")
    ps.add_argument("--overwrite", action="store_true", help="Owner-confirmed replacement for this period")

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

    # eval (explicit provider-backed three-arm golden-question experiment)
    p = subparsers.add_parser(
        "eval",
        help="Compare ContextPack, full-memory and no-memory with a blind LLM judge",
    )
    _add_logging_flags(p)
    p.add_argument("id", help="Entry memory ID with scored golden questions")
    p.add_argument("--llm-config", required=True, help="Explicit llm_gateway YAML config path")
    p.add_argument("--answer-model", required=True, help="Answer model alias or provider/model")
    p.add_argument("--judge-model", required=True, help="Blind judge model alias or provider/model")
    p.add_argument("--depth", choices=["required", "recommended", "full"], default="recommended")
    p.add_argument("--budget", type=int)
    p.add_argument("--answer-max-tokens", type=int, default=1024)
    p.add_argument("--judge-max-tokens", type=int, default=512)
    p.add_argument("--output", help="Optional JSON report path; stdout when omitted")
    p.add_argument("--overwrite", action="store_true", help="Replace the exact --output path")

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
    p.add_argument("--kind", dest="kinds", nargs="+",
                   choices=["capture", "incubator_topic", "incubator_claim", "atom"],
                   help="Filter by typed object kind")
    p.add_argument("--from", dest="date_from", help="Earliest date (YYYY-MM-DD)")
    p.add_argument("--to", dest="date_to", help="Latest date (YYYY-MM-DD)")
    p.add_argument("--topic")
    p.add_argument("--project")
    p.add_argument("--person")
    p.add_argument("--origin")
    p.add_argument("--claim-status", dest="claim_status")
    p.add_argument("--semantic", action="store_true",
                   help="Use the explicitly enabled local Personal semantic index")
    p.add_argument("--limit", dest="semantic_limit", type=int, default=10,
                   help="Maximum semantic candidates (default: 10)")

    # Personal semantic derived-index operations
    p = subparsers.add_parser("semantic", help="Manage local Personal semantic discovery")
    _add_logging_flags(p)
    semantic_subparsers = p.add_subparsers(dest="semantic_command", required=True)
    semantic_subparsers.add_parser("index", help="Build or reuse the local derived index")
    semantic_subparsers.add_parser("status", help="Show disabled/missing/stale/ready state")

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
    p = subparsers.add_parser("compile-md", help="Register Markdown sources and build an anchor/derived review set")
    _add_logging_flags(p)
    p.add_argument("source", help="Markdown file or directory to compile")
    p.add_argument("--review-id", help="Stable review ID; defaults to timestamp")
    p.add_argument("--tags", help="Comma-separated tags for generated proposals")
    p.add_argument("--namespace", help="Proposal namespace (default: user/imports deterministic, user for LLM)")
    p.add_argument("--proposer", choices=["deterministic", "llm"], default="deterministic",
                   help="Proposal engine; LLM mode is explicit opt-in")
    p.add_argument("--llm-config", help="Explicit llm_gateway YAML config path (LLM proposer only)")
    p.add_argument("--llm-model", help="Explicit model alias or provider/model (LLM proposer only)")
    p.add_argument("--llm-max-tokens", type=int, default=4096,
                   help="Maximum structured output tokens in LLM mode (default: 4096)")

    # materialize-review
    p = subparsers.add_parser("materialize-review", help="Materialize accepted compiler candidates as proposed atoms")
    _add_logging_flags(p)
    p.add_argument("review_id", help="Review ID from compile-md")
    p.add_argument("--accept-all", action="store_true", help="Accept all pending proposals before materializing")

    args = parser.parse_args(argv)

    configure_logging(verbose=args.verbose, quiet=args.quiet)

    root = get_root_dir(args.root)
    cmd = args.command

    if cmd == "init":
        print(handle_init_personal(
            Path(args.path),
            owner=args.owner,
            timezone_name=args.timezone,
            auto_commit=args.auto_commit,
            auto_push=args.auto_push,
            remote=args.remote,
            branch=args.branch,
        ))
    elif cmd == "capture":
        if args.stdin and args.text is not None:
            parser.error("capture accepts either text or --stdin, not both")
        if args.stdin:
            payload = sys.stdin.read()
        elif args.text is not None:
            payload = args.text
        else:
            parser.error("capture requires text or --stdin")
        print(handle_capture(root, payload, actor=args.actor))
    elif cmd == "read":
        print(handle_read(root, args.id))
    elif cmd == "maintenance":
        if args.maintenance_command == "status":
            print(handle_maintenance_status(root))
        elif args.maintenance_command == "run":
            changeset = None
            if args.changeset:
                import json
                changeset = json.loads(Path(args.changeset).read_text(encoding="utf-8"))
            print(handle_maintenance_run(root, changeset))
        else:
            print(handle_maintenance_resume(root))
    elif cmd == "review-batch":
        import json
        decisions = json.loads(Path(args.file).read_text(encoding="utf-8"))
        if not isinstance(decisions, list):
            parser.error("review-batch file must contain a JSON list")
        print(handle_review_batch(root, decisions))
    elif cmd == "periodic-review":
        if args.periodic_review_command == "prepare":
            print(handle_periodic_review_prepare(
                root,
                period=args.period,
                anchor=args.anchor,
                output=Path(args.output) if args.output else None,
            ))
        else:
            print(handle_periodic_review_save(
                root,
                bundle_path=Path(args.bundle),
                content_path=Path(args.content),
                created_by=args.created_by,
                overwrite=args.overwrite,
            ))
    elif cmd == "create":
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
    elif cmd == "eval":
        if args.overwrite and not args.output:
            parser.error("eval --overwrite requires --output")
        print(asyncio.run(handle_eval(
            root,
            args.id,
            config_path=args.llm_config,
            answer_model=args.answer_model,
            judge_model=args.judge_model,
            depth=args.depth,
            budget=args.budget,
            answer_max_tokens=args.answer_max_tokens,
            judge_max_tokens=args.judge_max_tokens,
            output=args.output,
            overwrite=args.overwrite,
        )))
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
                            has_imports=args.has_imports, has_schema=args.has_schema,
                            kinds=args.kinds, date_from=args.date_from, date_to=args.date_to,
                            topic=args.topic, project=args.project, person=args.person,
                            origin=args.origin, claim_status=args.claim_status,
                            semantic=args.semantic, semantic_limit=args.semantic_limit))
    elif cmd == "semantic":
        if args.semantic_command == "index":
            print(handle_semantic_index(root))
        else:
            print(handle_semantic_status(root))
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
        if args.proposer == "llm":
            if not args.llm_config or not args.llm_model:
                parser.error("--proposer llm requires --llm-config and --llm-model")
            if args.llm_max_tokens < 1:
                parser.error("--llm-max-tokens must be positive")
            print(asyncio.run(handle_compile_md_llm(
                root,
                args.source,
                config_path=args.llm_config,
                model=args.llm_model,
                review_id=args.review_id,
                tags=tags_list,
                namespace=args.namespace or "user",
                max_tokens=args.llm_max_tokens,
            )))
        else:
            if args.llm_config or args.llm_model or args.llm_max_tokens != 4096:
                parser.error("LLM flags require --proposer llm")
            print(handle_compile_md(
                root,
                args.source,
                review_id=args.review_id,
                tags=tags_list,
                namespace=args.namespace or "user/imports",
            ))
    elif cmd == "materialize-review":
        print(handle_materialize_review(
            root,
            args.review_id,
            accept_all=args.accept_all,
        ))


if __name__ == "__main__":
    main()
