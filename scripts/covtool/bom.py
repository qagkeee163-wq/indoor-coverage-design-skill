"""Bill of materials + CSV / Markdown reports."""
import csv
import math
from collections import Counter

from .engine import device_counts, all_segments, manhattan, count_antennas
from .i18n import T, txt, path_str

FT = 3.28084

L = {
    "en": dict(cols=["Item", "Spec", "Qty", "Unit", "Notes"], booster="Booster (single output port)", ceiling="Indoor ceiling antenna",
               donor="Donor antenna", donor_n="1 per booster, facing the base station", coupler="Coupler", splitter="Splitter",
               indoor="cable – indoor distribution", donor_c="cable – donor (booster → roof)", total="cable – total (estimate)",
               order="cable – suggested order", conn="N-type connector", pcs="pcs", m="m",
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
               donor_c="线缆 – 施主线（主机 → 屋顶）", total="线缆 – 合计（估算）", order="线缆 – 建议采购", conn="N 型接头",
               pcs="个", m="m", margin="含 {p:.0f}% 余量", conn_n="每段线 2 个（室内 {s} 段 + 施主线 {d} 段）",
               per="按主机拆分", pcols=["主机", "功率", "天线数", "器件", "室内线 (m)", "施主线 (m)"], assum="估算前提",
               a=["按图纸直角走线量取。", "每台主机到吊顶 {riser} m 竖线；每支天线 {slack} m 余量。",
                  "施主线 = 主机到屋顶角的直角距离 + {riser} m 竖线 + {roof} m 穿屋顶。", "吊顶高度为假设值，需现场确认。"],
               sum_cols=["区域", "主机", "主机功率", "主机位置", "天线", "线长 (m)", "线损 (dB)", "器件损耗 (dB)", "总损耗 (dB)",
                         "天线口功率 (dBm)", "经过的器件"]),
}


def compute_bom(d, cfg):
    k = d["project"]["m_per_px"]; c = cfg["cable"]
    rows, tot = [], Counter()
    for b in d["boosters"]:
        segs = all_segments(b, d)
        n_ant = count_antennas(b["tree"])
        indoor = c["riser_m"] + sum(manhattan(s) for s in segs) * k + n_ant * c["slack_per_antenna_m"]
        donor = manhattan([b["pos"], b["donor"]]) * k + c["riser_m"] + c["donor_roof_m"]
        dev = device_counts(b["tree"])
        rows.append(dict(id=b["id"], P=b["power_dbm"], n_ant=n_ant, dev=dev, indoor=indoor, donor=donor, nseg=len(segs)))
        tot += dev; tot["indoor"] += indoor; tot["donor"] += donor; tot["seg"] += len(segs); tot["ant"] += n_ant
        tot[("booster", b["power_dbm"])] += 1
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
        for P in sorted({b["power_dbm"] for b in d["boosters"]}, reverse=True):
            ids = ", ".join(r["id"] for r in rows if r["P"] == P)
            w.writerow([l["booster"], f"{P} dBm", tot[("booster", P)], l["pcs"], ids])
        w.writerow([l["ceiling"], "", tot["ant"], l["pcs"], ""])
        w.writerow([l["donor"], "", len(rows), l["pcs"], l["donor_n"]])
        for v in sorted(cfg["couplers"]):
            w.writerow([l["coupler"], f"{v} dB", tot.get(("coupler", v), 0), l["pcs"], ""])
        for v in sorted(cfg["splitters"]):
            w.writerow([l["splitter"], f"1:{v}", tot.get(("splitter", v), 0), l["pcs"], ""])
        nm = c["name"]
        w.writerow([f"{nm} {l['indoor']}", f"{c['loss_db_per_100m']} dB/100 m", round(tot["indoor"]), l["m"], f"≈ {tot['indoor']*FT:,.0f} ft"])
        w.writerow([f"{nm} {l['donor_c']}", "", round(tot["donor"]), l["m"], f"≈ {tot['donor']*FT:,.0f} ft"])
        w.writerow([f"{nm} {l['total']}", "", round(total), l["m"], f"≈ {total*FT:,.0f} ft"])
        w.writerow([f"{nm} {l['order']}", "", order, l["m"], f"≈ {order*FT:,.0f} ft, " + l["margin"].format(p=c["order_margin"] * 100)])
        nconn = c["connectors_per_segment"] * (tot["seg"] + len(rows))
        w.writerow([l["conn"], "", nconn, l["pcs"], l["conn_n"].format(s=tot["seg"], d=len(rows))])
        w.writerow([]); w.writerow([l["per"]]); w.writerow(l["pcols"])
        for r in rows:
            w.writerow([r["id"], f"{r['P']} dBm", r["n_ant"], dev_str(r["dev"], lang), round(r["indoor"]), round(r["donor"])])
        w.writerow([]); w.writerow([l["assum"]])
        for a in l["a"]:
            w.writerow([a.format(riser=c["riser_m"], slack=c["slack_per_antenna_m"], roof=c["donor_roof_m"])])
    return rows, tot, order


def write_summary(d, cfg, lang, results, out):
    l = L[lang]
    with open(out, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh); w.writerow(l["sum_cols"])
        for b in d["boosters"]:
            for r in sorted(results[b["id"]], key=lambda r: (len(r["antenna"]), r["antenna"])):
                w.writerow([txt(b.get("area", ""), lang), f"{T[lang]['booster']} {b['id']}", f"{b['power_dbm']} dBm",
                            txt(b.get("location", ""), lang), r["antenna"], round(r["length_m"]), round(r["cable_db"], 1),
                            round(r["device_db"], 2), round(r["total_db"], 1), round(r["out_dbm"], 1), path_str(r["path"], lang)])


def write_report(d, cfg, lang, results, bom, images, warns, out):
    rows, tot, order = bom; t = T[lang]; zh = lang == "zh"
    total = tot["indoor"] + tot["donor"]
    s = [f"# {txt(d['project']['name'], lang)} – " + ("室内信号覆盖方案" if zh else "Indoor Signal Coverage Design"), ""]
    s += [("## 主机一览" if zh else "## Boosters"), "",
          "| " + " | ".join(t["bcols"]) + " |", "|" + "---|" * len(t["bcols"])]
    for b in d["boosters"]:
        ps = [r["out_dbm"] for r in results[b["id"]]]
        s.append(f"| {t['booster']} {b['id']} | {txt(b.get('location',''), lang)} | {b['power_dbm']} dBm | {len(ps)} | {min(ps):.1f} ~ {max(ps):.1f} dBm |")
    s += ["", ("## 每支天线输出功率" if zh else "## Per-antenna output"), ""]
    s += ["| " + " | ".join(t["cols"]) + " |", "|" + "---|" * len(t["cols"])]
    for b in d["boosters"]:
        for r in sorted(results[b["id"]], key=lambda r: (len(r["antenna"]), r["antenna"])):
            s.append(f"| {r['antenna']} | {r['length_m']:.0f} m | {r['cable_db']:.1f} dB | {r['device_db']:.1f} dB | {r['total_db']:.1f} dB | "
                     f"{r['out_dbm']:.1f} dBm | {path_str(r['path'], lang)} |")
    s += ["", ("## 材料清单" if zh else "## Bill of materials"), ""]
    for P in sorted({b["power_dbm"] for b in d["boosters"]}, reverse=True):
        s.append(f"- {t['booster']} {P} dBm: {tot[('booster', P)]}")
    s.append(f"- {t['antenna']}: {tot['ant']};  {t['donor']}: {len(rows)}")
    s.append(("- 耦合器：" if zh else "- Couplers: ") + ", ".join(f"{v} dB × {tot.get(('coupler', v), 0)}" for v in sorted(cfg["couplers"])))
    s.append(("- 功分器：" if zh else "- Splitters: ") + ", ".join(f"1:{v} × {tot.get(('splitter', v), 0)}" for v in sorted(cfg["splitters"])))
    s.append(f"- {cfg['cable']['name']}: " + (f"室内 {tot['indoor']:.0f} m + 施主线 {tot['donor']:.0f} m = {total:.0f} m（≈{total*FT:,.0f} ft），建议采购 {order} m"
                                             if zh else f"indoor {tot['indoor']:.0f} m + donor {tot['donor']:.0f} m = {total:.0f} m (≈{total*FT:,.0f} ft); order {order} m"))
    s += ["", ("## 图纸" if zh else "## Drawings"), ""] + [f"- {i}" for i in images]
    if warns:
        s += ["", ("## 设计检查提示（内部）" if zh else "## Design-check warnings (internal)"), ""] + [f"- {w}" for w in warns]
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(s) + "\n")
