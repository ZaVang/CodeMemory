"""Memory search: lexical entry discovery (architecture.md §4.2).

Query tokens are matched case-insensitively as substrings against id,
summary, tags, and body. score = Σ(field_weight × hits/total_tokens)
with weights id=4 / summary=3 / tags=2 / body=1; OR semantics across
tokens; untokenizable queries fall back to whole-string substring match.
"""

import re
from pathlib import Path

from .core import parse_frontmatter
from .index import load_index
from .models import IndexData

_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)


def _tokenize(query: str) -> list[str]:
    """Split a query on whitespace/punctuation into lowercase tokens."""
    return [t.lower() for t in _TOKEN_RE.findall(query)]


def _count_dependents(memory_id: str, index: IndexData) -> int:
    """Count how many other memories import this one."""
    count = 0
    for mid, entry in index.memories.items():
        imports_dict = entry.imports
        if not isinstance(imports_dict, dict):
            continue
        all_refs = (
            imports_dict.get("required", [])
            + imports_dict.get("recommended", [])
            + imports_dict.get("related", [])
        )
        for ref in all_refs:
            ref_id = ref if isinstance(ref, str) else ref.get("id", "")
            if ref_id == memory_id:
                count += 1
                break
    return count


def _extract_snippet(body: str, query: str, context_chars: int = 40) -> str:
    """Extract a snippet from body text around the first query match."""
    if not body or not query:
        return ""
    q_lower = query.lower()
    body_lower = body.lower()
    idx = body_lower.find(q_lower)
    if idx >= 0:
        start = max(0, idx - context_chars)
        end = min(len(body), idx + len(query) + context_chars)
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(body) else ""
        snippet = prefix + body[start:end].replace("\n", " ") + suffix
        return snippet
    return ""


def search(
    root_dir: Path,
    query: str | None = None,
    tags: list[str] | None = None,
    type_: str | None = None,
    status: str | None = None,
    maturity: str | None = None,
    semantic_type: str | None = None,
    has_imports: bool = False,
    has_schema: bool = False,
) -> list[dict]:
    """Search memories by query, tags, type, status, maturity, and/or semantic type.

    R16-C1: Query now matches against body full-text in addition to summary, tags,
    and ID. Exact ID match > summary/tags match > body full-text match.
    Body snippets are included for body matches.

    Builds output dicts from MemoryEntry.model_dump() to eliminate field divergence
    between search output and the canonical data model (R15-C4).
    Any field added to MemoryEntry automatically appears in search results.

    Results are sorted by dependents descending, then access_count descending,
    then id ascending.

    Phase A: when ``status`` is None, only active/draft memories are returned;
    proposed/archived/superseded require an explicit status filter.
    """
    index = load_index(root_dir)
    results: list[dict] = []

    for mid, entry in index.memories.items():
        if type_ and entry.type != type_:
            continue
        if status:
            if entry.status != status:
                continue
        elif entry.status not in ("active", "draft"):
            # Default view shows only assemblable statuses; proposed/archived/
            # superseded require an explicit --status filter (Phase A contract).
            continue
        if maturity and entry.maturity != maturity:
            continue
        if semantic_type and semantic_type not in entry.tags:
            continue
        if tags:
            if not all(t in entry.tags for t in tags):
                continue

        # Lexical scoring against id, summary, tags, and body full-text.
        match_kind = ""  # "id" | "summary" | "tag" | "body"
        snippet = ""
        score = 0.0
        if query:
            q_lower = query.lower()
            tokens = _tokenize(query)
            body = ""
            file_path = root_dir / entry.path
            if file_path.exists():
                _, body = parse_frontmatter(file_path)
            body_lower = body.lower()

            if tokens:
                total = len(tokens)
                id_hits = sum(1 for t in tokens if t in mid.lower())
                summary_hits = sum(1 for t in tokens if t in entry.summary.lower())
                tag_hits = sum(1 for t in tokens
                               if any(t in tag.lower() for tag in entry.tags))
                body_hits = sum(1 for t in tokens if t in body_lower)
                score = (4.0 * id_hits + 3.0 * summary_hits
                         + 2.0 * tag_hits + 1.0 * body_hits) / total
                if score == 0:
                    continue
                # Display field: strongest field with at least one hit
                if id_hits:
                    match_kind = "id"
                elif summary_hits:
                    match_kind = "summary"
                elif tag_hits:
                    match_kind = "tag"
                else:
                    match_kind = "body"
                    first_hit = next(t for t in tokens if t in body_lower)
                    snippet = _extract_snippet(body, first_hit)
            else:
                # Fallback: untokenizable query — legacy whole-string substring
                if q_lower in mid.lower():
                    match_kind = "id"
                elif q_lower in entry.summary.lower():
                    match_kind = "summary"
                elif any(q_lower in t.lower() for t in entry.tags):
                    match_kind = "tag"
                elif body and q_lower in body_lower:
                    match_kind = "body"
                    snippet = _extract_snippet(body, query)
                else:
                    continue

        if has_imports:
            imports_dict = entry.imports
            if not isinstance(imports_dict, dict) or not any(
                imports_dict.get(k) for k in ("required", "recommended", "related")
            ):
                continue
        if has_schema and not entry.schema:
            continue

        # R15-C4: Build output from model_dump() + computed fields.
        # This ensures all MemoryEntry fields are present, eliminating
        # "field missing from search output" bugs permanently.
        dump = entry.model_dump(mode="json")
        dump["id"] = mid  # Ensure id uses the index key
        dump["dependents"] = _count_dependents(mid, index)
        if query:
            dump["score"] = round(score, 3)
        if match_kind:
            dump["match_field"] = match_kind
        if snippet:
            dump["snippet"] = snippet
        results.append(dump)

    results.sort(key=lambda r: (
        -r.get("score", 0.0), -r["dependents"], -r["access_count"], r["id"],
    ))
    return results
