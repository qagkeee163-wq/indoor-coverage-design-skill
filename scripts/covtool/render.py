"""Draw area maps, antenna layouts and booster/cabling plans on the floor-plan image."""
import os
from collections import Counter

from PIL import Image, ImageDraw, ImageFont

import math

from . import geom
from .engine import antenna_index, branches, node_floors, bands, ref_band
from .i18n import T, txt, path_str, loss_str
from .lint import expand

FT = 3.28084
_FONT = None


def font_path(cfg):
    global _FONT
    if _FONT is None:
        for p in cfg.get("fonts", []) + ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
            if os.path.exists(p):
                _FONT = p
                break
    return _FONT


def F(cfg, size):
    p = font_path(cfg)
    return ImageFont.truetype(p, max(8, int(size))) if p else ImageFont.load_default()


def C(c):
    return tuple(c)


class Canvas:
    def __init__(self, d, cfg, crop=None, width=2400, panel=1700, fade=110, floor=None):
        self.floor = floor or geom.default_floor(d)
        fl = geom.floors(d)[self.floor]
        self.k = float(fl["m_per_px"])
        img = Image.open(os.path.join(d["_dir"], fl["floorplan"])).convert("RGBA")
        crop = crop or [0, 0, img.width, img.height]
        img = img.crop(crop)
        self.z = width / img.width
        img = img.resize((width, max(1, int(img.height * self.z))), Image.LANCZOS)
        img = Image.alpha_composite(img, Image.new("RGBA", img.size, (255, 255, 255, fade)))
        self.base_w, self.base_h = img.size
        self.im = Image.new("RGBA", (img.width + panel, img.height), "white")
        self.im.paste(img, (0, 0))
        self.d = ImageDraw.Draw(self.im)
        self.x0, self.y0 = crop[0], crop[1]
        self.cfg = cfg
        self.s = 1.0

    def P(self, p):
        return ((p[0] - self.x0) * self.z, (p[1] - self.y0) * self.z)

    def f(self, size):
        return F(self.cfg, size)

    def label(self, xy, text, size, fill, bg="white"):
        x, y = xy
        w = self.d.textlength(text, font=self.f(size))
        self.d.rectangle([x - 3, y - 2, x + w + 3, y + size * 1.2], fill=bg)
        self.d.text((x, y - size * 0.1), text, font=self.f(size), fill=fill)

    def grow(self, h):
        if h > self.im.height:
            im2 = Image.new("RGBA", (self.im.width, int(h)), "white")
            im2.paste(self.im, (0, 0))
            self.im = im2
            self.d = ImageDraw.Draw(self.im)

    def save(self, out):
        im = self.im.convert("RGB")
        if im.width > 7900:  # many chat/upload tools reject > 8000 px
            im = im.resize((7900, int(im.height * 7900 / im.width)), Image.LANCZOS)
        im.save(out)
        return out


# ---------------------------------------------------------------- helpers
def floor_name(d, f, lang):
    fl = geom.floors(d).get(f, {})
    return txt(fl.get("name", f), lang) or f


def on_floor(obj, d, floor):
    return geom.obj_floor(obj, d) == floor


def idf_points(d, floor):
    out = []
    for p in d.get("idf", []):
        if isinstance(p, dict):
            if (p.get("floor") or geom.default_floor(d)) == floor:
                out.append(p["pos"])
        elif floor == geom.default_floor(d):
            out.append(p)
    return out


def _dir(pts):
    q = expand(pts)
    for a, b in zip(q, q[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        if dx or dy:
            return ((dx > 0) - (dx < 0), 0) if abs(dx) >= abs(dy) else (0, (dy > 0) - (dy < 0))
    return (1, 0)


def booster_color(cfg, P):
    for b in cfg.get("boosters") or []:
        if b["power_dbm"] == P:
            return C(b["color"])
    pal = [(185, 25, 40), (184, 134, 11), (0, 128, 128), (90, 90, 90), (120, 60, 160)]
    return pal[int(P) % len(pal)]


def aim_unit(deg):
    r = math.radians(float(deg))
    return (math.sin(r), -math.cos(r))          # 0° = up (north), 90° = right (east)


def panel_symbol(cv, X, Y, deg, color, arrow=True):
    ux, uy = aim_unit(deg); px, py = -uy, ux     # perpendicular = wall direction
    L, T2 = 30, 11
    pts = [(X + px * L - ux * T2, Y + py * L - uy * T2), (X - px * L - ux * T2, Y - py * L - uy * T2),
           (X - px * L + ux * T2, Y - py * L + uy * T2), (X + px * L + ux * T2, Y + py * L + uy * T2)]
    cv.d.polygon(pts, fill=color, outline="white")
    if arrow:
        tip = (X + ux * 62, Y + uy * 62)
        cv.d.line([(X + ux * T2, Y + uy * T2), tip], fill=color, width=5)
        cv.d.polygon([tip, (tip[0] - ux * 16 + px * 9, tip[1] - uy * 16 + py * 9),
                      (tip[0] - ux * 16 - px * 9, tip[1] - uy * 16 - py * 9)], fill=color)


def panel_footprint(cv, a, cfg, k):
    rng = float(a.get("range_m") or cfg["panel_antenna_range_m"][1]) / k * cv.z
    hw = float(a.get("half_width_m") or cfg.get("panel_half_width_m", 5)) / k * cv.z
    X, Y = cv.P(a["pos"]); ux, uy = aim_unit(a.get("aim_deg", 0)); px, py = -uy, ux
    return [(X + px * hw, Y + py * hw), (X - px * hw, Y - py * hw),
            (X - px * hw + ux * rng, Y - py * hw + uy * rng), (X + px * hw + ux * rng, Y + py * hw + uy * rng)]


# ---------------------------------------------------------------- step 0 / 1
def draw_areas(cv, d, lang, show_size=True):
    cfg = cv.cfg; k = cv.k; col = C(cfg["colors"]["area"])
    for a in d.get("areas", []):
        if not on_floor(a, d, cv.floor):
            continue
        x0, y0, x1, y1 = a["rect"]
        p0, p1 = cv.P((x0, y0)), cv.P((x1, y1))
        cv.d.rectangle([p0, p1], outline=col, width=5)
        w, h = abs(x1 - x0) * k, abs(y1 - y0) * k
        cv.label((p0[0] + 8, p0[1] + 8), txt(a.get("name", a["id"]), lang), 34, col)
        if show_size:
            cv.label((p0[0] + 8, p0[1] + 52), f"{w:.0f}×{h:.0f} m / {w*FT:.0f}×{h*FT:.0f} ft", 24, col)
            cv.label((p0[0] + 8, p0[1] + 82), f"{w*h:,.0f} m² / {w*h*FT*FT:,.0f} ft²", 24, col)
    for p in idf_points(d, cv.floor):
        X, Y = cv.P(p)
        cv.d.rectangle([X - 12, Y - 12, X + 12, Y + 12], fill=C(cfg["colors"]["idf"]), outline="black", width=2)
        cv.label((X + 16, Y - 14), T[lang]["idf"], 22, C(cfg["colors"]["idf"]))


def _title(d, lang, floor, what):
    fn = floor_name(d, floor, lang) if d.get("floors") else ""
    return f"{txt(d['project']['name'], lang)}{(' · ' + fn) if fn else ''} – {what}"


def render_areas(d, cfg, lang, out, floor=None):
    t = T[lang]; cv = Canvas(d, cfg, floor=floor); k = cv.k
    draw_areas(cv, d, lang)
    x, y = cv.base_w + 40, 40
    cv.d.text((x, y), _title(d, lang, cv.floor, t["areas_title"]), font=cv.f(42), fill="black"); y += 90
    cols = [x, x + 260, x + 560, x + 860, x + 1110]
    for c, h in zip(cols, t["area_tbl"]):
        cv.d.text((c, y), h, font=cv.f(28), fill="black")
    y += 48; tot = 0
    for a in d.get("areas", []):
        if not on_floor(a, d, cv.floor):
            continue
        x0, y0, x1, y1 = a["rect"]; w, h = abs(x1 - x0) * k, abs(y1 - y0) * k; tot += w * h
        for c, v in zip(cols, [txt(a.get("name", a["id"]), lang), f"{w:.0f} × {h:.0f}", f"{w*FT:.0f} × {h*FT:.0f}",
                               f"{w*h:,.0f}", f"{w*h*FT*FT:,.0f}"]):
            cv.d.text((c, y), v, font=cv.f(26), fill="black")
        y += 42
    cv.d.text((x, y + 10), f"{t['total']}: {tot:,.0f} m² / {tot*FT*FT:,.0f} ft²", font=cv.f(30), fill="black")
    cv.grow(y + 80)
    return cv.save(out)


def render_layout(d, cfg, lang, out, floor=None):
    t = T[lang]; cv = Canvas(d, cfg, floor=floor); k = cv.k
    draw_areas(cv, d, lang, show_size=False)
    R = cfg["ceiling_antenna"]["radius_m"] / k * cv.z
    pu = C(cfg["colors"]["antenna"])
    mine = [a for a in d.get("antennas", []) if on_floor(a, d, cv.floor)]
    for a in mine:
        X, Y = cv.P(a["pos"])
        if a.get("type") == "panel":
            cv.d.polygon(panel_footprint(cv, a, cfg, k), outline=pu)
            panel_symbol(cv, X, Y, a.get("aim_deg", 0), pu)
        else:
            cv.d.ellipse([X - R, Y - R, X + R, Y + R], outline=pu + (255,), width=2)
            cv.d.ellipse([X - 18, Y - 18, X + 18, Y + 18], fill=pu, outline="white", width=4)
        cv.label((X + 22, Y - 40), a["id"], 22, pu)
    x, y = cv.base_w + 40, 40
    cv.d.text((x, y), _title(d, lang, cv.floor, t["layout_title"].format(r=cfg["ceiling_antenna"]["radius_m"])),
              font=cv.f(36), fill="black"); y += 80
    cnt = Counter(a.get("area", "?") for a in mine)
    names = {a["id"]: txt(a.get("name", a["id"]), lang) for a in d.get("areas", []) if on_floor(a, d, cv.floor)}
    for aid in list(names) + [a for a in cnt if a not in names]:
        cv.d.text((x, y), f"{names.get(aid, aid)}:  {cnt.get(aid, 0)}", font=cv.f(28), fill="black"); y += 44
    cv.d.text((x, y + 10), f"{t['total']}: " + t["ant_count"].format(n=len(mine)), font=cv.f(30), fill="black")
    cv.grow(y + 80)
    return cv.save(out)


# ---------------------------------------------------------------- plans
def draw_plan(cv, d, boosters, results, lang, ant_labels=True, donor_labels=True, panel_arrows=True):
    cfg = cv.cfg; t = T[lang]; ants = antenna_index(d); FL = cv.floor
    OR = C(cfg["colors"]["cable"]); W = 8
    cnt = Counter()
    devs = []

    def poly(pts):
        if len(pts) > 1:
            cv.d.line([cv.P(p) for p in expand(pts)], fill=OR, width=W, joint="curve")

    def rise_marks(rises):
        for r in rises:
            if r["from_floor"] == FL:
                X, Y = cv.P(r["at_from"])
                cv.d.ellipse([X - 12, Y - 12, X + 12, Y + 12], fill="white", outline=OR, width=5)
                cv.label((X + 16, Y + 6), t["to_floor"].format(f=floor_name(d, r["to_floor"], lang)), 26, OR)
            if r["to_floor"] == FL:
                X, Y = cv.P(r["at_to"])
                cv.d.ellipse([X - 12, Y - 12, X + 12, Y + 12], fill=OR, outline="white", width=3)
                cv.label((X + 16, Y + 6), t["from_floor"].format(f=floor_name(d, r["from_floor"], lang)), 26, OR)

    def draw_branch(path, start_floor, splitter=None, lane=0):
        pieces, rises, end = geom.split_path(path, start_floor, d)
        for i, (f, pts) in enumerate(pieces):
            if f != FL:
                continue
            if splitter is not None and i == 0 and len(pts) >= 2:
                splitter_lane(splitter, pts, lane)
            else:
                poly(pts)
        rise_marks(rises)
        return end

    def splitter_lane(n, pts, i):
        """Outputs leave the far long side as parallel short lines, then follow their paths."""
        od = _dir(n["outputs"][0]["path"]); w = len(n["outputs"])
        X, Y = cv.P(n["pos"]); Lb, Tb = 34, 12
        perp = (od[1] != 0, od[0] != 0)
        off = (-Lb * 0.6 + 1.2 * Lb * i / (w - 1)) if w > 1 else 0
        s0 = (X + od[0] * Tb + perp[0] * off, Y + od[1] * Tb + perp[1] * off)
        q = [cv.P(p) for p in expand(pts)]
        p1 = q[1]
        lane = (p1[0], s0[1]) if od[1] == 0 else (s0[0], p1[1])
        cv.d.line([s0, lane] + (q[2:] if len(q) > 2 else [p1]), fill=OR, width=W, joint="curve")

    for b in boosters:
        nf = node_floors(b, d)

        def walk(n, inpath):
            if n["type"] == "antenna":
                return
            if nf[id(n)] == FL:
                devs.append((n, inpath))
                cnt[("coupler", int(n["value"])) if n["type"] == "coupler" else ("splitter", len(n["outputs"]))] += 1
            for i, (_, br) in enumerate(branches(n)):
                draw_branch(br["path"], nf[id(n)], n if n["type"] == "splitter" else None, i)
                walk(br["node"], br["path"])
        draw_branch(b["feed"], geom.obj_floor(b, d))
        walk(b["tree"], b["feed"])
        if on_floor(b, d, FL) and b.get("donor"):
            a, e = cv.P(b["pos"]), cv.P(b["donor"])
            for i in range(30):  # dashed donor cable
                t0, t1 = i / 30, (i + .5) / 30
                cv.d.line([(a[0] + (e[0] - a[0]) * t0, a[1] + (e[1] - a[1]) * t0),
                           (a[0] + (e[0] - a[0]) * t1, a[1] + (e[1] - a[1]) * t1)], fill=C(cfg["colors"]["donor"]), width=5)

    for n, inpath in devs:
        X, Y = cv.P(n["pos"])
        if n["type"] == "coupler":
            c = C(cfg["couplers"][int(n["value"])]["color"])
            hd, td = _dir(n["through"]["path"]), _dir(n["coupled"]["path"])
            BL, ST, LW = 60, 26, 11
            cv.d.line([(X, Y), (X - hd[0] * BL, Y - hd[1] * BL)], fill=c, width=LW)   # bar on the input side
            cv.d.line([(X, Y), (X + td[0] * ST, Y + td[1] * ST)], fill=c, width=LW)   # stub toward coupled port
            if hd[1] == 0:
                lx, ly = X - hd[0] * BL / 2 - 30, Y + (12 if td[1] <= 0 else -40)
            else:
                lx, ly = X + 14, Y - hd[1] * BL / 2 - 10
            cv.d.text((lx, ly), f"{n['value']}dB", font=cv.f(26), fill=c)
        else:
            w = len(n["outputs"]); sp = cfg["splitters"][w]; fc, oc = C(sp["fill"]), C(sp["line"])
            orient = n.get("orient") or ("h" if _dir(n["outputs"][0]["path"])[0] == 0 else "v")
            L, T2 = 34, 12
            box = [X - L, Y - T2, X + L, Y + T2] if orient == "h" else [X - T2, Y - L, X + T2, Y + L]
            cv.d.rectangle(box, fill=fc, outline=oc, width=3)
            cv.d.text((box[2] + 4, box[1] - 30), f"1:{w}", font=cv.f(28), fill=oc)

    pu = C(cfg["colors"]["antenna"])
    for b in boosters:
        for r in results[b["id"]]:
            a = ants[r["antenna"]]
            if not on_floor(a, d, FL):
                continue
            X, Y = cv.P(r["pos"])
            if a.get("type") == "panel":
                panel_symbol(cv, X, Y, a.get("aim_deg", 0), pu, arrow=panel_arrows)
            else:
                cv.d.ellipse([X - 22, Y - 22, X + 22, Y + 22], fill=pu, outline="white", width=4)
            if ant_labels:
                cv.label((X + 26, Y - 44), r["antenna"], 28, pu)
        if not on_floor(b, d, FL):
            continue
        X, Y = cv.P(b["pos"]); hc = booster_color(cfg, b["power_dbm"])
        cv.d.rectangle([X - 16, Y - 32, X + 16, Y + 32], fill=hc, outline="black", width=3)
        lab = f"{t['booster']} {b['id']}  {b['power_dbm']:g}dBm"; fs = 34; tw = cv.d.textlength(lab, font=cv.f(fs))
        bx = (X - 40 - tw, X - 30) if b.get("label_side", "L") == "L" else (X + 30, X + 40 + tw)
        dy = b.get("label_dy", 0)
        cv.d.rounded_rectangle([bx[0], Y - 24 + dy, bx[1], Y + 24 + dy], 8, fill=hc)
        cv.d.text((bx[0] + 5, Y - 24 + dy), lab, font=cv.f(fs), fill="white")
        if b.get("donor"):
            dx, dy2 = cv.P(b["donor"])
            cv.d.polygon([(dx, dy2 - 44), (dx - 20, dy2 + 4), (dx + 20, dy2 + 4)], fill=C(cfg["colors"]["donor"]))
            if donor_labels:
                tt = f"{t['donor']} ({b['id']}) N↑"; tw = cv.d.textlength(tt, font=cv.f(26))
                tx = dx + 22 if dx < cv.base_w - tw - 40 else dx - 22 - tw
                cv.label((tx, dy2 - 52), tt, 26, (20, 120, 20))
    return cnt


def legend(cv, x, y, boosters, cnt, lang, d, has_panel=False, has_ceiling=True):
    cfg = cv.cfg; t = T[lang]
    for P in sorted({b["power_dbm"] for b in boosters}, reverse=True):
        c = booster_color(cfg, P); cv.d.rectangle([x + 18, y, x + 42, y + 44], fill=c)
        models = sorted({b["model"] for b in boosters if b["power_dbm"] == P and b.get("model")})
        cv.d.text((x + 80, y), f"{t['booster']} {P:g} dBm" + (f"  ({', '.join(models)})" if models else ""), font=cv.f(30), fill="black"); y += 54
    cv.d.polygon([(x + 30, y), (x + 12, y + 40), (x + 48, y + 40)], fill=C(cfg["colors"]["donor"]))
    cv.d.text((x + 80, y), t["donor_legend"], font=cv.f(30), fill="black"); y += 54
    if has_ceiling:
        cv.d.ellipse([x + 12, y + 4, x + 48, y + 40], fill=C(cfg["colors"]["antenna"]))
        cv.d.text((x + 80, y), t["antenna"], font=cv.f(30), fill="black"); y += 54
    if has_panel:
        panel_symbol(cv, x + 30, y + 26, 0, C(cfg["colors"]["antenna"]), arrow=False)
        cv.d.text((x + 80, y), t["panel"], font=cv.f(30), fill="black"); y += 54
    cv.d.line([x, y + 22, x + 60, y + 22], fill=C(cfg["colors"]["cable"]), width=8)
    cv.d.text((x + 80, y), t["cable"].format(name=cfg["cable"]["name"], loss=loss_str(cfg, bands(d, cfg))), font=cv.f(30), fill="black"); y += 60
    cv.d.text((x, y), t["couplers"], font=cv.f(30), fill="black"); y += 52
    for v, sp in sorted(cfg["couplers"].items()):
        c = C(sp["color"]); cv.d.line([(x + 6, y + 30), (x + 56, y + 30)], fill=c, width=10); cv.d.line([(x + 56, y + 30), (x + 56, y + 10)], fill=c, width=10)
        cv.d.text((x + 80, y), t["coupler_item"].format(v=v, c=sp["coupled"], t=sp["through"], n=cnt.get(("coupler", v), 0)), font=cv.f(29), fill=c); y += 50
    cv.d.text((x, y + 4), t["splitters"], font=cv.f(30), fill="black"); y += 54
    for w, sp in sorted(cfg["splitters"].items()):
        n = cnt.get(("splitter", w), 0)
        cv.d.rectangle([x + 20, y + 4, x + 44, y + 44], fill=C(sp["fill"]), outline=C(sp["line"]), width=3)
        cv.d.text((x + 80, y), t["splitter_item"].format(w=w, l=sp["loss"], n=n) + (t["not_used"] if n == 0 else ""), font=cv.f(29), fill=C(sp["line"])); y += 52
    return y + 16


def notes(cv, x, y, lang, d, extra=()):
    cfg = cv.cfg; t = T[lang]; c = cfg["cable"]; a = cfg["antenna_output"]
    for s in [t["note1"].format(lo=a["min_dbm"], hi=a["max_dbm"]),
              t["note2"].format(loss=loss_str(cfg, bands(d, cfg)), riser=c["riser_m"], slack=c["slack_per_antenna_m"]), *extra]:
        cv.d.text((x, y), s, font=cv.f(25), fill=(80, 80, 80)); y += 38
    return y


def _band_tag(bd):
    return f"@{bd}" if bd is not None else ""


def render_view(d, cfg, lang, view, results, out):
    t = T[lang]; ants = antenna_index(d)
    bs = [b for b in d["boosters"] if b["id"] in view["boosters"]]
    floor = view.get("floor") or geom.default_floor(d)
    cv = Canvas(d, cfg, crop=view.get("crop"), width=view.get("width", 2400), panel=view.get("panel", 2100), floor=floor)
    cnt = draw_plan(cv, d, bs, results, lang, panel_arrows=view.get("panel_arrows", True))
    on = [ants[r["antenna"]] for b in bs for r in results[b["id"]] if on_floor(ants[r["antenna"]], d, floor)]
    x, y = cv.base_w + 30, 30
    cv.d.text((x, y), txt(view["title"], lang), font=cv.f(44), fill="black"); y += 80
    y = legend(cv, x, y, bs, cnt, lang, d, has_panel=any(a.get("type") == "panel" for a in on),
               has_ceiling=any(a.get("type", "ceiling") != "panel" for a in on))
    bl = bands(d, cfg); rb = ref_band(d, cfg); others = [b for b in bl if b != rb]
    head = list(t["cols"])
    if rb is not None:
        head[2] += f" {_band_tag(rb)}"; head[4] += f" {_band_tag(rb)}"; head[5] += f" {_band_tag(rb)}"
    cols = [x, x + 140, x + 290, x + 530, x + 710, x + 950, x + 1190]
    if others:
        head = head[:6] + [t["other_bands"]] + head[6:]
        cols = cols[:6] + [x + 1190, x + 1530]
    for c, h in zip(cols, head):
        cv.d.text((c, y), h, font=cv.f(26), fill="black")
    y += 46
    for b in bs:
        loc = txt(b.get("location", ""), lang)
        mdl = f", {b['model']}" if b.get("model") else ""
        cv.d.text((x, y), f"{t['booster']} {b['id']}  ({loc}, {b['power_dbm']:g} dBm{mdl})", font=cv.f(30),
                  fill=booster_color(cfg, b["power_dbm"])); y += 46
        rows = [r for r in results[b["id"]] if not d.get("floors") or r["floor"] == floor]
        for r in sorted(rows, key=lambda r: (len(r["antenna"]), r["antenna"])):
            vals = [r["antenna"], f"{r['length_m']:.1f} m", f"{r['cable_db']:.1f} dB", f"{r['device_db']:.1f} dB",
                    f"{r['total_db']:.1f} dB", f"{r['out_dbm']:.2f} dBm"]
            if others:
                vals.append("  ".join(f"{bd}: {r['by_band'][bd]['out_dbm']:.2f}" for bd in others))
            for c, v in zip(cols, vals):
                cv.d.text((c, y), v, font=cv.f(26), fill="black")
            cv.d.text((cols[-1], y + 3), path_str(r["path"], lang), font=cv.f(22), fill=(70, 70, 70)); y += 42
        y += 16
    y = notes(cv, x, y + 10, lang, d, [txt(n, lang) for n in view.get("notes", [])])
    cv.grow(y + 40)
    return cv.save(out)


def render_overview(d, cfg, lang, results, out, floor=None):
    t = T[lang]; ants = antenna_index(d)
    cv = Canvas(d, cfg, width=d["project"].get("overview_width", 3000), panel=1900, floor=floor)
    cnt = draw_plan(cv, d, d["boosters"], results, lang, ant_labels=False, donor_labels=False, panel_arrows=False)
    on = [ants[r["antenna"]] for b in d["boosters"] for r in results[b["id"]] if on_floor(ants[r["antenna"]], d, cv.floor)]
    x, y = cv.base_w + 30, 30
    n_ant = len(on)
    nb = len([b for b in d["boosters"] if on_floor(b, d, cv.floor)])
    what = (f"{nb} boosters, {n_ant} antennas" if lang == "en" else f"{nb} 台主机，{n_ant} 支天线")
    cv.d.text((x, y), _title(d, lang, cv.floor, what), font=cv.f(40), fill="black"); y += 80
    y = legend(cv, x, y, d["boosters"], cnt, lang, d, has_panel=any(a.get("type") == "panel" for a in on),
               has_ceiling=any(a.get("type", "ceiling") != "panel" for a in on))
    cols = [x, x + 170, x + 900, x + 1060, x + 1220]
    for c, h in zip(cols, t["bcols"]):
        cv.d.text((c, y), h, font=cv.f(28), fill="black")
    y += 46
    for b in d["boosters"]:
        ps = [v["out_dbm"] for r in results[b["id"]] for v in r["by_band"].values()]
        for c, v in zip(cols, [f"{t['booster']} {b['id']}", txt(b.get("location", ""), lang), f"{b['power_dbm']:g} dBm",
                               str(len(results[b["id"]])), f"{min(ps):.2f} ~ {max(ps):.2f} dBm"]):
            cv.d.text((c, y), v, font=cv.f(26), fill="black")
        y += 42
    y = notes(cv, x, y + 20, lang, d)
    cv.grow(y + 40)
    return cv.save(out)
