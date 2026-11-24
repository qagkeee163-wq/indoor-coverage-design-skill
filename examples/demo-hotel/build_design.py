"""Fictional 2-floor hotel: Europe 5D profile, basement ceiling antennas, ground-floor panels, one booster."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))
from covtool.build import ant, coupler, splitter   # noqa: E402

ants = [
    {"id": "B1", "pos": [230, 330], "floor": "B", "area": "SPA"},
    {"id": "B2", "pos": [600, 330], "floor": "B", "area": "MEET"},
    {"id": "B3", "pos": [980, 330], "floor": "B", "area": "GYM"},
    {"id": "G1", "pos": [30, 250], "floor": "G", "area": "LOBBY", "type": "panel", "aim_deg": 90, "range_m": 18, "half_width_m": 5},
    {"id": "G2", "pos": [600, 30], "floor": "G", "area": "LOBBY", "type": "panel", "aim_deg": 180, "range_m": 12, "half_width_m": 5},
    {"id": "G3", "pos": [1170, 250], "floor": "G", "area": "REST", "type": "panel", "aim_deg": 270, "range_m": 18, "half_width_m": 5},
]
# basement 1:3 splitter fed from the coupled port; outputs leave north, one lane each
basement = splitter("S1", (600, 420), [
    ([(600, 420), (600, 400), (230, 400), (230, 330)], ant("B1")),
    ([(600, 420), (600, 330)], ant("B2")),
    ([(600, 420), (600, 400), (980, 400), (980, 330)], ant("B3"))])
# ground floor 1:3 splitter; panels are fed from behind (last hop in the aim direction)
ground = splitter("S2", (700, 400), [
    ([(700, 400), (700, 380), (10, 380), (10, 250), (30, 250)], ant("G1")),
    ([(700, 400), (700, 10), (600, 10), (600, 30)], ant("G2")),
    ([(700, 400), (700, 380), (1190, 380), (1190, 250), (1170, 250)], ant("G3"))])
# coupler at the booster: through → riser to the ground floor (far side), coupled → basement
tree = coupler("C0", (620, 600),
               [(620, 600), (620, 500), (600, 500), (600, 420)], basement,
               [(620, 600), (560, 600), (560, 580, "G"), (700, 580), (700, 400)], ground)

d = {
    "project": {"name": {"en": "Demo Hotel", "zh": "示例酒店"}, "region": "europe", "bands": [1800],
                "overview_width": 2400},
    "floors": [
        {"id": "B", "name": {"en": "Basement", "zh": "地下室"}, "floorplan": "basement.png", "m_per_px": 0.03, "elevation_m": 0},
        {"id": "G", "name": {"en": "Ground floor", "zh": "首层"}, "floorplan": "ground.png", "m_per_px": 0.03, "elevation_m": 3.0}],
    "areas": [
        {"id": "SPA", "floor": "B", "name": {"en": "SPA", "zh": "SPA"}, "rect": [0, 0, 400, 700]},
        {"id": "MEET", "floor": "B", "name": {"en": "Meeting", "zh": "会议室"}, "rect": [400, 0, 820, 500]},
        {"id": "GYM", "floor": "B", "name": {"en": "Gym", "zh": "健身房"}, "rect": [820, 0, 1200, 700]},
        {"id": "LOBBY", "floor": "G", "name": {"en": "Lobby", "zh": "大堂"}, "rect": [0, 0, 600, 470]},
        {"id": "REST", "floor": "G", "name": {"en": "Restaurant", "zh": "餐厅"}, "rect": [600, 0, 1200, 470]}],
    "idf": [{"floor": "B", "pos": [700, 660]}],
    "antennas": ants,
    "boosters": [{
        "id": "M1", "floor": "B", "model": "Hi23-6S-PLUS CE", "power_dbm": 23, "pos": [700, 640], "donor_cable_m": 25,
        "label_side": "R", "location": {"en": "IDF (basement, service room)", "zh": "IDF 弱电间（地下室后勤区）"},
        "area": {"en": "Basement + ground floor", "zh": "地下室 + 首层"},
        "feed": [[700, 640], [700, 600], [620, 600]], "tree": tree}],
    "views": [
        {"title": {"en": "Basement (Booster M1)", "zh": "地下室（主机 M1）"}, "floor": "B", "boosters": ["M1"],
         "file": {"en": "Basement", "zh": "地下室"}},
        {"title": {"en": "Ground floor (from Booster M1)", "zh": "首层（主机 M1 供线）"}, "floor": "G", "boosters": ["M1"],
         "file": {"en": "Ground_floor", "zh": "首层"}, "panel_arrows": False,
         "notes": [{"en": "The feeder rises 3.0 m from the basement next to the stair; the vertical run is included in the lengths.",
                    "zh": "馈线在楼梯旁从地下室上升 3.0 m，过层长度已计入。"}]}]}
json.dump(d, open(os.path.join(HERE, "design.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote design.json")
