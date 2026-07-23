"""Lazy local-only sentence-transformer adapter."""

from __future__ import annotations

import hashlib
from pathlib import Path


def model_fingerprint(path: Path) -> str:
    resolved = path.resolve()
    if not resolved.is_dir():
        raise FileNotFoundError(f"local semantic model directory not found: {path}")
    manifest = [
        f"{item.relative_to(resolved).as_posix()}:{item.stat().st_size}:{item.stat().st_mtime_ns}"
        for item in sorted(resolved.rglob("*"))
        if item.is_file()
    ]
    return hashlib.sha256("\n".join(manifest).encode("utf-8")).hexdigest()


class LocalSentenceTransformerEmbedder:
    def __init__(self, model_path: Path, model_id: str) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_id = model_id
        self.fingerprint = model_fingerprint(model_path)
        self._model = SentenceTransformer(
            str(model_path.resolve()),
            local_files_only=True,
            trust_remote_code=False,
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(texts, normalize_embeddings=False)
        return [[float(value) for value in vector] for vector in vectors]
