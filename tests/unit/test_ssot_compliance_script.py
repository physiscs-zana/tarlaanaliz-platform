# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-041: CI compliance gate test coverage.

from pathlib import Path

from scripts.check_ssot_compliance import (
    BOUND_HEADERS,
    has_bound_header,
    has_kr_reference,
    should_check,
)


def test_should_check_targets_repo_critical_paths(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    target = Path("src/module.py")
    target.parent.mkdir(parents=True)
    target.write_text("# KR-041\n# sample", encoding="utf-8")

    assert should_check(target)


def test_should_check_skips_non_target_paths(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    target = Path("alembic/versions/migration.py")
    target.parent.mkdir(parents=True)
    target.write_text("# sample", encoding="utf-8")

    assert not should_check(target)


def test_has_bound_header_detects_valid_header(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    target = Path("scripts/tool.py")
    target.parent.mkdir(parents=True)
    target.write_text(f"# {BOUND_HEADERS[0]}\n# KR-041\nprint('ok')\n", encoding="utf-8")

    assert has_bound_header(target)


def test_has_kr_reference_detects_kr_code(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    target = Path("tests/unit/sample.py")
    target.parent.mkdir(parents=True)
    target.write_text("# KR-041\nprint('ok')\n", encoding="utf-8")

    assert has_kr_reference(target)
