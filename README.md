# Chad

Agent skills installed for this repo.

## Skills

### `last30days`

An agent-led search engine that researches what people actually said about a topic
in the last 30 days, scored by upvotes, likes, and real money rather than by editors.
It searches Reddit, X, YouTube, TikTok, Hacker News, Polymarket, GitHub, arXiv,
Techmeme, and more in parallel, merges duplicate stories across sources, and
synthesizes one grounded brief.

Installed at `.claude/skills/last30days/`, so any Claude Code session opened in this
repo picks it up automatically.

**Usage**

```
/last30days Peter Steinberger
/last30days OpenClaw vs Hermes vs Paperclip
/last30days what's exploding in AI agents?
```

Or drive the engine directly:

```sh
python3.12 .claude/skills/last30days/scripts/last30days.py "AI coding agents"
python3.12 .claude/skills/last30days/scripts/last30days.py --preflight
```

**Requirements**

- Python 3.12+. The skill resolves an interpreter itself (it prefers `python3.14` /
  `python3.13` / `python3.12` over a bare `python3`, and provisions a managed CPython
  3.12 via `uv` when no system 3.12 exists), so a default `python3` of 3.11 is fine.
- No API keys needed to start. Reddit (with comments), Hacker News, Polymarket, and
  GitHub work immediately. Running the skill once launches a setup wizard that unlocks
  X, YouTube, TikTok, arXiv, Techmeme, and others.

Per-source keys, output locations, watchlists, and the library feed are documented in
the upstream `CONFIGURATION.md`.

## Provenance

`last30days` is vendored from [mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill)
(MIT, see `.claude/skills/last30days/LICENSE`).

| | |
|---|---|
| Version | 3.18.4 |
| Upstream commit | `1004324ad35a3ba656e6df0faabd54749e398455` (2026-08-07) |

The vendored copy is the runtime skill tree (`SKILL.md`, `scripts/`, `references/`,
`agents/`) with upstream's `assets/` directory omitted — those 14 MB of demo images and
audio are README media and are referenced nowhere in the runtime.

To take a newer upstream release, re-vendor the same tree and update the version and
commit above.
