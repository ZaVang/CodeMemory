from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from codememory.capture import append_capture
from codememory.profile import init_personal_profile, validate_personal_profile


def test_non_git_profile_is_valid_and_delivery_is_unavailable(tmp_path: Path):
    result = init_personal_profile(tmp_path)

    assert result.profile_valid is True
    assert result.git_delivery.status == "unavailable"
    assert result.git_delivery.reason == "not_git_repo"
    assert result.profile is not None
    assert result.profile.maintenance.auto_commit is False
    assert result.profile.maintenance.auto_push is False
    assert not (tmp_path / ".git").exists()


def test_init_preserves_existing_readme_and_profile(tmp_path: Path):
    tmp_path.joinpath("README.md").write_text("owner text\n", encoding="utf-8")
    first = init_personal_profile(tmp_path, owner="alice")
    second = init_personal_profile(tmp_path, owner="bob", auto_commit=True)

    assert first.profile_valid and second.profile_valid
    assert tmp_path.joinpath("README.md").read_text(encoding="utf-8") == "owner text\n"
    raw = yaml.safe_load(tmp_path.joinpath(".codememory/profile.yaml").read_text(encoding="utf-8"))
    assert raw["owner"] == "alice"
    assert raw["maintenance"]["auto_commit"] is False


def test_git_repo_without_remote_does_not_invalidate_profile(tmp_path: Path):
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    result = init_personal_profile(tmp_path)

    assert result.profile_valid is True
    assert result.git_delivery.status == "unavailable"
    assert result.git_delivery.reason == "remote_missing"
    assert append_capture(tmp_path, "capture still works").id.startswith("cap_")


def test_tracked_private_local_is_validation_error(tmp_path: Path):
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    init_personal_profile(tmp_path)
    secret = tmp_path / "private-local" / "secret.txt"
    secret.write_text("local only", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "-f", "private-local/secret.txt"],
        check=True,
        capture_output=True,
    )

    result = validate_personal_profile(tmp_path)

    assert result.profile_valid is False
    assert any("already tracked" in error for error in result.errors)


def test_custom_private_local_rule_is_validated_and_init_repairs_it(tmp_path: Path):
    init_personal_profile(tmp_path)
    profile_path = tmp_path / ".codememory" / "profile.yaml"
    raw = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    raw["paths"]["private_local"] = "secret-local"
    profile_path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    (tmp_path / "secret-local").mkdir()

    before = validate_personal_profile(tmp_path)
    assert before.profile_valid is False
    assert any("secret-local/" in error for error in before.errors)

    repaired = init_personal_profile(tmp_path)
    ignores = (tmp_path / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert repaired.profile_valid is True
    assert "secret-local/" in ignores

    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    secret = tmp_path / "secret-local" / "secret.txt"
    secret.write_text("local only", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "-f", "secret-local/secret.txt"],
        check=True,
        capture_output=True,
    )
    tracked = validate_personal_profile(tmp_path)
    assert tracked.profile_valid is False
    assert any("secret-local" in error and "already tracked" in error for error in tracked.errors)
