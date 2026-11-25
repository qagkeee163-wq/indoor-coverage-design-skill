#!/usr/bin/env python3
"""Indoor signal-booster coverage design tool.

  python scripts/coverage.py areas    DESIGN.json [--lang zh,en]     # step 0: area map with m / ft sizes
  python scripts/coverage.py layout   DESIGN.json [--lang zh,en]     # step 1: antenna layout + coverage circles
  python scripts/coverage.py optimize DESIGN.json [--booster A] [--powers 27,17]  # pick coupler values (writes back)
  python scripts/coverage.py check    DESIGN.json [--lang zh]        # step 2/3: per-antenna budget (every band), feasible
                                                                    # booster window, design-rule lint
  python scripts/coverage.py report   DESIGN.json [--lang zh,en]     # design version: drawings, connection diagram, CSVs, BOM, report
  python scripts/coverage.py report   DESIGN.json --client --lang en # + customer version in output/<lang>/client/
  python scripts/coverage.py connection DESIGN.json [--client]       # connection diagram only

Common option: --config path/to/equipment.yaml   --out output_dir
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from covtool import engine, render, geom, bom as bomm    # noqa: E402
from covtool.connection import render_connection        # noqa: E402
from covtool.lint import lint                           # noqa: E402
from covtool.i18n import T, txt, path_str               # noqa: E402


def floor_ids(d):
    return list(geom.floors(d))


def floor_suffix(d, f, lang):
    return ("_" + render.floor_name(d, f, lang).replace(" ", "_")) if d.get("floors") else ""


def outdir(args, d, lang):
    base = args.out or os.path.join(d["_dir"], "output")
    p = os.path.join(base, lang)
    os.makedirs(p, exist_ok=True)
    return p


def langs(args):
    return [x.strip() for x in args.lang.split(",") if x.strip()]


def print_table(d, cfg, res, lang):
    t = T[lang]
    others = [b for b in engine.bands(d, cfg) if b != engine.ref_band(d, cfg)]
    for b in d["boosters"]:
        ps = engine.all_outputs(res[b["id"]])
        win = engine.feasible_window(res[b["id"]], cfg)
        mdl = f" {b['model']}" if b.get("model") else ""
        print(f"\n{t['booster']} {b['id']}{mdl}  {b['power_dbm']:g} dBm  @ {txt(b.get('location',''), lang)}   "
              f"min {min(ps):.2f} / max {max(ps):.2f} dBm")
        for bd, (lo, hi) in win.items():
            tag = f" @{bd} MHz" if bd is not None else ""
            ok = "OK" if lo < hi else "NONE – no single output fits every antenna"
            print(f"  feasible booster output{tag}: {lo:.2f} < P < {hi:.2f} dBm  ({ok})")
        print("  " + " | ".join(t["cols"]))
        for r in sorted(res[b["id"]], key=lambda r: (len(r["antenna"]), r["antenna"])):
            extra = "  " + "  ".join(f"@{bd}: {r['by_band'][bd]['out_dbm']:.2f}" for bd in others) if others else ""
            print(f"  {r['antenna']:<7} {r['length_m']:6.1f} m  {r['cable_db']:5.2f} dB  {r['device_db']:5.2f} dB  "
                  f"{r['total_db']:5.2f} dB  {r['out_dbm']:6.2f} dBm{extra}   {path_str(r['path'], lang)}")


def write_client(d, cfg, lang, res, o):
    """Customer version in a fixed order: (01 system diagram on the customer's own drawing – made by hand)
    → 02 connection diagram → 03 BOM → 04 plan overview per floor → 05 per-view plans.
    No labels at boosters / antennas / devices, no coverage or arrows, no lengths, no power table."""
    oc = os.path.join(o, "client"); os.makedirs(oc, exist_ok=True)
    f = T[lang]["files"]; zh = lang == "zh"; files = []
    files.append(render_connection(d, cfg, lang, res, os.path.join(oc, "02_" + f["connection"] + ".png"), client=True))
    files.append(os.path.join(oc, "03_" + f["bom"])); bomm.write_bom(d, cfg, lang, files[-1], client=True)
    for fl in floor_ids(d):
        files.append(render.render_client_plan(d, cfg, lang, res, os.path.join(
            oc, "04_" + f["plan"] + floor_suffix(d, fl, lang) + ".png"), floor=fl))
    for i, v in enumerate(d.get("views", []), 1):
        fn = (v.get("file", {}).get(lang) if isinstance(v.get("file"), dict) else v.get("file")) or ("_".join(v["boosters"]))
        files.append(render.render_client_plan(d, cfg, lang, res, os.path.join(oc, f"05_{i:02d}_{fn}.png"), view=v))
    idx = ["# " + txt(d["project"]["name"], lang) + (" – 客户版" if zh else " – customer version"), "",
           ("01 系统图：在客户提供的原图上标注（手工完成，不另画建筑）" if zh else
            "01 System diagram: drawn on the customer's own drawing (by hand; do not redraw the buildings)")]
    idx += [f"{os.path.basename(p)}" for p in files]
    with open(os.path.join(oc, "00_Index.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(idx) + "\n")
    return oc


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["areas", "layout", "optimize", "check", "report", "connection"])
    ap.add_argument("design")
    ap.add_argument("--config")
    ap.add_argument("--lang", default="zh,en")
    ap.add_argument("--out")
    ap.add_argument("--booster", help="optimise only this booster id")
    ap.add_argument("--client", action="store_true",
                    help="also write the customer version (no labels, arrows, coverage, lengths or power tables)")
    ap.add_argument("--powers", help="comma list of candidate booster powers, e.g. 27,17 (default: keep current)")
    args = ap.parse_args()
    cfg = engine.load_config(args.config)
    d = engine.load_design(args.design)

    if args.cmd in ("areas", "layout"):
        fn_ = render.render_areas if args.cmd == "areas" else render.render_layout
        for lang in langs(args):
            for f in floor_ids(d):
                fn = T[lang]["files"][args.cmd] + floor_suffix(d, f, lang) + ".png"
                print("wrote", fn_(d, cfg, lang, os.path.join(outdir(args, d, lang), fn), floor=f))
        return

    if args.cmd == "optimize":
        powers = [float(x) for x in args.powers.split(",")] if args.powers else None
        failed = False
        for b in d["boosters"]:
            if args.booster and b["id"] != args.booster:
                continue
            best = engine.optimise_booster(b, d, cfg, powers)
            if best is None:
                limits = cfg["antenna_output"]
                print(f"Booster {b['id']}: no candidate found within strict range "
                      f"{limits['min_dbm']} < P < {limits['max_dbm']} dBm for every antenna")
                failed = True
                continue
            sc, P, vals = best
            b["power_dbm"] = P; engine.apply_values(b, vals)
            ps = engine.all_outputs(engine.evaluate_booster(b, d, cfg))
            print(f"Booster {b['id']}: {P:g} dBm, couplers {vals} → {min(ps):.2f} ~ {max(ps):.2f} dBm")
        engine.save_design(d)          # keep the boosters that did succeed
        print("saved", d["_path"])
        if failed:
            sys.exit(1)
        return

    try:
        res = engine.evaluate_all(d, cfg)
    except engine.ConfigError as e:
        print("ERROR  ", e); sys.exit(2)
    errs, warns = lint(d, cfg, res)
    if args.cmd == "connection":
        for lang in langs(args):
            o = outdir(args, d, lang); fn = T[lang]["files"]["connection"]
            print("wrote", render_connection(d, cfg, lang, res, os.path.join(o, fn + ".png")))
            if args.client:
                oc = os.path.join(o, "client"); os.makedirs(oc, exist_ok=True)
                print("wrote", render_connection(d, cfg, lang, res, os.path.join(oc, "02_" + fn + ".png"), client=True))
        return
    if args.cmd == "check":
        print_table(d, cfg, res, langs(args)[0])
        print()
        for e in errs:
            print("ERROR  ", e)
        for w in warns:
            print("WARN   ", w)
        print("OK – no errors" if not errs else f"{len(errs)} error(s)")
        sys.exit(1 if errs else 0)

    if errs:
        print("Fix these errors before the report:"); [print("ERROR  ", e) for e in errs]; sys.exit(1)
    for lang in langs(args):
        o = outdir(args, d, lang); f = T[lang]["files"]; imgs = []
        for fl in floor_ids(d):
            imgs.append(os.path.basename(render.render_overview(
                d, cfg, lang, res, os.path.join(o, f["overview"] + floor_suffix(d, fl, lang) + ".png"), floor=fl)))
        for v in d.get("views", []):
            fn = (v.get("file", {}).get(lang) if isinstance(v.get("file"), dict) else v.get("file")) or ("_".join(v["boosters"]))
            imgs.append(os.path.basename(render.render_view(d, cfg, lang, v, res, os.path.join(o, fn + ".png"))))
        if d.get("areas"):
            for fl in floor_ids(d):
                imgs.append(os.path.basename(render.render_areas(
                    d, cfg, lang, os.path.join(o, f["areas"] + floor_suffix(d, fl, lang) + ".png"), floor=fl)))
        imgs.append(os.path.basename(render_connection(d, cfg, lang, res, os.path.join(o, f["connection"] + ".png"))))
        bomm.write_summary(d, cfg, lang, res, os.path.join(o, f["summary"]))
        b = bomm.write_bom(d, cfg, lang, os.path.join(o, f["bom"]))
        bomm.write_report(d, cfg, lang, res, b, imgs, warns if lang == "zh" else [], os.path.join(o, f["report"]))
        print(f"[{lang}] wrote {len(imgs)} drawings + CSVs + report in {o}")
        if args.client:
            print(f"[{lang}] customer version:", write_client(d, cfg, lang, res, o))
    for w in warns:
        print("WARN   ", w)


if __name__ == "__main__":
    main()
