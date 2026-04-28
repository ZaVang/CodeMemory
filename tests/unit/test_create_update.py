"""Integration tests for create.py and update.py using temp directories.

Tests use pytest's tmp_path fixture for isolation — no real memory data touched.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from codememory.create import create
from codememory.update import update
from codememory.core import compute_body_hash, parse_frontmatter
from codememory.index import load_index


# ==================================================================
# 3.1 create atom
# ==================================================================

def test_create_atom_file_generated(tmp_path: Path):
    """create atom produces a .md file with correct YAML frontmatter fields."""
    filepath = create(tmp_path, "atom", "user/ideas/my-thesis", intensity=5,
                       tags=["research", "ai"])

    assert filepath is not None
    assert filepath.exists()
    assert filepath.suffix == ".md"

    meta, body = parse_frontmatter(filepath)
    assert meta["type"] == "atom"
    assert meta["id"] == "user/ideas/my-thesis"
    assert meta["intensity"] == 5
    assert meta["tags"] == ["research", "ai"]
    assert meta["status"] == "active"
    assert meta["version"] == 1
    assert "summary_hash" in meta
    assert "created" in meta
    assert "updated" in meta


def test_create_auto_reindex(tmp_path: Path):
    """create auto-reindexes, so the new memory appears in the index."""
    create(tmp_path, "atom", "user/test/reindex-check")
    idx = load_index(tmp_path)
    assert "user/test/reindex-check" in idx.memories
    entry = idx.memories["user/test/reindex-check"]
    assert entry.type == "atom"


# ==================================================================
# 3.2 create --dry-run
# ==================================================================

def test_create_dry_run_no_file(tmp_path: Path):
    """dry_run=True does not create a file on disk."""
    result = create(tmp_path, "atom", "user/test/dry-run", dry_run=True)
    assert result is None

    expected = tmp_path / "user" / "test" / "dry-run.md"
    assert not expected.exists()


# ==================================================================
# 3.3 create intensity >= 8 → protected
# ==================================================================

def test_create_protected_high_intensity(tmp_path: Path):
    """intensity >= 8 automatically marks protected: true."""
    filepath = create(tmp_path, "atom", "user/test/protected",
                       intensity=8)
    assert filepath is not None
    meta, _body = parse_frontmatter(filepath)
    assert meta.get("protected") is True


def test_create_not_protected_low_intensity(tmp_path: Path):
    """intensity < 8 does not set protected."""
    filepath = create(tmp_path, "atom", "user/test/normal",
                       intensity=5)
    meta, _body = parse_frontmatter(filepath)
    assert meta.get("protected") is not True


# ==================================================================
# 3.4 update version increment
# ==================================================================

def test_update_version_incremented(tmp_path: Path):
    """update increments version by 1."""
    create(tmp_path, "atom", "user/test/version-check")
    filepath = update(tmp_path, "user/test/version-check",
                       change_note="First update",
                       summary="Updated summary")
    assert filepath is not None

    meta, _body = parse_frontmatter(filepath)
    assert meta["version"] == 2


def test_update_version_twice(tmp_path: Path):
    """Two updates give version 3."""
    create(tmp_path, "atom", "user/test/version-twice")
    update(tmp_path, "user/test/version-twice",
           change_note="Update 1", summary="S1")
    update(tmp_path, "user/test/version-twice",
           change_note="Update 2", summary="S2")
    meta, _body = parse_frontmatter(
        tmp_path / "user" / "test" / "version-twice.md"
    )
    assert meta["version"] == 3


# ==================================================================
# 3.5 update change_log
# ==================================================================

def test_update_change_log_appended(tmp_path: Path):
    """update appends to change_log with version, date, and note."""
    create(tmp_path, "atom", "user/test/changelog-check")
    filepath = update(tmp_path, "user/test/changelog-check",
                       change_note="Added new content",
                       summary="New summary")

    meta, _body = parse_frontmatter(filepath)
    changelog = meta.get("change_log", [])
    assert isinstance(changelog, list)
    assert len(changelog) >= 1
    latest = changelog[0]
    assert latest["version"] == 2
    assert "date" in latest
    assert latest["note"] == "Added new content"


def test_update_change_log_multiple_entries(tmp_path: Path):
    """Multiple updates produce multiple change_log entries."""
    create(tmp_path, "atom", "user/test/changelog-multi")
    update(tmp_path, "user/test/changelog-multi",
           change_note="First change", summary="S1")
    update(tmp_path, "user/test/changelog-multi",
           change_note="Second change", summary="S2")

    meta, _body = parse_frontmatter(
        tmp_path / "user" / "test" / "changelog-multi.md"
    )
    changelog = meta.get("change_log", [])
    assert len(changelog) >= 2
    # Most recent entry first (inserted at position 0)
    assert changelog[0]["note"] == "Second change"
    assert changelog[1]["note"] == "First change"


# ==================================================================
# 3.6 update summary_hash
# ==================================================================

def test_update_summary_hash_with_summary(tmp_path: Path):
    """Passing --summary updates summary_hash to match new body hash."""
    create(tmp_path, "atom", "user/test/hash-update")

    new_body = "## New Content\n\nThis is fresh body text for testing."
    new_summary = "Fresh summary."

    result = update(tmp_path, "user/test/hash-update",
                    change_note="Update both",
                    body=new_body, summary=new_summary)
    assert result is not None

    meta, _body = parse_frontmatter(result)
    expected_hash = compute_body_hash(new_body.strip())
    assert meta.get("summary_hash") == expected_hash


def test_update_summary_hash_unchanged_without_summary(tmp_path: Path):
    """Updating body without --summary keeps old summary_hash (stale trigger)."""
    create(tmp_path, "atom", "user/test/hash-unchanged")

    # Get initial hash
    filepath = tmp_path / "user" / "test" / "hash-unchanged.md"
    initial_meta, _ = parse_frontmatter(filepath)
    initial_hash = initial_meta.get("summary_hash")

    # Update body only — no summary
    update(tmp_path, "user/test/hash-unchanged",
           change_note="Body only",
           body="## Updated Body\n\nDifferent content now.")

    meta, body = parse_frontmatter(filepath)
    # summary_hash should be unchanged (old hash)
    assert meta.get("summary_hash") == initial_hash
    # But body has changed, so hash would NOT match
    actual_hash = compute_body_hash(body)
    assert actual_hash != initial_hash


# ==================================================================
# 3.7 update --status
# ==================================================================

def test_update_status_archived(tmp_path: Path):
    """Passing --status archived changes the memory status."""
    create(tmp_path, "atom", "user/test/status-change")
    result = update(tmp_path, "user/test/status-change",
                    change_note="Archive this",
                    status="archived")
    assert result is not None

    meta, _body = parse_frontmatter(result)
    assert meta["status"] == "archived"
