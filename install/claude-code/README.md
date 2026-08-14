# Publication Figure Design — Claude Code Installation

The Claude Code skill is at `publication-figure-design/`. Install via symlink:

```bash
ln -s $(pwd)/publication-figure-design ~/.claude/skills/publication-figure-design
```

Or copy:
```bash
cp -r publication-figure-design ~/.claude/skills/publication-figure-design
```

After installation, Claude Code auto-triggers on: "make a volcano plot", "画个热图",
"review this figure for Nature", etc.

The skill checks `publication-figure-design/assets/figures/<type>/` for production scripts before
generating any code. Add your own scripts there to extend figure type coverage.

Generated: 2026-08-14 11:31 UTC
