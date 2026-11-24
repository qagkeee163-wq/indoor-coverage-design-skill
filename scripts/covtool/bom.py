"""Bill of materials + CSV / Markdown reports."""
import csv
import math
from collections import Counter

from . import geom
from .engine import device_counts, all_branches, count_antennas, node_floors, bands, ref_band, branches
from .i18n import T, txt, path_str, loss_str

FT = 3.28084

L = {
    "en": dict(cols=["Item", "Spec", "Qty", "Unit", "Notes"], booster="Booster (single output port)", ceiling="Indoor ceiling antenna",
               donor="Donor antenna", donor_n="1 per booster, facing the base station", coupler="Coupler", splitter="Splitter",
               indoor="cable – indoor distribution", donor_c="cable – donor (booster → roof)", total="cable – total (estimate)",
               order="cable – suggested order", extra="of which approved extra length", conn="N-type connector", pcs="pcs", m="m",
               margin="+{p:.0f}% margin", conn_n="2 per segment ({s} indoor segments + {d} donor runs)",
               per="Per-booster breakdown", pcols=["Booster", "Output", "Antennas", "Devices", "Indoor cable (m)", "Donor cable (m)"],
               assum="Assumptions",
               a=["Right-angle routing measured on the drawing.",
                  "{riser} m riser from each booster to the ceiling; {slack} m slack per antenna.",
                  "Donor cable = right-angle distance booster → roof corner + {riser} m riser + {roof} m through the roof.",
                  "Ceiling height is assumed; confirm on site."],
               sum_cols=["Area", "Booster", "Booster output", "Booster location", "Antenna", "Cable length (m)", "Cable loss (dB)",
                         "Device loss (dB)", "Total loss (dB)", "Antenna output (dBm)", "Path (devices passed)"]),
    "zh": dict(cols=["项目", "规格", "数量", "单位", "备注"], booster="主机（单口）", ceiling="吸顶天线", donor="施主天线",
               donor_n="每台主机 1 支，朝向基站", coupler="耦合器", splitter="功分器", indoor="线缆 – 室内分布线",
               donor_c="线缆 – 施主线（主机 → 屋顶）", total="线缆 – 合计（估算）", order="线缆 – 建议采购", extra="其中经确认的加长段", conn="N 型接头",
               pcs="个", m="m", margin="含 {p:.0f}% 余量", conn_n="每段线 2 个（室内 {s} 段 + 施主线 {d} 段）",
               per="按主机拆分", pcols=["主机", "功率", "天线数", "器件", "室内线 (m)", "施主线 (m)"], assum="估算前提",
               a=["按图纸直角走线量取。", "每台主机到吊顶 {riser} m 竖线；每支天线 {slack} m 余量。",
                  "施主线 = 主机到屋顶角的直角距离 + {riser} m 竖线 + {roof} m 穿屋顶。", "吊顶高度为假设值，需现场确认。"],
               sum_cols=["区域", "主机", "主机功率", "主机位置", "天线", "线长 (m)", "线损 (dB)", "器件损耗 (dB)", "总损耗 (dB)",
                         "天线口功率 (dBm)", "经过的器件"]),
}


def compute_bom(d, cfg):
    """Unique physical segments: the feed and every branch once, vertical rises and approved extra included."""
    c = cfg["cable"]
    rows, tot = [], Counter()
    for b in d["boosters"]:
        nf = node_floors(b, d)
        f0 = geom.obj_floor(b, d)
        feedL, _ = geom.path_length_m(b["feed"], f0, d)
        L = feedL; rise = sum(r["length_m"] for r in geom.split_path(b["feed"], f0, d)[1]); extra = 0.0; nseg = 1

        def walk(n):
            nonlocal L, rise, extra, nseg
            for _, br in branches(n):
                bl, _ = geom.path_length_m(br["path"], nf[id(n)], d)
                rise += sum(r["length_m"] for r in geom.split_path(br["path"], nf[id(n)], d)[1])
                e = float(br.get("extra_m", 0) or 0)
                L += bl + e; extra += e; nseg += 1
                walk(br["node"])
        walk(b["tree"])
        n_ant = count_antennas(b["tree"])
        indoor = c["riser_m"] + L + n_ant * c["slack_per_antenna_m"]
        if b.get("donor_cable_m") is not None:
            donor = float(b["donor_cable_m"])
        elif b.get("donor"):
            k = float(geom.floors(d)[f0]["m_per_px"])
            donor = (abs(b["pos"][0] - b["donor"][0]) + abs(b["pos"][1] - b["donor"][1])) * k + c["riser_m"] + c["donor_roof_m"]
        else:
            donor = 0.0
        dev = device_counts(b["tree"])
        rows.append(dict(id=b["id"], P=b["power_dbm"], model=b.get("model", ""), n_ant=n_ant, dev=dev, indoor=indoor,
                         donor=donor, nseg=nseg, rise=rise, extra=extra))
        tot += dev; tot["indoor"] += indoor; tot["donor"] += donor; tot["seg"] += nseg; tot["ant"] += n_ant
        tot["rise"] += rise; tot["extra"] += extra
        tot[("booster", b["power_dbm"], b.get("model", ""))] += 1
    return rows, tot


def dev_str(dev, lang):
    parts = []
    for (kind, v), n in sorted(dev.items(), key=lambda x: (x[0][0] != "splitter", x[0][1])):
        parts.append(f"1:{v}×{n}" if kind == "splitter" else f"{v}dB×{n}")
    return ", ".join(parts) or "—"


def write_bom(d, cfg, lang, out):
    l = L[lang]; c = cfg["cable"]
    rows, tot = compute_bom(d, cfg)
    total = tot["indoor"] + tot["donor"]; order = math.ceil(total * (1 + c["order_margin"]) / 10) * 10
    with open(out, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh); w.writerow(l["cols"])
        for P, M in sorted({(r["P"], r["model"]) for r in rows}, key=lambda x: (-x[0], x[1])):
            ids = ", ".join(r["id"] for r in rows if r["P"] == P and r["model"] == M)
            w.writerow([l["booster"], f"{M + ' ' if M else ''}{P:g} dBm", tot[("booster", P, M)], l["pcs"], ids])
        kinds = Counter(a.get("type", "ceiling") for a in d.get("antennas", []))
        w.writerow([l["ceiling"], "", kinds.get("ceiling", 0), l["pcs"], ""])
        if kinds.get("panel"):
            w.writerow([T[lang]["panel"], "", kinds["panel"], l["pcs"], ""])
        w.writerow([l["donor"], "", len(rows), l["pcs"], l["donor_n"]])
        for v in sorted(cfg["couplers"]):
            w.writerow([l["coupler"], f"{v} dB", tot.get(("coupler", v), 0), l["pcs"], ""])
        for v in sorted(cfg["splitters"]):
            w.writerow([l["splitter"], f"1:{v}", tot.get(("splitter", v), 0), l["pcs"], ""])
        nm = c["name"]
        w.writerow([f"{nm} {l['indoor']}", loss_str(cfg, bands(d, cfg)), round(tot["indoor"], 1), l["m"], f"≈ {tot['indoor']*FT:,.0f} ft"])
        if tot["rise"]:
            w.writerow([f"  {T[lang]['rise']}", "", round(tot["rise"], 1), l["m"], ""])
        if tot["extra"]:
            w.writerow([f"  {l['extra']}", "", round(tot["extra"], 1), l["m"], ""])
        w.writerow([f"{nm} {l['donor_c']}", "", round(tot["donor"]), l["m"], f"≈ {tot['donor']*FT:,.0f} ft"])
        w.writerow([f"{nm} {l['total']}", "", round(total), l["m"], f"≈ {total*FT:,.0f} ft"])
        w.writerow([f"{nm} {l['order']}", "", order, l["m"], f"≈ {order*FT:,.0f} ft, " + l["margin"].format(p=c["order_margin"] * 100)])
        nconn = c["connectors_per_segment"] * (tot["seg"] + len(rows))
        w.writerow([l["conn"], "", nconn, l["pcs"], l["conn_n"].format(s=tot["seg"], d=len(rows))])
        w.writerow([]); w.writerow([l["per"]]); w.writerow(l["pcols"])
        for r in rows:
            w.writerow([r["id"], f"{r['model'] + ' ' if r['model'] else ''}{r['P']:g} dBm", r["n_ant"], dev_str(r["dev"], lang), round(r["indoor"]), round(r["donor"])])
        w.writerow([]); w.writerow([l["assum"]])
        for a in l["a"]:
            w.writerow([a.format(riser=c["riser_m"], slack=c["slack_per_antenna_m"], roof=c["donor_roof_m"])])
    return rows, tot, order


def write_summary(d, cfg, lang, results, out):
    l = L[lang]; t = T[lang]
    bl = bands(d, cfg); rb = ref_band(d, cfg); others = [b for b in bl if b != rb]
    head = list(l["sum_cols"])
    if rb is not None:
        head[6] += f" @{rb}"; head[8] += f" @{rb}"; head[9] += f" @{rb}"
    head = head[:10] + [f"{t['cols'][5]} @{b}" for b in others] + [t["floor"]] + head[10:]
    with open(out, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh); w.writerow(head)
        for b in d["boosters"]:
            for r in sorted(results[b["id"]], key=lambda r: (len(r["antenna"]), r["antenna"])):
                w.writerow([txt(b.get("area", ""), lang), f"{t['booster']} {b['id']}",
                            f"{(b.get('model') + ' ') if b.get('model') else ''}{b['power_dbm']:g} dBm",
                            txt(b.get("location", ""), lang), r["antenna"], round(r["length_m"], 1), round(r["cable_db"], 2),
                            round(r["device_db"], 2), round(r["total_db"], 2), round(r["out_dbm"], 2)]
                           + [round(r["by_band"][x]["out_dbm"], 2) for x in others]
                           + [r["floor"] if r["floor"] != geom.SINGLE else "", path_str(r["path"], lang)])


def write_report(d, cfg, lang, results, bom, images, warns, out):
    rows, tot, order = bom; t = T[lang]; zh = lang == "zh"
    total = tot["indoor"] + tot["donor"]
    s = [f"# {txt(d['project']['name'], lang)} – " + ("室内信号覆盖方案" if zh else "Indoor Signal Coverage Design"), ""]
    s += [("## 主机一览" if zh else "## Boosters"), "",
          "| " + " | ".join(t["bcols"]) + " |", "|" + "---|" * len(t["bcols"])]
    for b in d["boosters"]:
        ps = [v["out_dbm"] for r in results[b["id"]] for v in r["by_band"].values()]
        s.append(f"| {t['booster']} {b['id']} | {txt(b.get('location',''), lang)} | {(b.get('model') + ' ') if b.get('model') else ''}{b['power_dbm']:g} dBm | "
                 f"{len(results[b['id']])} | {min(ps):.2f} ~ {max(ps):.2f} dBm |")
    s += ["", ("## 每支天线输出功率" if zh else "## Per-antenna output"), ""]
    s += ["| " + " | ".join(t["cols"]) + " |", "|" + "---|" * len(t["cols"])]
    for b in d["boosters"]:
        for r in sorted(results[b["id"]], key=lambda r: (len(r["antenna"]), r["antenna"])):
            s.append(f"| {r['antenna']} | {r['length_m']:.0f} m | {r['cable_db']:.1f} dB | {r['device_db']:.1f} dB | {r['total_db']:.1f} dB | "
                     f"{r['out_dbm']:.2f} dBm | {path_str(r['path'], lang)} |")
    s += ["", ("## 材料清单" if zh else "## Bill of materials"), ""]
    for P, M in sorted({(r["P"], r["model"]) for r in rows}, key=lambda x: (-x[0], x[1])):
        s.append(f"- {t['booster']} {M + ' ' if M else ''}{P:g} dBm: {tot[('booster', P, M)]}")
    kinds = Counter(a.get("type", "ceiling") for a in d.get("antennas", []))
    s.append(f"- {t['antenna']}: {kinds.get('ceiling', 0)};  " + (f"{t['panel']}: {kinds['panel']};  " if kinds.get("panel") else "")
             + f"{t['donor']}: {len(rows)}")
    s.append(("- 耦合器：" if zh else "- Couplers: ") + ", ".join(f"{v} dB × {tot.get(('coupler', v), 0)}" for v in sorted(cfg["couplers"])))
    s.append(("- 功分器：" if zh else "- Splitters: ") + ", ".join(f"1:{v} × {tot.get(('splitter', v), 0)}" for v in sorted(cfg["splitters"])))
    s.append(f"- {cfg['cable']['name']}: " + (f"室内 {tot['indoor']:.0f} m + 施主线 {tot['donor']:.0f} m = {total:.0f} m（≈{total*FT:,.0f} ft），建议采购 {order} m"
                                             if zh else f"indoor {tot['indoor']:.0f} m + donor {tot['donor']:.0f} m = {total:.0f} m (≈{total*FT:,.0f} ft); order {order} m"))
    s += ["", ("## 图纸" if zh else "## Drawings"), ""] + [f"- {i}" for i in images]
    if warns:
        s += ["", ("## 设计检查提示（内部）" if zh else "## Design-check warnings (internal)"), ""] + [f"- {w}" for w in warns]
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(s) + "\n")
