# AGENTS.md — instructions for Codex and other coding agents

This repository is an agent skill for designing indoor cellular signal-booster coverage plans.

**Before doing any design work, read `SKILL.md` in full, then `references/design-rules.md` and
`references/design-file-format.md`.** Follow the workflow in `SKILL.md` step by step and stop for
the user's confirmation after every step.

Setup: `pip install -r requirements.txt` (Python 3.9+, Pillow, PyYAML). For Chinese drawings a CJK
font is needed (Noto Sans CJK, PingFang, Microsoft YaHei …); add its path to `fonts:` in
`config/equipment.yaml` if it is not found.

Quick test: `python scripts/coverage.py report examples/demo-factory/design.json`
→ drawings, CSVs and reports in `examples/demo-factory/output/{zh,en}/`.

Put each new project in its own folder (e.g. `projects/<name>/` with `floorplan.png` and
`design.json`); do not commit client drawings to the public repository.
