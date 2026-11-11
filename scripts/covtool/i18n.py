T = {
    "en": {
        "booster": "Booster", "donor": "Donor antenna", "donor_legend": "Donor antenna: roof corner at exterior wall, facing the base station",
        "antenna": "Indoor ceiling antenna", "cable": "{name} cable, {loss} dB/100 m",
        "couplers": "Couplers (input & through at the ends, coupled port at the side):",
        "splitters": "Splitters (single input on one long side, outputs side by side on the other):",
        "coupler_item": "{v} dB coupler (coupled −{c}, through −{t} dB)   Qty: {n}",
        "splitter_item": "1:{w} splitter (−{l} dB per port)   Qty: {n}", "not_used": " (not used)",
        "cols": ["Antenna", "Cable", "Cable loss", "Device loss", "Total loss", "Output", "Path (devices passed)"],
        "bcols": ["Booster", "Location", "Output", "Antennas", "Antenna output"],
        "coupled": "coupled", "through": "through", "cpl": "{v} dB coupler ({p}) −{l}", "spl": "1:{w} splitter −{l}",
        "note1": "Antenna output = booster output − device loss − cable loss (target {lo} to {hi} dBm).",
        "note2": "Cable loss = length × {loss} dB/100 m. Right-angle routing, incl. {riser} m riser at the booster and {slack} m slack per antenna.",
        "idf": "IDF", "area_tbl": ["Area", "Size (m)", "Size (ft)", "Area (m²)", "Area (ft²)"],
        "ant_count": "{n} ceiling antennas", "layout_title": "Antenna layout (ceiling antennas, R = {r} m)",
        "areas_title": "Area division (approx. rectangles)", "total": "Total",
        "files": {"overview": "Overview", "areas": "Areas", "layout": "Antenna_Layout",
                  "summary": "Antenna_Output_Summary.csv", "bom": "Bill_of_Materials.csv", "report": "Report.md"},
    },
    "zh": {
        "booster": "主机", "donor": "施主天线", "donor_legend": "施主天线：外墙屋顶角，朝向基站",
        "antenna": "吸顶天线", "cable": "{name} 线缆，{loss} dB/100 m",
        "couplers": "耦合器（进线和直通在两端，耦合端在侧面）：",
        "splitters": "功分器（一条长边单进，另一条长边并排出）：",
        "coupler_item": "{v} dB 耦合器（耦合端 −{c}，直通 −{t} dB）  数量：{n}",
        "splitter_item": "1:{w} 功分器（每路 −{l} dB）  数量：{n}", "not_used": "（未使用）",
        "cols": ["天线", "线长", "线损", "器件损耗", "总损耗", "天线口功率", "经过的器件"],
        "bcols": ["主机", "位置", "功率", "天线数", "天线口功率"],
        "coupled": "耦合端", "through": "直通", "cpl": "{v}dB耦合器·{p} −{l}", "spl": "1:{w}功分器 −{l}",
        "note1": "天线口功率 = 主机功率 − 器件损耗 − 线损（目标 {lo}–{hi} dBm）。",
        "note2": "线损 = 线长 × {loss} dB/100 m。按直角走线，含主机到吊顶 {riser} m 和每支天线 {slack} m 余量。",
        "idf": "IDF 弱电间", "area_tbl": ["区域", "尺寸 (m)", "尺寸 (ft)", "面积 (m²)", "面积 (ft²)"],
        "ant_count": "{n} 支吸顶天线", "layout_title": "天线布置（吸顶天线，覆盖半径 {r} m）",
        "areas_title": "区域划分（按矩形估算）", "total": "合计",
        "files": {"overview": "全厂总图", "areas": "区域划分", "layout": "天线布置",
                  "summary": "天线输出功率汇总.csv", "bom": "材料清单.csv", "report": "方案说明.md"},
    },
}


def txt(d, lang):
    """A design text field may be a plain string or {"en":..., "zh":...}."""
    if isinstance(d, dict):
        return d.get(lang) or d.get("en") or next(iter(d.values()))
    return d or ""


def path_str(path, lang):
    t = T[lang]
    out = []
    for kind, v, port, loss in path:
        if kind == "coupler":
            out.append(t["cpl"].format(v=v, p=t[port], l=loss))
        else:
            out.append(t["spl"].format(w=v, l=loss))
    return " → ".join(out) if out else "—"
