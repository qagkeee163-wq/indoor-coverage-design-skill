# design.json format

All coordinates are **pixels of the floor-plan PNG** (`[x, y]`, y downward).
`project.m_per_px` converts pixels to metres. Text fields can be a string or `{"en": "...", "zh": "..."}`.
See `examples/demo-factory/design.json` for a complete file.

```jsonc
{
  "project": {
    "name": {"en": "Demo Factory", "zh": "示例工厂"},
    "floorplan": "floorplan.png",        // relative to design.json
    "m_per_px": 0.06,                     // from a known dimension: metres / pixels
    "overview_width": 2400                // optional, px of the overview plan
  },
  "areas": [                              // step 0 – rectangles along walls
    {"id": "WH", "name": {"en": "Warehouse", "zh": "仓库"}, "rect": [x0, y0, x1, y1]}
  ],
  "idf": [[870, 900]],                    // IDF / telecom rooms
  "antennas": [                           // step 1
    {"id": "W1", "pos": [700, 250], "area": "WH"}
  ],
  "boosters": [                           // step 2
    {
      "id": "B", "power_dbm": 27,
      "pos": [860, 900],                  // booster (on a wall / in the IDF)
      "donor": [840, 945],                // donor antenna on the roof corner
      "location": {"en": "IDF (office)", "zh": "IDF 弱电间"},
      "area": {"en": "Warehouse", "zh": "仓库"},
      "location_reason": "optional – required if not in an IDF while one exists",
      "label_side": "L",                  // booster label left (L) or right (R); "label_dy": px offset
      "feed": [[860, 900], [860, 500], [840, 500]],   // booster -> first device; ends at tree.pos
      "tree": { ...node... }
    }
  ],
  "views": [                              // one drawing per view (crop of the plan)
    {"title": {"en": "...", "zh": "..."}, "boosters": ["B"], "crop": [x0, y0, x1, y1],
     "file": {"en": "Warehouse", "zh": "仓库"}, "notes": [{"en": "...", "zh": "..."}]}
  ]
}
```

## Multi-floor, panels, bands, models (v2)

See `examples/demo-hotel/design.json` (2 floors, panels, Europe 5D profile).

```jsonc
{
  "project": {"name": "...", "region": "europe",
              "bands": [800, 1800],          // every band is checked; loss per band comes from the config
              "design_band": 1800},          // optional: band shown in single-value tables (default: highest loss)
  "floors": [                                // replaces project.floorplan / m_per_px
    {"id": "B", "name": {"en": "Basement", "zh": "地下室"}, "floorplan": "basement.png", "m_per_px": 0.03, "elevation_m": 0},
    {"id": "G", "name": {"en": "Ground floor", "zh": "首层"}, "floorplan": "ground.png", "m_per_px": 0.03, "elevation_m": 3.0}],
  "areas":    [{"id": "SPA", "floor": "B", "rect": [...]}],
  "idf":      [{"floor": "B", "pos": [700, 660]}],
  "antennas": [{"id": "B1", "floor": "B", "pos": [230, 330]},
               {"id": "G1", "floor": "G", "pos": [30, 250], "type": "panel",
                "aim_deg": 90,                 // 0 = up/north, 90 = right/east, 180 = down, 270 = left
                "range_m": 18, "half_width_m": 5}],
  "boosters": [{"id": "M1", "floor": "B", "model": "Hi23-6S-PLUS CE", "power_dbm": 23,
                "power_by_band": {"800": 20, "1800": 20},   // only after the user confirmed per-band output
                "per_band_confirmed": true,
                "donor_cable_m": 25,                         // optional: confirmed donor route length
                "feed": [...], "tree": {...}}],
  "views": [{"floor": "G", "boosters": ["M1"], "panel_arrows": false, ...}]
}
```

- **Floor change inside a path**: a point `[x, y, "G"]` moves the cable to floor G. The vertical length
  is `|elevation(G) − elevation(previous floor)|`; the x/y jump between the two plans is only alignment and
  is not counted. Drawings mark the riser "→ Ground floor" / "from Basement".
- Nodes have no floor field: a device is on the floor where its incoming path ends. `check` reports an
  error when a cable reaches an antenna on a different floor than `antennas[].floor`.
- **Panel antennas**: the last short segment of the feeder must travel in the aim direction (fed from behind).
- **Extra cable to burn power**: on a branch, `"extra_m": 4, "extra_approved": true`. Without
  `extra_approved` it is an error – show the user the extra length, loss and new output first.
- **Model checks** (when the config has `booster_models`): the model must support every project band;
  `power_dbm` ≤ model max; for a `total` power model and more than one band, `power_by_band` and
  `per_band_confirmed` are required — never split the total evenly on your own.
- Cable loss per band: `cable.loss_db_per_100m` in the config may be a table `{band: dB/100 m}`; an empty
  value stops the calculation with a request for the datasheet value.

## Nodes

```jsonc
{"type": "antenna", "id": "W1"}                         // position comes from antennas[]

{"type": "coupler", "id": "cW1", "pos": [700, 310],
 "value": 8,            // 5 / 8 / 10, or null → filled in by `optimize`
 "lock": false,         // true = optimize keeps this value
 "coupled": {"path": [[700, 310], [700, 250]], "node": {...}},   // weaker port, goes off at 90°
 "through": {"path": [[700, 310], [450, 310]], "node": {...}}}   // continues straight on

{"type": "splitter", "id": "S2", "pos": [840, 500],
 "orient": "v",         // optional; auto from the output direction
 "outputs": [           // 2, 3 or 4 outputs → 1:2 / 1:3 / 1:4
   {"path": [[840, 500], [810, 500], [810, 310], [700, 310]], "node": {...}},
   {"path": [[840, 500], [810, 500], [810, 690], [700, 690]], "node": {...}}]}
```

Path rules (checked by `check`):
- every `path` starts at its device's `pos` and ends at the child's position;
- a step between two points that differ in both x and y is drawn / measured horizontal-first;
- splitter: all outputs leave in the same direction (first hop), the input arrives from the opposite
  side; the first hop of each output is drawn as its own parallel lane;
- coupler: `through` continues in the direction the input arrived; `coupled` leaves at 90°;
- a coupler whose coupled port feeds an antenna shares x or y with that antenna;
- no two cables of the same booster on the same line for > 2 m (duplicated run).

## Tips for building trees

A row of antennas fed from one end is a chain of couplers on a cable line parallel to the row
(offset a few metres), each coupled port going straight to its antenna, the last antenna on the
final through port. Use the helpers in `scripts/covtool/build.py` (`row`, `coupler`, `splitter`); `examples/demo-factory/build_design.py` shows a complete build.
Two parallel rows fed from the middle → a 1:2 splitter between the rows, one output per row.
