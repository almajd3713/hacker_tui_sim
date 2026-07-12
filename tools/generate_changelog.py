from __future__ import annotations

import argparse
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CommitEntry:
    sha: str
    subject: str


SECTION_RULES = [
    ("Features", re.compile(r"^(feat)(\(.+\))?:\s+", re.IGNORECASE)),
    ("Fixes", re.compile(r"^(fix)(\(.+\))?:\s+", re.IGNORECASE)),
    ("Docs", re.compile(r"^(docs)(\(.+\))?:\s+", re.IGNORECASE)),
    ("Refactors", re.compile(r"^(refactor)(\(.+\))?:\s+", re.IGNORECASE)),
    ("Performance", re.compile(r"^(perf)(\(.+\))?:\s+", re.IGNORECASE)),
    ("Build", re.compile(r"^(build)(\(.+\))?:\s+", re.IGNORECASE)),
    ("CI", re.compile(r"^(ci)(\(.+\))?:\s+", re.IGNORECASE)),
    ("Tests", re.compile(r"^(test)(\(.+\))?:\s+", re.IGNORECASE)),
    ("Chores", re.compile(r"^(chore)(\(.+\))?:\s+", re.IGNORECASE)),
]


def run_git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def git_lines(*args: str) -> list[str]:
    output = run_git(*args)
    return [line for line in output.splitlines() if line.strip()]


def normalize_tag(tag: str) -> str:
    return tag[1:] if tag.startswith("v") else tag


def find_previous_tag(tag: str) -> str | None:
    tags = git_lines("tag", "--list", "--sort=-version:refname")
    if not tags:
        return None
    if tag in tags:
        index = tags.index(tag)
        return tags[index + 1] if index + 1 < len(tags) else None
    return tags[0]


def known_tags() -> list[str]:
    return git_lines("tag", "--list", "--sort=-version:refname")


def collect_commits(tag: str, previous_tag: str | None) -> list[CommitEntry]:
    revision_range = f"{previous_tag}..{tag}" if previous_tag else tag
    lines = git_lines("log", "--pretty=format:%H%x09%s", revision_range)
    commits: list[CommitEntry] = []
    for line in lines:
        sha, _, subject = line.partition("\t")
        commits.append(CommitEntry(sha=sha, subject=subject.strip()))
    return commits


def classify_commit(subject: str) -> str:
    for section, pattern in SECTION_RULES:
        if pattern.match(subject):
            return section
    return "Other"


def clean_subject(subject: str) -> str:
    for _, pattern in SECTION_RULES:
        if pattern.match(subject):
            return pattern.sub("", subject).strip()
    return subject.strip()


def build_release_notes(tag: str, previous_tag: str | None, commits: list[CommitEntry], repo_url: str | None) -> str:
    grouped: dict[str, list[CommitEntry]] = defaultdict(list)
    for commit in commits:
        grouped[classify_commit(commit.subject)].append(commit)

    version = normalize_tag(tag)
    compare_url = None
    is_named_tag = tag in known_tags()
    if repo_url:
        if previous_tag:
            compare_url = f"{repo_url}/compare/{previous_tag}...{tag if is_named_tag else 'HEAD'}"
        elif is_named_tag:
            compare_url = f"{repo_url}/releases/tag/{tag}"

    lines = [f"# {version}", ""]
    if compare_url:
        lines.append(f"[Full diff]({compare_url})")
        lines.append("")

    if not commits:
        lines.append("- No user-facing changes recorded in git history for this release.")
        lines.append("")
        return "\n".join(lines)

    ordered_sections = [section for section, _ in SECTION_RULES] + ["Other"]
    for section in ordered_sections:
        entries = grouped.get(section, [])
        if not entries:
            continue
        lines.append(f"## {section}")
        lines.append("")
        for entry in entries:
            short_sha = entry.sha[:7]
            subject = clean_subject(entry.subject)
            lines.append(f"- {subject} (`{short_sha}`)")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def update_changelog(changelog_path: Path, release_notes: str) -> None:
    existing = changelog_path.read_text(encoding="utf-8") if changelog_path.exists() else "# Changelog\n\n"
    header = "# Changelog\n\n"
    body = existing[len(header) :] if existing.startswith(header) else existing
    changelog_path.write_text(f"{header}{release_notes}\n{body.lstrip()}", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate release notes from git history.")
    parser.add_argument("--tag", required=True, help="Release tag, for example v0.1.0")
    parser.add_argument("--previous-tag", help="Previous release tag. Auto-detected if omitted.")
    parser.add_argument("--repo-url", help="Repository URL used for compare links.")
    parser.add_argument("--output", default="release-notes.md", help="Output markdown path.")
    parser.add_argument("--update-changelog", action="store_true", help="Prepend generated notes to CHANGELOG.md.")
    parser.add_argument("--changelog-path", default="CHANGELOG.md", help="Changelog path to update.")
    args = parser.parse_args()

    previous_tag = args.previous_tag or find_previous_tag(args.tag)
    commits = collect_commits(args.tag, previous_tag)
    notes = build_release_notes(args.tag, previous_tag, commits, args.repo_url)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(notes, encoding="utf-8")

    if args.update_changelog:
        update_changelog(Path(args.changelog_path), notes)


if __name__ == "__main__":
    main()
