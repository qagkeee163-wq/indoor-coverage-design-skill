# AGENTS.md — instructions for Codex and other coding agents

This repository is an agent skill for designing indoor cellular signal-booster coverage plans.

Read `SKILL.md` and the relevant design references before working on a coverage plan. Follow its stage order and reuse already confirmed decisions.

Setup: `pip install -r requirements.txt` (Python 3.9+, Pillow, PyYAML). For Chinese drawings a CJK
font is needed (Noto Sans CJK, PingFang, Microsoft YaHei …); add its path to `fonts:` in
`config/equipment.yaml` if it is not found.

Quick test: `python scripts/coverage.py report examples/demo-factory/design.json`
→ drawings, CSVs and reports in `examples/demo-factory/output/{zh,en}/`.

Put each new project in its own folder (e.g. `projects/<name>/` with `floorplan.png` and
`design.json`); do not commit client drawings to the public repository.
