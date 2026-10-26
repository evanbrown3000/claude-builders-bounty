#!/usr/bin/env python3
"""Generate a deterministic, four-section changelog from local Git history."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

SECTIONS = ("Added", "Fixed", "Changed", "Removed")
CONVENTIONAL = re.compile(r"^(\w+)(?:\([^\r\n]*\))?(!)?:\s*(.*)$")


def git(repo, *args):
    result = subprocess.run(["git", "-C", str(repo), *args], text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise ValueError(result.stderr.strip() or "Git command failed")
    return result.stdout.strip()


def categorize(subject):
    match = CONVENTIONAL.match(subject)
    if match:
        kind, breaking, description = match.groups()
        section = {"feat": "Added", "add": "Added", "fix": "Fixed",
                   "remove": "Removed"}.get(kind.lower(), "Changed")
        if breaking:
            description = "**BREAKING** " + description
        return section, description or subject
    word = subject.split(maxsplit=1)[0].lower().rstrip(":") if subject else ""
    section = {"add": "Added", "added": "Added", "fix": "Fixed", "fixed": "Fixed",
               "remove": "Removed", "removed": "Removed", "delete": "Removed"}.get(word, "Changed")
    return section, subject


def escape(text):
    # Commit subjects are untrusted text, not Markdown supplied by the author.
    return re.sub(r"([\\`*_{}\[\]<>])", r"\\\1", text)


def generate(repo):
    git(repo, "rev-parse", "--verify", "HEAD")
    # A shallow clone cannot prove where the last tag is. Never silently emit
    # incomplete release notes; the caller can obtain full history first.
    if git(repo, "rev-parse", "--is-shallow-repository") == "true":
        raise ValueError("Shallow repository: fetch full history and tags before generating notes")
    result = subprocess.run(["git", "-C", str(repo), "describe", "--tags", "--abbrev=0", "HEAD"],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    tag = result.stdout.strip() if result.returncode == 0 else None
    revision = f"{tag}..HEAD" if tag else "HEAD"
    # NUL separates records; the unit separator separates hash and subject.
    history = git(repo, "log", "--reverse", "--format=%H%x1f%s%x00", revision)
    sections = {section: [] for section in SECTIONS}
    for record in history.split("\0"):
        if not record.strip():
            continue
        sha, subject = record.lstrip("\n").split("\x1f", 1)
        section, description = categorize(subject)
        breaking = description.startswith("**BREAKING** ")
        if breaking:
            description = description[len("**BREAKING** "):]
        prefix = "**BREAKING** " if breaking else ""
        sections[section].append(f"- {prefix}{escape(description)} (`{sha[:12]}`)")
    scope = f"after `{escape(tag)}`" if tag else "all reachable commits (no reachable tag)"
    lines = ["# Changelog", "", "## [Unreleased]", "", f"<!-- Scope: {scope}; HEAD {git(repo, 'rev-parse', 'HEAD')} -->", ""]
    for section in SECTIONS:
        lines.extend([f"### {section}", "", *(sections[section] or ["- None."]), ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Git checkout (default: current directory)")
    parser.add_argument("--output", type=Path, default=Path("CHANGELOG.md"), help="Output relative to current directory; '-' for stdout")
    parser.add_argument("--force", action="store_true", help="Replace an existing output file (full replacement, not append)")
    args = parser.parse_args()
    try:
        content = generate(args.repo)
        if str(args.output) == "-":
            print(content, end="")
        else:
            target = args.output.resolve()
            if target.exists() and not args.force:
                raise ValueError(f"Output already exists: {target}; use --force to replace it")
            # Stage completely before publication; exclusive creation protects
            # existing notes even if another process writes after the check.
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(content)
            try:
                if args.force:
                    os.replace(temporary, target)
                else:
                    os.link(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)
            print(f"Wrote {args.output}")
    except (ValueError, OSError) as error:
        print(f"changelog: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
