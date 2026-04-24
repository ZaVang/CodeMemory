"""
LLM Bridge — Built-in I/O tools.

``FetchURLTool``, ``ReadFileTool``, ``GlobTool``, ``SearchDocsTool``
and their internal helpers (HTML stripping, TF-IDF scoring).
"""

from __future__ import annotations

import logging
import math
import re
from pathlib import Path
from typing import Any

from ..models import ToolParam
from .base import BridgeTool

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# FetchURLTool
# ---------------------------------------------------------------------------

class FetchURLTool(BridgeTool):
    """Fetch any URL and return its text content (HTML stripped to plain text).

    Works with both public URLs and internal/intranet addresses that are
    reachable from the machine running the bridge — the HTTP request is made
    locally, NOT by the LLM provider's cloud servers.

    Parameters
    ----------
    max_chars :
        Maximum number of characters to return (default 8 000).
        Longer pages are truncated to keep token usage reasonable.
    timeout :
        Request timeout in seconds (default 15).
    headers :
        Optional dict of extra HTTP headers (e.g. ``{"Authorization": "Bearer <token>"}``).
        Useful for intranet services that require token authentication.
    """

    def __init__(
        self,
        max_chars: int = 8006,
        timeout: float = 15.0,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._max_chars = max_chars
        self._timeout = timeout
        self._headers = headers or {}

    @property
    def definition(self) -> ToolParam:
        return ToolParam(
            name="fetch_url",
            description=(
                "Fetch the content of a URL and return it as plain text. "
                "Use this to retrieve documentation, web pages, or any HTTP resource "
                "that is accessible from the local machine."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full URL to fetch (http or https).",
                    }
                },
                "required": ["url"],
            },
        )

    async def run(self, url: str, **_kwargs) -> str:  # type: ignore[override]
        """Fetch *url* and return stripped plain text."""
        try:
            import httpx
        except ImportError as exc:
            raise RuntimeError(
                "httpx is required for FetchURLTool — run: pip install httpx"
            ) from exc

        logger.info("FetchURLTool: GET %s", url)
        async with httpx.AsyncClient(
            timeout=self._timeout,
            follow_redirects=True,
            headers=self._headers,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()

        text = _html_to_text(response.text)
        if len(text) > self._max_chars:
            text = text[: self._max_chars] + "\n\n[内容已截断]"
        return text


# ---------------------------------------------------------------------------
# ReadFileTool
# ---------------------------------------------------------------------------

class ReadFileTool(BridgeTool):
    """Read a local file and return its text content.

    Optionally restrict to a line range to avoid injecting huge files into
    context.  Paths are resolved relative to ``base_dir`` (default: CWD) and
    must stay within it to prevent directory traversal.

    Parameters
    ----------
    base_dir :
        Base directory for path resolution.  Defaults to the current working
        directory.  All requested paths must resolve inside this directory.
    max_chars :
        Maximum number of characters to return (default 16 000).
    """

    def __init__(
        self,
        base_dir: Path | str | None = None,
        max_chars: int = 16_000,
    ) -> None:
        self._base_dir = Path(base_dir).resolve() if base_dir else Path.cwd()
        self._max_chars = max_chars

    @property
    def definition(self) -> ToolParam:
        return ToolParam(
            name="read_file",
            description=(
                "Read the contents of a local file and return them as text. "
                "Optionally specify start_line and end_line (1-based, inclusive) "
                "to read only a portion of a large file."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "File path, relative to the project root "
                            "or absolute (must be within the allowed base directory)."
                        ),
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "First line to return (1-based, inclusive). Defaults to 1.",
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "Last line to return (1-based, inclusive). Defaults to end of file.",
                    },
                },
                "required": ["path"],
            },
        )

    async def run(  # type: ignore[override]
        self,
        path: str,
        start_line: int | None = None,
        end_line: int | None = None,
        **_kwargs,
    ) -> str:
        resolved = (self._base_dir / path).resolve()
        try:
            resolved.relative_to(self._base_dir)
        except ValueError:
            return f"[错误] 路径 '{path}' 超出允许范围 '{self._base_dir}'"

        if not resolved.exists():
            return f"[错误] 文件不存在: {resolved}"
        if not resolved.is_file():
            return f"[错误] 路径不是文件: {resolved}"

        logger.info("ReadFileTool: read %s", resolved)
        try:
            text = resolved.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return f"[错误] 无法读取文件: {exc}"

        if start_line is not None or end_line is not None:
            lines = text.splitlines(keepends=True)
            s = (start_line - 1) if start_line and start_line >= 1 else 0
            e = end_line if end_line else len(lines)
            text = "".join(lines[s:e])

        if len(text) > self._max_chars:
            text = text[: self._max_chars] + "\n\n[内容已截断]"
        return text


# ---------------------------------------------------------------------------
# GlobTool
# ---------------------------------------------------------------------------

class GlobTool(BridgeTool):
    """Find files matching a glob pattern under a base directory.

    Returns a newline-separated list of matching relative paths, sorted
    alphabetically.  Results are capped at ``max_results`` entries.

    Parameters
    ----------
    base_dir :
        Root directory for the search.  Defaults to the current working
        directory.
    max_results :
        Maximum number of paths to return (default 200).
    """

    def __init__(
        self,
        base_dir: Path | str | None = None,
        max_results: int = 200,
    ) -> None:
        self._base_dir = Path(base_dir).resolve() if base_dir else Path.cwd()
        self._max_results = max_results

    @property
    def definition(self) -> ToolParam:
        return ToolParam(
            name="glob",
            description=(
                "Find files matching a glob pattern (e.g. 'src/**/*.py', '*.yaml'). "
                "Returns a sorted, newline-separated list of matching file paths "
                "relative to the project root."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": (
                            "Glob pattern to match.  Supports '**' for recursive "
                            "directory matching.  Example: 'src/**/*.py'."
                        ),
                    }
                },
                "required": ["pattern"],
            },
        )

    async def run(self, pattern: str, **_kwargs) -> str:  # type: ignore[override]
        logger.info("GlobTool: glob '%s' under %s", pattern, self._base_dir)
        try:
            matches = sorted(self._base_dir.glob(pattern))
        except ValueError as exc:
            return f"[错误] 无效的 glob 模式: {exc}"

        paths = [
            str(p.relative_to(self._base_dir))
            for p in matches
            if p.is_file()
        ]

        if not paths:
            return "（无匹配结果）"

        truncated = paths[: self._max_results]
        result = "\n".join(truncated)
        if len(paths) > self._max_results:
            result += f"\n\n[结果已截断，共 {len(paths)} 条，仅展示前 {self._max_results} 条]"
        return result


# ---------------------------------------------------------------------------
# SearchDocsTool
# ---------------------------------------------------------------------------

class SearchDocsTool(BridgeTool):
    """Search a documentation page for the most relevant paragraphs.

    Fetches *url*, splits the page into paragraphs, scores each paragraph
    against the *query* using TF-IDF cosine similarity, and returns the
    top-*k* most relevant paragraphs.  Avoids injecting the entire page into
    the model's context window.

    Parameters
    ----------
    max_chars_per_chunk :
        Maximum characters per returned paragraph chunk (default 600).
    top_k :
        Number of top paragraphs to return (default 5).
    timeout :
        HTTP request timeout in seconds (default 15).
    headers :
        Optional extra HTTP headers for intranet auth.
    """

    def __init__(
        self,
        max_chars_per_chunk: int = 600,
        top_k: int = 5,
        timeout: float = 15.0,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._max_chars_per_chunk = max_chars_per_chunk
        self._top_k = top_k
        self._timeout = timeout
        self._headers = headers or {}

    @property
    def definition(self) -> ToolParam:
        return ToolParam(
            name="search_docs",
            description=(
                "Fetch a documentation URL and return the most relevant paragraphs "
                "for the given query.  Use this instead of fetch_url when you only "
                "need specific information from a long documentation page."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The documentation URL to search.",
                    },
                    "query": {
                        "type": "string",
                        "description": (
                            "Natural-language query describing the information you need.  "
                            "Example: '股票日线收盘价在哪个表'."
                        ),
                    },
                    "top_k": {
                        "type": "integer",
                        "description": f"Number of top paragraphs to return (default {self._top_k}).",
                    },
                },
                "required": ["url", "query"],
            },
        )

    async def run(  # type: ignore[override]
        self,
        url: str,
        query: str,
        top_k: int | None = None,
        **_kwargs,
    ) -> str:
        try:
            import httpx
        except ImportError as exc:
            raise RuntimeError(
                "httpx is required for SearchDocsTool — run: pip install httpx"
            ) from exc

        k = top_k if top_k is not None else self._top_k
        logger.info("SearchDocsTool: GET %s query='%s'", url, query)

        async with httpx.AsyncClient(
            timeout=self._timeout,
            follow_redirects=True,
            headers=self._headers,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()

        text = _html_to_text(response.text)
        paragraphs = _split_paragraphs(text)

        if not paragraphs:
            return "（页面内容为空）"

        scored = _score_paragraphs(paragraphs, query)
        top_paragraphs = [p for _, p in scored[:k]]

        if not top_paragraphs:
            return "（未找到相关段落）"

        header = f"以下是 {url} 中与查询「{query}」最相关的 {len(top_paragraphs)} 个段落：\n\n"
        separator = "\n\n---\n\n"
        chunks = []
        for para in top_paragraphs:
            if len(para) > self._max_chars_per_chunk:
                para = para[: self._max_chars_per_chunk] + "…"
            chunks.append(para)
        return header + separator.join(chunks)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _html_to_text(html: str) -> str:
    """Strip HTML tags and return readable plain text."""
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)
    except ImportError:
        # Fallback: crude tag stripping without beautifulsoup4
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text)
        return text.strip()


def _split_paragraphs(text: str, min_chars: int = 40) -> list[str]:
    """Split *text* into non-trivial paragraphs."""
    raw = re.split(r"\n{2,}", text)
    paragraphs = []
    for chunk in raw:
        chunk = chunk.strip()
        if len(chunk) >= min_chars:
            paragraphs.append(chunk)
    return paragraphs


def _tokenize(text: str) -> list[str]:
    """Lower-case word tokenization: ASCII words + individual CJK characters."""
    tokens: list[str] = []
    for chunk in re.findall(r"[a-zA-Z0-9_]+|[\u4e00-\u9fff]", text):
        tokens.append(chunk.lower())
    return tokens


def _tfidf_scores(
    paragraphs: list[str],
) -> list[dict[str, float]]:
    """Compute TF vectors for each paragraph (IDF weighting applied globally)."""
    tokenized = [_tokenize(p) for p in paragraphs]
    n = len(tokenized)

    # Document frequency
    df: dict[str, int] = {}
    for tokens in tokenized:
        for word in set(tokens):
            df[word] = df.get(word, 0) + 1

    # TF-IDF vectors
    vectors: list[dict[str, float]] = []
    for tokens in tokenized:
        tf: dict[str, float] = {}
        for word in tokens:
            tf[word] = tf.get(word, 0) + 1
        vec: dict[str, float] = {}
        for word, freq in tf.items():
            idf = math.log((n + 1) / (df.get(word, 0) + 1)) + 1
            vec[word] = (freq / len(tokens)) * idf
        vectors.append(vec)
    return vectors


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    """Cosine similarity between two sparse TF-IDF vectors."""
    dot = sum(a.get(w, 0.0) * v for w, v in b.items())
    norm_a = math.sqrt(sum(v * v for v in a.values())) or 1e-9
    norm_b = math.sqrt(sum(v * v for v in b.values())) or 1e-9
    return dot / (norm_a * norm_b)


def _score_paragraphs(
    paragraphs: list[str],
    query: str,
) -> list[tuple[float, str]]:
    """Return paragraphs sorted by relevance to *query* (descending)."""
    query_tokens = _tokenize(query)
    if not query_tokens:
        return [(0.0, p) for p in paragraphs]

    tfidf_vecs = _tfidf_scores(paragraphs)
    n = len(paragraphs)
    df: dict[str, int] = {}
    for vec in tfidf_vecs:
        for word in vec:
            df[word] = df.get(word, 0) + 1

    # Build query vector with same IDF
    query_tf: dict[str, float] = {}
    for word in query_tokens:
        query_tf[word] = query_tf.get(word, 0) + 1
    query_vec: dict[str, float] = {}
    for word, freq in query_tf.items():
        idf = math.log((n + 1) / (df.get(word, 0) + 1)) + 1
        query_vec[word] = (freq / len(query_tokens)) * idf

    scored = [
        (_cosine(vec, query_vec), para)
        for vec, para in zip(tfidf_vecs, paragraphs)
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored
