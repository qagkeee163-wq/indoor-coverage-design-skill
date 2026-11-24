#!/usr/bin/env python3
"""Regression tests. Run: python tests/run_tests.py   (add --update to rewrite the golden files)

The golden files hold every antenna's length/loss/output for the examples. Any other
implementation of the engine (e.g. the web tool) must reproduce them to 0.01 dB.
"""
import copy
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from covtool import engine            # noqa: E402
from covtool.lint import lint         # noqa: E402

CASES = [("demo-factory", "config/equipment.yaml"), ("demo-hotel", "config/regions/europe-5d.yaml")]
FAILS = []


def check(name, cond, msg=""):
    print(("ok    " if cond else "FAIL  ") + name + (f"  ({msg})" if msg and not cond else ""))
    if not cond:
        FAILS.append(name)


def snapshot(res):
    return {bid: [{"antenna": r["antenna"], "length_m": round(r["length_m"], 3), "device_db": round(r["device_db"], 3),
                   "by_band": {str(b): {"cable_db": round(v["cable_db"], 3), "out_dbm": round(v["out_dbm"], 3)}
                               for b, v in r["by_band"].items()}}
                  for r in sorted(rs, key=lambda r: r["antenna"])] for bid, rs in res.items()}


def golden(update):
    for ex, cfgp in CASES:
        cfg = engine.load_config(os.path.join(ROOT, cfgp))
        d = engine.load_design(os.path.join(ROOT, "examples", ex, "design.json"))
        snap = snapshot(engine.evaluate_all(d, cfg))
        gp = os.path.join(ROOT, "tests", "golden", ex + ".json")
        if update or not os.path.exists(gp):
            json.dump({"config": cfgp, "design": f"examples/{ex}/design.json", "results": snap}, open(gp, "w"), indent=1)
            print("wrote", gp)
            continue
        ref = json.load(open(gp))["results"]
        worst = 0.0
        for bid, rows in ref.items():
            for a, b in zip(rows, snap[bid]):
                for band, v in a["by_band"].items():
                    worst = max(worst, abs(v["out_dbm"] - b["by_band"][band]["out_dbm"]))
                worst = max(worst, abs(a["length_m"] - b["length_m"]))
        check(f"golden {ex}", worst < 0.01, f"max diff {worst}")


def rules():
    cfg = engine.load_config(os.path.join(ROOT, "config/regions/europe-5d.yaml"))
    base = engine.load_design(os.path.join(ROOT, "examples/demo-hotel/design.json"))

    # 1. unknown per-band loss → stop and ask
    d = copy.deepcopy(base); d["project"]["bands"] = [800, 1800]
    try:
        engine.evaluate_all(d, cfg); ok = False
    except engine.ConfigError as e:
        ok = "800" in str(e)
    check("missing 5D loss at 800 MHz raises ConfigError", ok)

    # 2. multi-band with a 'total' power model and no per-band confirmation → error
    c2 = copy.deepcopy(cfg); c2["cable"]["loss_db_per_100m"][800] = 20.0
    res = engine.evaluate_all(d, c2)
    errs, _ = lint(d, c2, res)
    check("total DL power not split by itself", any("TOTAL DL output" in e for e in errs))
    d["boosters"][0]["power_by_band"] = {"800": 20, "1800": 20}; d["boosters"][0]["per_band_confirmed"] = True
    res = engine.evaluate_all(d, c2)
    errs, _ = lint(d, c2, res)
    check("confirmed per-band output accepted", not any("TOTAL DL output" in e for e in errs))
    check("every band is evaluated", set(res["M1"][0]["by_band"]) == {800, 1800})

    # 3. band not supported by the model
    d3 = copy.deepcopy(base); d3["project"]["bands"] = [700, 1800]; d3["boosters"][0]["model"] = "Hi23-5S-PLUS CE"
    c3 = copy.deepcopy(cfg); c3["cable"]["loss_db_per_100m"][700] = 18.0
    errs, _ = lint(d3, c3, engine.evaluate_all(d3, c3))
    check("model without 700 MHz is rejected", any("does not support" in e for e in errs))

    # 4. extra cable to burn power needs approval
    d4 = copy.deepcopy(base)
    d4["boosters"][0]["tree"]["coupled"]["node"]["outputs"][1]["extra_m"] = 4
    res = engine.evaluate_all(d4, cfg)
    errs, _ = lint(d4, cfg, res)
    check("unapproved extra cable is an error", any("not approved" in e for e in errs))
    b2 = [r for r in res["M1"] if r["antenna"] == "B2"][0]
    b2_ref = [r for r in engine.evaluate_all(base, cfg)["M1"] if r["antenna"] == "B2"][0]
    check("extra length is counted in loss", abs(b2["length_m"] - b2_ref["length_m"] - 4) < 1e-9)
    d4["boosters"][0]["tree"]["coupled"]["node"]["outputs"][1]["extra_approved"] = True
    errs, _ = lint(d4, cfg, engine.evaluate_all(d4, cfg))
    check("approved extra cable accepted", not any("not approved" in e for e in errs))

    # 5. strict window on unrounded values + near-limit warning
    c5 = copy.deepcopy(cfg)
    res = engine.evaluate_all(base, c5)
    lo = min(engine.all_outputs(res["M1"]))
    d5 = copy.deepcopy(base); d5["boosters"][0]["power_dbm"] = 23 - lo + 1e-4   # min antenna ≈ 0.0001 dBm
    errs, warns = lint(d5, c5, engine.evaluate_all(d5, c5))
    check("0.0001 dBm passes the strict window", not any("outside strict range" in e for e in errs))
    check("near-limit warning raised", any("close to the limit" in w for w in warns))
    d5["boosters"][0]["power_dbm"] = 23 - lo
    errs, _ = lint(d5, c5, engine.evaluate_all(d5, c5))
    check("exactly 0 dBm fails (strict)", any("outside strict range" in e for e in errs))

    # 6. vertical run counted once per path, floors respected
    r = {x["antenna"]: x for x in engine.evaluate_all(base, cfg)["M1"]}
    check("rise between floors adds elevation difference", r["G2"]["floor"] == "G" and r["B2"]["floor"] == "B")

    # 7. wrong floor at antenna
    d7 = copy.deepcopy(base); d7["antennas"][0]["floor"] = "G"
    errs, _ = lint(d7, cfg, engine.evaluate_all(d7, cfg))
    check("antenna on another floor than its cable is an error", any("reaches antenna B1 on floor B" in e for e in errs))

    # 8. panel fed from the front → warning
    d8 = copy.deepcopy(base)
    g1 = d8["boosters"][0]["tree"]["through"]["node"]["outputs"][0]
    g1["path"] = [[700, 400], [700, 380], [60, 380], [60, 250], [30, 250]]
    _, warns = lint(d8, cfg, engine.evaluate_all(d8, cfg))
    check("panel must be fed from behind", any("panel G1" in w for w in warns))

    # 9. feasible window formula
    win = engine.feasible_window(engine.evaluate_all(base, cfg)["M1"], cfg)[1800]
    Ls = [x["total_db"] for x in engine.evaluate_all(base, cfg)["M1"]]
    check("feasible window = (max L + min, min L + max)", abs(win[0] - max(Ls)) < 1e-9 and abs(win[1] - min(Ls) - 8) < 1e-9)


def cli():
    import shutil, tempfile
    tmp = tempfile.mkdtemp()
    d = json.load(open(os.path.join(ROOT, "examples/demo-factory/design.json")))
    d["project"]["floorplan"] = os.path.join(ROOT, "examples/demo-factory/floorplan.png")
    for b in d["boosters"]:
        for c in engine.couplers_of(b["tree"]):
            c["value"] = None
    br = d["boosters"][1]["tree"]["outputs"][0]          # booster B: add 200 m → impossible at 27 dBm
    br["extra_m"] = 200; br["extra_approved"] = True
    p = os.path.join(tmp, "partial.json"); json.dump(d, open(p, "w"))
    out = subprocess.run([sys.executable, os.path.join(ROOT, "scripts/coverage.py"), "optimize", p, "--powers", "27"],
                         capture_output=True, text=True)
    saved = json.load(open(p))
    check("optimize exits with error when a booster fails", out.returncode == 1, out.stdout)
    check("optimize still saves the boosters that succeeded",
          all(c.get("value") for c in engine.couplers_of(saved["boosters"][0]["tree"])), out.stdout + out.stderr)
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    golden("--update" in sys.argv)
    rules()
    cli()
    print(f"\n{len(FAILS)} failure(s)" if FAILS else "\nall tests passed")
    sys.exit(1 if FAILS else 0)
