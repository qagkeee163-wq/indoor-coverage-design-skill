---
name: indoor-coverage-design
description: Design an indoor cellular signal-booster (DAS) coverage plan from a floor plan — areas, ceiling antennas, booster/IDF placement, coupler/splitter cabling, per-antenna link budget, drawings and bill of materials in Chinese and English. Use when the user gives a building/factory floor plan or area and asks for a signal coverage / booster installation design, 信号覆盖方案, 室分方案, or 主机/天线/耦合器/功分器 layout.
---

# Indoor signal-booster coverage design

You design a passive indoor distribution system for a cellular signal booster: one or more boosters,
each with **one** output cable that is split by couplers / splitters into ceiling antennas, plus a
donor antenna on the roof. The deliverable is a set of drawings (Chinese + English), a per-antenna
link-budget table and a bill of materials.

Speak to the user in the language they use (often Chinese). **Everything that goes to the end
client is produced in English as well** (the client may be foreign) — the tool renders both.

Read before starting:
- `references/design-rules.md` — the rules. Every rule there is a correction a senior engineer made
  during a real project. Treat them as hard requirements.
- `references/design-file-format.md` — how to write `design.json`.
- `config/equipment.yaml` — equipment and limits (cable loss, booster powers, coupler / splitter losses,
  antenna output window). If the user mentions different equipment, edit this file first.

Tool (Python 3.9+, `pip install -r requirements.txt`):

```
python scripts/coverage.py areas    DESIGN.json            # step 0 image: areas with m and ft
python scripts/coverage.py layout   DESIGN.json            # step 1 image: antennas + coverage circles
python scripts/coverage.py optimize DESIGN.json            # pick coupler values (writes back into DESIGN.json)
python scripts/coverage.py check    DESIGN.json --lang zh  # per-antenna budget + design-rule lint
python scripts/coverage.py report   DESIGN.json            # final drawings, CSVs, BOM, report in zh/ and en/
```

Worked example: `examples/demo-factory/` (fictional). Copy its structure for a new project.

## Workflow — stop for the user's confirmation after every step

Do one step, show the result (image + short table), ask "确认 / 要调整哪里？", and only continue
when the user confirms. If anything is unclear, ask **before** doing the step. Large sites are done
**area by area**: design one area, get it confirmed, then the next.

### Step 0 — Intake and areas
1. Collect (ask for anything missing, in one message):
   - floor plan (PDF/PNG) and one known dimension to set the scale (`m_per_px`);
   - priority areas (e.g. circled in red) — everything else still needs coverage;
   - direction / distance of the base station (sets donor-antenna facing);
   - IDF / telecom rooms (often red squares on drawings), ceiling height (riser length),
     areas that need no antennas (electrical rooms, storage);
   - any changes to equipment (`config/equipment.yaml`).
2. Convert the plan to PNG (e.g. `pdftoppm -r 150 -png`), set up `project/`, `idf`, and divide the
   building **along walls** into rectangles in `areas`.
3. Run `areas`; show the image with each area's size in **m and ft** and area in m² and ft².

### Step 1 — Antennas (count, position, type)
- Default to **ceiling antennas only** for commercial / professionally installed jobs.
- Rule of thumb: ~300 m² or R ≈ 10 m each, 3–5 m through a wall (config `ceiling_antenna`).
- Keep the count reasonable — too many makes boosters hard to fit and raises the client's price
  expectations. Open/empty spaces get **edge coverage**, not full coverage; circles should not spill
  far outside exterior walls. Small rooms / storage can be covered by neighbours' edge antennas.
- Spread antennas evenly; leave room so cables to neighbouring antennas don't crowd together.
- Write `antennas` (id, pos, area), run `layout`, show counts per area. Expect the user to move,
  merge or delete antennas; apply and re-render until confirmed.

### Step 2 — Booster positions, routing, couplers / splitters, losses
For each area (or merged group of areas):
1. **Booster position** (see rules §2): IDF first; if no IDF nearby or the IDF is so far that an
   antenna would fall below 0 dBm, mount on a wall near the load. Never in the middle of a room
   without an IDF there. The donor antenna does **not** decide booster position.
2. **Booster count**: as few as possible; share a booster with a neighbouring small area instead of
   adding one. One booster per ~6–13 antennas is typical with 27 dBm.
3. **Routing tree**: one cable leaves the booster; split only where cables actually diverge.
   Splitter for branches of similar length; coupler when one branch is much longer (far side gets the
   through port). Couplers directly feeding an antenna are aligned with it. No duplicated / parallel /
   back-tracking runs. Build the tree in `boosters[].tree` (see format doc).
4. Run `optimize` (picks 5/8/10 dB values) then `check`. Fix every ERROR. Treat every WARN as
   something the user will spot — fix it or explain it.
5. Show the area drawing (`report` renders views) **and** the per-antenna table: cable length,
   cable loss, device loss, output (dBm). All antennas must be within the configured window
   (default 0–8 dBm).
6. After **any** change (moved booster, new route, swapped device) re-run `optimize`/`check` and show
   the new per-antenna outputs — the user expects this every time.

Booster power: choose from the configured list (default 27/17/15/12 dBm single port). Prefer the
lowest power that keeps every antenna ≥ 0 dBm, but the user may also ask to merge two small boosters
into one bigger one. `optimize --powers 27,17,15,12` tries several.

### Step 3 — Margins and booster gain (only when the user asks to continue)
From the original method: add margins (end 2–3 dB + antenna 4–6 dB = 8–10 dB), then derive required
booster gain from outdoor signal (RSRP at the donor), donor cable loss and target antenna output.
You need from the user: outdoor RSRP, their gain formula, and the model list. **Ask; don't invent.**

### Step 4 — Final deliverables
1. `report` → `output/zh/` and `output/en/`:
   overview, one drawing per view, areas map, per-antenna CSV, bill of materials CSV, report.md.
2. Check the images yourself (open them): labels readable, no lines on top of each other, legend
   quantities right, every booster/donor labelled. English version must contain **no Chinese**.
3. BOM: boosters by power, couplers by dB, splitters by ratio, ceiling + donor antennas, cable split
   into indoor / donor / total / order quantity (+15 %), in m and ft, N connectors, plus per-booster
   breakdown and the assumptions (riser, slack, ceiling height to confirm on site).
4. Deliver both language folders. Summarise in chat: boosters, antennas, output range, cable total.

## Conventions the drawings must follow
See `references/design-rules.md` §5. In short: booster = coloured box (colour by power, 27 red,
17 gold), donor = green triangle "N↑" with dashed line, antenna = purple dot, LMR400 = orange line;
coupler = bar on the input side + short stub toward the coupled port ("──┘"), colour by dB
(5 green, 8 blue, 10 black); splitter = rectangle, single input on one long side and parallel
outputs on the opposite long side, colour by ratio (1:2 light blue, 1:3 yellow, 1:4 pink); legend
shows the quantity of each device.

## When the tool is not enough
The JSON + CLI cover the standard cases. For an unusual layout you may edit drawings by hand or extend
`scripts/covtool/`, but keep the link-budget math identical:
`output = booster − device losses − length × loss/100 m`, length = right-angle routing + riser +
slack per antenna.
