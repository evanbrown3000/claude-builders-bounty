# Claude Builders Bounty 🤖

> A community bounty board for Claude Code builders.

Building with Claude Code? Have tasks to delegate?
Want to get paid for contributing to AI projects?
You're in the right place.

---

## How it works

**To post a bounty**
1. Open a GitHub issue with a clear description and acceptance criteria
2. Comment `/opire create $XXX` in the issue to set the reward
3. Share the link — contributors will find it

**To claim a bounty**
1. Browse the open issues below
2. Comment `/opire try` in the issue you want to work on
3. Submit a PR — payment is automatic on merge ✅

---

## Active Bounties

| # | Task | Amount | Status |
|---|------|--------|--------|
| [#1](../../issues/1) | SKILL: Generate a CHANGELOG from git history | $50 | 🟢 Open |
| [#2](../../issues/2) | TEMPLATE: CLAUDE.md for a Next.js + SQLite project | $75 | 🟢 Open |
| [#3](../../issues/3) | HOOK: Block destructive bash commands in Claude Code | $100 | 🟢 Open |
| [#4](../../issues/4) | AGENT: PR reviewer with structured Markdown output | $150 | 🟢 Open |
| [#5](../../issues/5) | WORKFLOW: n8n + Claude API — automated weekly dev summary | $200 | 🟢 Open |

---

## Rules

- Tasks must be related to Claude Code or AI tooling
- Every issue must have clear acceptance criteria before a bounty is activated
- Payment is handled by [Opire](https://opire.dev) (Stripe)
- Quality over speed — a solid PR beats a fast one

---

## Community

- 🐦 X: [@ClaudeBounty](https://x.com/ClaudeBounty)
- 📧 Contact: claudebounty@gmail.com

---

*Started by the Claude builder community · March 2026 · MIT License*

## Generate a changelog (bounty #1)

Requires Git, Bash, and Python 3.8+; no Python packages, API keys, or network access.

1. Clone this repository (or copy `changelog.sh` and `scripts/generate_changelog.py` together).
2. In a Git checkout with full history and tags, run `bash /path/to/changelog.sh`.
3. Review the resulting `CHANGELOG.md` before publishing it.

Optional usage:

```bash
# Read another checkout; output is relative to the invoking directory.
bash changelog.sh --repo /path/to/project --output release-notes.md
# Preview without writing a file.
bash changelog.sh --repo /path/to/project --output -
# Explicitly replace existing notes (not an append operation).
bash changelog.sh --force
```

The default range is the nearest reachable tag (`git describe --tags --abbrev=0`)
through HEAD, excluding the tagged commit. Both annotated and lightweight tags
are supported. If no tag is reachable, all reachable commits are included.
An empty repository and a shallow checkout fail with a diagnostic rather than
silently producing incomplete notes. If needed, obtain the full history and tags
before running the generator; it never fetches anything itself.

Conventional `feat:`/`feat(scope):` commits become **Added**, `fix:` becomes
**Fixed**, and `remove:` becomes **Removed**. Other types become **Changed**.
A `!` before the colon marks the entry as breaking. Ordinary subjects beginning
with Add/Added, Fix/Fixed, or Remove/Removed/Delete are classified similarly;
other subjects are Changed. This is a deterministic heuristic, not semantic
analysis: review entries (especially reverts) before publishing. Subjects are
escaped as Markdown text and retain a 12-character commit reference. All four
sections are emitted, including explicit empty sections.

Existing output is protected unless `--force` is supplied. Generation finishes
before the output is published; errors go to stderr with nonzero exit status.

### Verification and real-repository sample

```bash
python3 -m unittest discover -s tests -v
bash -n changelog.sh
bash changelog.sh --output examples/CHANGELOG.sample.md
```

[`examples/CHANGELOG.sample.md`](examples/CHANGELOG.sample.md) was actually generated
from this repository at `1aeae2adc82d33f971fd7731644348dcdd24b5a6` (no reachable tags).
It is not fabricated fixture output. Tests create isolated Git repositories and
cover tagged/untagged histories, category mapping, Unicode/Markdown subjects,
unrelated tags, no-new-commit output, empty/shallow checkouts, and overwrite safety.
