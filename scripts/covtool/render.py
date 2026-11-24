"""Draw area maps, antenna layouts and booster/cabling plans on the floor-plan image."""
import os
from collections import Counter

from PIL import Image, ImageDraw, ImageFont

from .engine import antenna_index, branches, node_pos, device_counts
from .i18n import T, txt, path_str
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
    def __init__(self, d, cfg, crop=None, width=2400, panel=1700, fade=110):
        img = Image.open(os.path.join(d["_dir"], d["project"]["floorplan"])).convert("RGBA")
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


# ---------------------------------------------------------------- step 0 / 1
def draw_areas(cv, d, lang, show_size=True):
    cfg = cv.cfg; k = d["project"]["m_per_px"]; col = C(cfg["colors"]["area"])
    for a in d.get("areas", []):
        x0, y0, x1, y1 = a["rect"]
        p0, p1 = cv.P((x0, y0)), cv.P((x1, y1))
        cv.d.rectangle([p0, p1], outline=col, width=5)
        w, h = abs(x1 - x0) * k, abs(y1 - y0) * k
        lab = txt(a.get("name", a["id"]), lang)
        cv.label((p0[0] + 8, p0[1] + 8), lab, 34, col)
        if show_size:
            cv.label((p0[0] + 8, p0[1] + 52), f"{w:.0f}×{h:.0f} m / {w*FT:.0f}×{h*FT:.0f} ft", 24, col)
            cv.label((p0[0] + 8, p0[1] + 82), f"{w*h:,.0f} m² / {w*h*FT*FT:,.0f} ft²", 24, col)
    for p in d.get("idf", []):
        X, Y = cv.P(p)
        cv.d.rectangle([X - 12, Y - 12, X + 12, Y + 12], fill=C(cfg["colors"]["idf"]), outline="black", width=2)
        cv.label((X + 16, Y - 14), T[lang]["idf"], 22, C(cfg["colors"]["idf"]))


def render_areas(d, cfg, lang, out):
    t = T[lang]; cv = Canvas(d, cfg); k = d["project"]["m_per_px"]
    draw_areas(cv, d, lang)
    x, y = cv.base_w + 40, 40
    cv.d.text((x, y), f"{txt(d['project']['name'], lang)} – {t['areas_title']}", font=cv.f(42), fill="black"); y += 90
    cols = [x, x + 260, x + 560, x + 860, x + 1110]
    for c, h in zip(cols, t["area_tbl"]):
        cv.d.text((c, y), h, font=cv.f(28), fill="black")
    y += 48; tot = 0
    for a in d.get("areas", []):
        x0, y0, x1, y1 = a["rect"]; w, h = abs(x1 - x0) * k, abs(y1 - y0) * k; tot += w * h
        for c, v in zip(cols, [txt(a.get("name", a["id"]), lang), f"{w:.0f} × {h:.0f}", f"{w*FT:.0f} × {h*FT:.0f}",
                               f"{w*h:,.0f}", f"{w*h*FT*FT:,.0f}"]):
            cv.d.text((c, y), v, font=cv.f(26), fill="black")
        y += 42
    cv.d.text((x, y + 10), f"{t['total']}: {tot:,.0f} m² / {tot*FT*FT:,.0f} ft²", font=cv.f(30), fill="black")
    cv.grow(y + 80)
    return cv.save(out)


def render_layout(d, cfg, lang, out):
    t = T[lang]; cv = Canvas(d, cfg); k = d["project"]["m_per_px"]
    draw_areas(cv, d, lang, show_size=False)
    R = cfg["ceiling_antenna"]["radius_m"] / k * cv.z
    pu = C(cfg["colors"]["antenna"])
    for a in d.get("antennas", []):
        X, Y = cv.P(a["pos"])
        cv.d.ellipse([X - R, Y - R, X + R, Y + R], outline=pu + (255,), width=2)
        cv.d.ellipse([X - 18, Y - 18, X + 18, Y + 18], fill=pu, outline="white", width=4)
        cv.label((X + 22, Y - 34), a["id"], 22, pu)
    x, y = cv.base_w + 40, 40
    cv.d.text((x, y), t["layout_title"].format(r=cfg["ceiling_antenna"]["radius_m"]), font=cv.f(40), fill="black"); y += 80
    cnt = Counter(a.get("area", "?") for a in d.get("antennas", []))
    names = {a["id"]: txt(a.get("name", a["id"]), lang) for a in d.get("areas", [])}
    for aid in [a["id"] for a in d.get("areas", [])] + [a for a in cnt if a not in names]:
        cv.d.text((x, y), f"{names.get(aid, aid)}:  {cnt.get(aid, 0)}", font=cv.f(28), fill="black"); y += 44
    cv.d.text((x, y + 10), f"{t['total']}: " + t["ant_count"].format(n=len(d.get("antennas", []))), font=cv.f(30), fill="black")
    cv.grow(y + 80)
    return cv.save(out)


# ---------------------------------------------------------------- step 2 plans
def _dir(pts):
    q = expand(pts)
    for a, b in zip(q, q[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        if dx or dy:
            return ((dx > 0) - (dx < 0), 0) if abs(dx) >= abs(dy) else (0, (dy > 0) - (dy < 0))
    return (1, 0)


def booster_color(cfg, P):
    for b in cfg["boosters"]:
        if b["power_dbm"] == P:
            return C(b["color"])
    return (185, 25, 40)


def draw_plan(cv, d, boosters, results, lang, ant_labels=True, donor_labels=True):
    cfg = cv.cfg; t = T[lang]; ants = antenna_index(d)
    OR = C(cfg["colors"]["cable"]); W = 8
    cnt = Counter()
    devs = []

    def poly(pts):
        cv.d.line([cv.P(p) for p in expand(pts)], fill=OR, width=W, joint="curve")

    def walk(n, inpath):
        if n["type"] == "antenna":
            return
        devs.append((n, inpath))
        if n["type"] == "splitter":
            draw_splitter_outputs(n)
        for _, br in branches(n):
            if n["type"] != "splitter":
                poly(br["path"])
            walk(br["node"], br["path"])

    def draw_splitter_outputs(n):
        """Outputs leave the far long side as parallel short lines, then follow their paths."""
        od = _dir(n["outputs"][0]["path"]); w = len(n["outputs"])
        X, Y = cv.P(n["pos"]); Lb, Tb = 34, 12
        perp = (od[1] != 0, od[0] != 0)            # axis along the long side
        for i, br in enumerate(n["outputs"]):
            off = (-Lb * 0.6 + 1.2 * Lb * i / (w - 1)) if w > 1 else 0
            s0 = (X + od[0] * Tb + perp[0] * off, Y + od[1] * Tb + perp[1] * off)
            pts = [cv.P(p) for p in expand(br["path"])]
            if len(pts) < 2:
                continue
            p1 = pts[1]
            lane = (p1[0], s0[1]) if od[1] == 0 else (s0[0], p1[1])
            line = [s0, lane] + (pts[2:] if len(pts) > 2 else [p1])
            cv.d.line(line, fill=OR, width=W, joint="curve")

    for b in boosters:
        poly(b["feed"]); walk(b["tree"], b["feed"])
        a, e = cv.P(b["pos"]), cv.P(b["donor"])
        for i in range(30):  # dashed donor cable
            t0, t1 = i / 30, (i + .5) / 30
            cv.d.line([(a[0] + (e[0] - a[0]) * t0, a[1] + (e[1] - a[1]) * t0),
                       (a[0] + (e[0] - a[0]) * t1, a[1] + (e[1] - a[1]) * t1)], fill=C(cfg["colors"]["donor"]), width=5)
        cnt += device_counts(b["tree"])

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
            X, Y = cv.P(r["pos"])
            cv.d.ellipse([X - 22, Y - 22, X + 22, Y + 22], fill=pu, outline="white", width=4)
            if ant_labels:
                cv.label((X + 26, Y - 44), r["antenna"], 28, pu)
        X, Y = cv.P(b["pos"]); hc = booster_color(cfg, b["power_dbm"])
        cv.d.rectangle([X - 16, Y - 32, X + 16, Y + 32], fill=hc, outline="black", width=3)
        lab = f"{t['booster']} {b['id']}  {b['power_dbm']}dBm"; fs = 34; tw = cv.d.textlength(lab, font=cv.f(fs))
        bx = (X - 40 - tw, X - 30) if b.get("label_side", "L") == "L" else (X + 30, X + 40 + tw)
        dy = b.get("label_dy", 0)
        cv.d.rounded_rectangle([bx[0], Y - 24 + dy, bx[1], Y + 24 + dy], 8, fill=hc)
        cv.d.text((bx[0] + 5, Y - 24 + dy), lab, font=cv.f(fs), fill="white")
        dx, dy2 = cv.P(b["donor"])
        cv.d.polygon([(dx, dy2 - 44), (dx - 20, dy2 + 4), (dx + 20, dy2 + 4)], fill=C(cfg["colors"]["donor"]), outline="black", width=2)
        if donor_labels:
            tt = f"{t['donor']} ({b['id']}) N↑"; tw = cv.d.textlength(tt, font=cv.f(26))
            tx = dx + 22 if dx < cv.base_w - tw - 40 else dx - 22 - tw
            cv.label((tx, dy2 - 52), tt, 26, (20, 120, 20))
    return cnt


def legend(cv, x, y, boosters, cnt, lang):
    cfg = cv.cfg; t = T[lang]
    for P in sorted({b["power_dbm"] for b in boosters}, reverse=True):
        c = booster_color(cfg, P); cv.d.rectangle([x + 18, y, x + 42, y + 44], fill=c)
        cv.d.text((x + 80, y), f"{t['booster']} {P} dBm", font=cv.f(30), fill="black"); y += 54
    cv.d.polygon([(x + 30, y), (x + 12, y + 40), (x + 48, y + 40)], fill=C(cfg["colors"]["donor"]), outline="black")
    cv.d.text((x + 80, y), t["donor_legend"], font=cv.f(30), fill="black"); y += 54
    cv.d.ellipse([x + 12, y + 4, x + 48, y + 40], fill=C(cfg["colors"]["antenna"]))
    cv.d.text((x + 80, y), t["antenna"], font=cv.f(30), fill="black"); y += 54
    cv.d.line([x, y + 22, x + 60, y + 22], fill=C(cfg["colors"]["cable"]), width=8)
    cv.d.text((x + 80, y), t["cable"].format(name=cfg["cable"]["name"], loss=cfg["cable"]["loss_db_per_100m"]), font=cv.f(30), fill="black"); y += 60
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


def notes(cv, x, y, lang, extra=()):
    cfg = cv.cfg; t = T[lang]; c = cfg["cable"]; a = cfg["antenna_output"]
    for s in [t["note1"].format(lo=a["min_dbm"], hi=a["max_dbm"]),
              t["note2"].format(loss=c["loss_db_per_100m"], riser=c["riser_m"], slack=c["slack_per_antenna_m"]), *extra]:
        cv.d.text((x, y), s, font=cv.f(25), fill=(80, 80, 80)); y += 38
    return y


def render_view(d, cfg, lang, view, results, out):
    t = T[lang]
    bs = [b for b in d["boosters"] if b["id"] in view["boosters"]]
    cv = Canvas(d, cfg, crop=view.get("crop"), width=view.get("width", 2400), panel=view.get("panel", 2000))
    cnt = draw_plan(cv, d, bs, results, lang)
    x, y = cv.base_w + 30, 30
    cv.d.text((x, y), txt(view["title"], lang), font=cv.f(44), fill="black"); y += 80
    y = legend(cv, x, y, bs, cnt, lang)
    cols = [x, x + 150, x + 300, x + 470, x + 650, x + 830, x + 1010]
    for c, h in zip(cols, t["cols"]):
        cv.d.text((c, y), h, font=cv.f(28), fill="black")
    y += 46
    for b in bs:
        cv.d.text((x, y), f"{t['booster']} {b['id']}  ({txt(b.get('location', ''), lang)}, {b['power_dbm']} dBm)", font=cv.f(30), fill=booster_color(cfg, b["power_dbm"])); y += 46
        for r in sorted(results[b["id"]], key=lambda r: (len(r["antenna"]), r["antenna"])):
            for c, v in zip(cols, [r["antenna"], f"{r['length_m']:.0f} m", f"{r['cable_db']:.1f} dB", f"{r['device_db']:.1f} dB",
                                   f"{r['total_db']:.1f} dB", f"{r['out_dbm']:.1f} dBm"]):
                cv.d.text((c, y), v, font=cv.f(27), fill="black")
            cv.d.text((cols[6], y + 3), path_str(r["path"], lang), font=cv.f(23), fill=(70, 70, 70)); y += 42
        y += 16
    y = notes(cv, x, y + 10, lang, [txt(n, lang) for n in view.get("notes", [])])
    cv.grow(y + 40)
    return cv.save(out)


def render_overview(d, cfg, lang, results, out):
    t = T[lang]
    cv = Canvas(d, cfg, width=d["project"].get("overview_width", 3000), panel=1800)
    cnt = draw_plan(cv, d, d["boosters"], results, lang, ant_labels=False, donor_labels=False)
    x, y = cv.base_w + 30, 30
    n_ant = sum(len(v) for v in results.values())
    title = f"{txt(d['project']['name'], lang)} – " + (f"{len(d['boosters'])} boosters, {n_ant} ceiling antennas" if lang == "en"
                                                       else f"{len(d['boosters'])} 台主机，{n_ant} 支吸顶天线")
    cv.d.text((x, y), title, font=cv.f(42), fill="black"); y += 80
    y = legend(cv, x, y, d["boosters"], cnt, lang)
    cols = [x, x + 170, x + 900, x + 1060, x + 1220]
    for c, h in zip(cols, t["bcols"]):
        cv.d.text((c, y), h, font=cv.f(28), fill="black")
    y += 46
    for b in d["boosters"]:
        ps = [r["out_dbm"] for r in results[b["id"]]]
        for c, v in zip(cols, [f"{t['booster']} {b['id']}", txt(b.get("location", ""), lang), f"{b['power_dbm']} dBm", str(len(ps)),
                               f"{min(ps):.1f} ~ {max(ps):.1f} dBm"]):
            cv.d.text((c, y), v, font=cv.f(26), fill="black")
        y += 42
    y = notes(cv, x, y + 20, lang)
    cv.grow(y + 40)
    return cv.save(out)
