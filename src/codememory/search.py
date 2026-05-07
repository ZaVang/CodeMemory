"""Memory search: query by summary, tags, type, body, sorted by dependency count."""

from pathlib import Path

from .core import parse_frontmatter
from .index import load_index
from .models import IndexData


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
    """
    index = load_index(root_dir)
    results: list[dict] = []

    for mid, entry in index.memories.items():
        if type_ and entry.type != type_:
            continue
        if status and entry.status != status:
            continue
        if maturity and entry.maturity != maturity:
            continue
        if semantic_type and semantic_type not in entry.tags:
            continue
        if tags:
            if not all(t in entry.tags for t in tags):
                continue

        # R16-C1: search query against id, summary, tags, AND body full-text
        match_kind = ""  # "id" | "summary" | "tag" | "body"
        snippet = ""
        if query:
            q_lower = query.lower()
            # Priority: exact ID match > summary match > tag match > body match
            if q_lower in mid.lower():
                match_kind = "id"
            elif q_lower in entry.summary.lower():
                match_kind = "summary"
            elif any(q_lower in t.lower() for t in entry.tags):
                match_kind = "tag"
            else:
                # R16-C1: full-text body search
                file_path = root_dir / entry.path
                if file_path.exists():
                    _, body = parse_frontmatter(file_path)
                    if q_lower in body.lower():
                        match_kind = "body"
                        snippet = _extract_snippet(body, query)
                if not match_kind:
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
        if match_kind:
            dump["match_field"] = match_kind
        if snippet:
            dump["snippet"] = snippet
        results.append(dump)

    results.sort(key=lambda r: (-r["dependents"], -r["access_count"], r["id"]))
    return results
