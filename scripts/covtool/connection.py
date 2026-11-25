"""Connection diagram: one simple, intuitive schematic of how every booster feeds every antenna.

Floors are pale horizontal bands (top floor on top, roof above when there are donors). Each booster gets
its own column and its own riser, so boosters that sit in different places are never drawn together.
Antennas are leaves at the bottom of their floor band; couplers / splitters sit at the floor where they
are installed. Lines are right-angle elbows only.

client=True (customer version): only floor names, booster titles and "Roof" — no powers, losses,
lengths, device values or antenna IDs.
"""
from PIL import Image, ImageDraw

from . import geom
from .engine import branches, node_floors, branch_length_m
from .i18n import T, txt
from .render import F, C, booster_color, floor_name

LV = 95          # vertical step between device levels inside a floor band
SLOT = 170
LEFT = 300
TOP = 210
GAP = 140
PALE = [(232, 242, 252), (240, 248, 234), (252, 244, 230), (244, 236, 250), (234, 248, 246), (250, 238, 240)]


def _leaves(n, acc):
    if n["type"] == "antenna":
        acc.append(n)
    for _, br in branches(n):
        _leaves(br["node"], acc)
    return acc


def render_connection(d, cfg, lang, results, out, client=False):
    t = T[lang]
    fl = geom.floors(d)
    order = sorted(fl, key=lambda f: -float(fl[f].get("elevation_m", 0)))
    has_roof = any(b.get("donor") or b.get("donor_cable_m") for b in d["boosters"])
    bands_ = (["_roof"] if has_roof else []) + order
    res = {b["id"]: {r["antenna"]: r for r in results.get(b["id"], [])} for b in d["boosters"]}
    ants = {a["id"]: a for a in d.get("antennas", [])}

    # device depth per floor: every child sits one level below its parent when both are on the same floor,
    # so elbows never cross (siblings own disjoint x ranges)
    depth, nfs, maxdep = {}, {}, {f: -1 for f in bands_}
    for b in d["boosters"]:
        nf = node_floors(b, d); nfs[b["id"]] = nf

        def dep(n, k):
            depth[id(n)] = k
            if n["type"] != "antenna":
                maxdep[nf[id(n)]] = max(maxdep[nf[id(n)]], k)
            for _, br in branches(n):
                c = br["node"]
                dep(c, k + 1 if nf[id(c)] == nf[id(n)] else 0)
        dep(b["tree"], 0)
    band_h = {f: (260 if f == "_roof" else 150 + (maxdep[f] + 1) * LV + 120) for f in bands_}
    top = {}
    y = TOP
    for f in bands_:
        top[f] = y; y += band_h[f]

    cols, x = [], LEFT
    for b in d["boosters"]:
        n = max(1, len(_leaves(b["tree"], [])))
        w = 150 + n * SLOT
        cols.append((b, x, w)); x += w + GAP
    W, H = x - GAP + 80, y + 40
    im = Image.new("RGB", (W, H), "white")
    dr = ImageDraw.Draw(im)
    for i, f in enumerate(bands_):
        dr.rectangle([0, top[f], W, top[f] + band_h[f] - 6], fill=(246, 246, 246) if f == "_roof" else PALE[i % len(PALE)])
        name = t["roof"] if f == "_roof" else (floor_name(d, f, lang) if d.get("floors") else "") or t["floor"]
        dr.text((24, top[f] + band_h[f] / 2 - 22), name, font=F(cfg, 40), fill=(40, 40, 40))

    OR = C(cfg["colors"]["cable"]); PU = C(cfg["colors"]["antenna"])

    def line(pts, color=OR, width=7):
        dr.line(pts, fill=color, width=width, joint="curve")

    for b, x0, w in cols:
        nf = nfs[b["id"]]; bf = geom.obj_floor(b, d); hc = booster_color(cfg, b["power_dbm"])
        title = f"{t['booster']} {b['id']}"
        if not client:
            title += f"  {b['power_dbm']:g} dBm" + (f"  {b['model']}" if b.get("model") else "")
        dr.text((x0, TOP - 90), title, font=F(cfg, 38), fill=hc)
        if not client and b.get("location"):
            dr.text((x0, TOP - 44), txt(b["location"], lang), font=F(cfg, 24), fill=(90, 90, 90))

        pos = {}
        for i, a in enumerate(_leaves(b["tree"], [])):
            f = nf[id(a)]
            pos[id(a)] = (x0 + 150 + SLOT * (i + 0.5), top[f] + band_h[f] - 120)

        def place(n):
            if n["type"] == "antenna":
                return
            kids = [br["node"] for _, br in branches(n)]
            for k in kids:
                place(k)
            xs = [pos[id(k)][0] for k in kids]
            f = nf[id(n)]
            pos[id(n)] = (sum(xs) / len(xs), top[f] + 90 + depth[id(n)] * LV)
        place(b["tree"])

        bx = x0 + 50; root = pos[id(b["tree"])]
        by = root[1] if nf[id(b["tree"])] == bf else top[bf] + 90
        line([(bx, by), (bx, root[1]), root])            # the booster's own riser, then across
        if not client:
            L, _ = geom.path_length_m(b["feed"], bf, d)
            dr.text((bx + 34, root[1] - 34), f"{L + cfg['cable']['riser_m']:.1f} m", font=F(cfg, 22), fill=OR)

        def leaf_x(n):
            return [pos[id(a)][0] for a in _leaves(n, [])]

        def edges(n):
            p = pos[id(n)]
            for _, br in branches(n):
                k = br["node"]; q = pos[id(k)]
                if nf[id(k)] == nf[id(n)]:
                    line([p, (q[0], p[1]), q]); lx, ly = q[0] + 8, (p[1] + q[1]) / 2 - 12
                else:
                    # change of floor: its own riser beside the subtree, so it never runs through other symbols
                    rx = min(leaf_x(k)) - SLOT * 0.5
                    line([p, (rx, p[1]), (rx, q[1]), q]); lx, ly = rx + 8, p[1] + (-70 if q[1] < p[1] else 30)
                if not client:
                    L, _ = branch_length_m(br, nf[id(n)], d)
                    dr.text((lx, ly), f"{L:.1f} m", font=F(cfg, 22), fill=OR)
                edges(k)
        edges(b["tree"])

        if has_roof and (b.get("donor") or b.get("donor_cable_m")):
            ty = top["_roof"] + 130
            for yy in range(int(ty + 30), int(by - 44), 26):
                dr.line([(bx, yy), (bx, min(yy + 13, by - 44))], fill=C(cfg["colors"]["donor"]), width=5)
            dr.polygon([(bx, ty - 30), (bx - 26, ty + 30), (bx + 26, ty + 30)], fill=C(cfg["colors"]["donor"]))
            if not client:
                dr.text((bx + 34, ty - 10), t["donor"], font=F(cfg, 24), fill=(20, 120, 20))
        dr.rectangle([bx - 26, by - 40, bx + 26, by + 40], fill=hc, outline="black", width=3)

        def symbols(n):
            X, Y = pos[id(n)]
            if n["type"] == "antenna":
                if ants[n["id"]].get("type") == "panel":
                    dr.rectangle([X - 34, Y - 12, X + 34, Y + 12], fill=PU, outline="white", width=2)
                else:
                    dr.ellipse([X - 20, Y - 20, X + 20, Y + 20], fill=PU, outline="white", width=3)
                if not client:
                    r = res[b["id"]].get(n["id"])
                    dr.text((X - 30, Y + 24), n["id"], font=F(cfg, 26), fill=PU)
                    if r:
                        dr.text((X - 50, Y + 56), f"{r['out_dbm']:.1f} dBm", font=F(cfg, 22), fill=(60, 60, 60))
                return
            if n["type"] == "coupler":
                c = C(cfg["couplers"][int(n["value"])]["color"])
                dr.line([(X - 34, Y), (X + 34, Y)], fill=c, width=12)
                dr.line([(X, Y), (X, Y + 24)], fill=c, width=12)
                if not client:
                    lab = f"{n['value']} dB"; dr.text((X - 44 - dr.textlength(lab, font=F(cfg, 24)), Y - 40), lab, font=F(cfg, 24), fill=c)
            else:
                w_ = len(n["outputs"]); sp = cfg["splitters"][w_]
                dr.rectangle([X - 36, Y - 13, X + 36, Y + 13], fill=C(sp["fill"]), outline=C(sp["line"]), width=3)
                if not client:
                    lab = f"1:{w_}"; dr.text((X - 44 - dr.textlength(lab, font=F(cfg, 24)), Y - 42), lab, font=F(cfg, 24), fill=C(sp["line"]))
            for _, br in branches(n):
                symbols(br["node"])
        symbols(b["tree"])

    dr.text((24, 24), f"{txt(d['project']['name'], lang)} – {t['conn_title']}", font=F(cfg, 40), fill="black")
    im.save(out)
    return out
