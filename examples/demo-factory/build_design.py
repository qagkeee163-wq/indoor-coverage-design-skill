"""Builds design.json for the fictional demo factory (run from the repo root or this folder)."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))
from covtool.build import coupler, splitter, row   # noqa: E402

ants = []
for i, x in enumerate([1000, 1250, 1500]):
    ants += [{"id": f"P{i+1}", "pos": [x, 200], "area": "PROD"}, {"id": f"P{i+4}", "pos": [x, 500], "area": "PROD"},
             {"id": f"O{i+1}", "pos": [x, 800], "area": "OFF"}]
for i, x in enumerate([700, 450, 200]):
    ants += [{"id": f"W{i+1}", "pos": [x, 250], "area": "WH"}, {"id": f"W{i+4}", "pos": [x, 750], "area": "WH"}]

# Booster A: coupler at the IDF -> coupled east to the office row, through north to a 1:2 splitter between production rows
prod = splitter("S1", (900, 350), [
    ([(900, 350), (930, 350), (930, 260), (1000, 260)], row(["P1", "P2", "P3"], [1000, 1250, 1500], 260, 200)),
    ([(900, 350), (930, 350), (930, 440), (1000, 440)], row(["P4", "P5", "P6"], [1000, 1250, 1500], 440, 500))])
treeA = coupler("cA0", (890, 860), [(890, 860), (1000, 860)], row(["O1", "O2", "O3"], [1000, 1250, 1500], 860, 800),
                [(890, 860), (890, 350), (900, 350)], prod)
# Booster B: 1:2 splitter on the shared wall, one output per warehouse row
treeB = splitter("S2", (840, 500), [
    ([(840, 500), (810, 500), (810, 310), (700, 310)], row(["W1", "W2", "W3"], [700, 450, 200], 310, 250)),
    ([(840, 500), (810, 500), (810, 690), (700, 690)], row(["W4", "W5", "W6"], [700, 450, 200], 690, 750))])

loc = {"en": "IDF (office, SW corner)", "zh": "IDF 弱电间（办公区西南角）"}
d = {
    "project": {"name": {"en": "Demo Factory", "zh": "示例工厂"}, "floorplan": "floorplan.png", "m_per_px": 0.06, "overview_width": 2400},
    "areas": [{"id": "WH", "name": {"en": "Warehouse", "zh": "仓库"}, "rect": [50, 50, 850, 950]},
              {"id": "PROD", "name": {"en": "Production", "zh": "生产区"}, "rect": [850, 50, 1650, 650]},
              {"id": "OFF", "name": {"en": "Office", "zh": "办公区"}, "rect": [850, 650, 1650, 950]}],
    "idf": [[870, 900]],
    "antennas": ants,
    "boosters": [
        {"id": "A", "power_dbm": 27, "pos": [890, 900], "donor": [880, 945], "label_side": "R", "location": loc,
         "area": {"en": "Production + Office", "zh": "生产区 + 办公区"}, "feed": [[890, 900], [890, 860]], "tree": treeA},
        {"id": "B", "power_dbm": 27, "pos": [860, 900], "donor": [840, 945], "label_side": "L", "location": loc,
         "area": {"en": "Warehouse", "zh": "仓库"}, "feed": [[860, 900], [860, 500], [840, 500]], "tree": treeB}],
    "views": [
        {"title": {"en": "Production + Office (Booster A, 9 antennas)", "zh": "生产区 + 办公区（主机 A，9 支天线）"},
         "boosters": ["A"], "crop": [800, 100, 1640, 960], "file": {"en": "Production_Office", "zh": "生产区_办公区"}},
        {"title": {"en": "Warehouse (Booster B, 6 antennas)", "zh": "仓库（主机 B，6 支天线）"}, "boosters": ["B"],
         "crop": [60, 120, 940, 960], "file": {"en": "Warehouse", "zh": "仓库"},
         "notes": [{"en": "Booster B shares the IDF with Booster A; its cable enters the warehouse through the shared wall.",
                    "zh": "主机 B 与主机 A 同在 IDF；线缆穿共用墙进入仓库。"}]}]}
json.dump(d, open(os.path.join(HERE, "design.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote design.json – next: python scripts/coverage.py optimize examples/demo-factory/design.json")
