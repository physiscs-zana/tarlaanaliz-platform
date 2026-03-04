# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-041: SDLC gate automation for compliance verification.

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

BOUND_HEADER = "BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated."
CHECKABLE_SUFFIXES = {
    ".py",
    ".md",
    ".yml",
    ".yaml",
    ".sh",
    ".txt",
    ".json",
}
KR_CHECK_SUFFIXES = {".py", ".md", ".yml", ".yaml", ".sh", ".txt"}
ALLOWED_ROOTS = {"src", "tests", "scripts", ".github"}


def git_changed_files(base_ref: str, head_ref: str) -> list[Path]:
    result = subprocess.run(
        ["git", "diff", "--name-only", base_ref, head_ref],
        check=True,
        capture_output=True,
        text=True,
    )
    return [Path(line.strip()) for line in result.stdout.splitlines() if line.strip()]


def git_numstat(base_ref: str, head_ref: str) -> tuple[int, int, int]:
    result = subprocess.run(
        ["git", "diff", "--numstat", base_ref, head_ref],
        check=True,
        capture_output=True,
        text=True,
    )
    files = 0
    added_total = 0
    deleted_total = 0
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        # Only count files within ALLOWED_ROOTS for batch sizing.
        # This prevents large merge commits that touch alembic/, config/,
        # docker-compose.yml, etc. from spuriously failing the batch check.
        file_path = Path(parts[2].strip())
        if not file_path.parts or file_path.parts[0] not in ALLOWED_ROOTS:
            continue
        files += 1
        added = 0 if parts[0] == "-" else int(parts[0])
        deleted = 0 if parts[1] == "-" else int(parts[1])
        added_total += added
        deleted_total += deleted
    return files, added_total, deleted_total


def should_check(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    if path.suffix.lower() not in CHECKABLE_SUFFIXES:
        return False

    repo_relative = path
    if path.is_absolute():
        try:
            repo_relative = path.resolve().relative_to(Path.cwd().resolve())
        except ValueError:
            return False

    return repo_relative.parts[0] in ALLOWED_ROOTS


def has_bound_header(path: Path) -> bool:
    top_lines = path.read_text(encoding="utf-8").splitlines()[:5]
    return any(header in line for line in top_lines for header in BOUND_HEADERS)


def has_kr_reference(path: Path) -> bool:
    if path.suffix.lower() not in KR_CHECK_SUFFIXES:
        return True
    top_lines = path.read_text(encoding="utf-8").splitlines()[:40]
    return any("KR-" in line for line in top_lines)


def validate_batch_size(base_ref: str, head_ref: str) -> tuple[bool, str]:
    file_count, added, deleted = git_numstat(base_ref=base_ref, head_ref=head_ref)
    changed_lines = added + deleted

    if changed_lines <= 120:
        max_files = 15
    elif changed_lines <= 300:
        max_files = 10
    else:
        max_files = 25

    if file_count > max_files:
        return (
            False,
            f"Adaptive batch check failed: files={file_count}, changed_lines={changed_lines}, limit={max_files}",
        )

    return True, f"Adaptive batch check passed: files={file_count}, changed_lines={changed_lines}, limit={max_files}"


def run(base_ref: str, head_ref: str) -> int:
    batch_ok, batch_message = validate_batch_size(base_ref=base_ref, head_ref=head_ref)
    print(batch_message)
    if not batch_ok:
        return 1

    changed = git_changed_files(base_ref=base_ref, head_ref=head_ref)
    check_targets = [path for path in changed if should_check(path)]

    if not check_targets:
        print("No compliance-target files changed.")
        return 0

    missing_header: list[Path] = []
    missing_kr_reference: list[Path] = []

    for path in check_targets:
        if not has_bound_header(path):
            missing_header.append(path)
        if not has_kr_reference(path):
            missing_kr_reference.append(path)

    if missing_header:
        print("SSOT compliance check failed: missing BOUND header")
        for path in missing_header:
            print(f" - {path}")
        return 1

    if missing_kr_reference:
        print("SSOT compliance check failed: missing KR reference in header block")
        for path in missing_kr_reference:
            print(f" - {path}")
        return 1

    print("SSOT compliance check passed.")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate SSOT compliance headers in changed files.")
    parser.add_argument("--base", default="HEAD~1", help="Git base reference for diff")
    parser.add_argument("--head", default="HEAD", help="Git head reference for diff")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    raise SystemExit(run(base_ref=args.base, head_ref=args.head))
