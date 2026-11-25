"""Design-rule checks. Each rule comes from a real correction made during design reviews."""
from . import geom
from .engine import (antenna_index, branches, node_pos, couplers_of, output_in_window, floor_pieces,
                     node_floors, branch_length_m, bands, count_antennas)


def expand(pts):
    """Same expansion the renderer uses: a diagonal hop is drawn horizontal-first."""
    pts = [geom.xy(p) for p in pts]
    q = [pts[0]]
    for a in pts[1:]:
        b = q[-1]
        if a[0] != b[0] and a[1] != b[1]:
            q.append((a[0], b[1]))
        q.append(a)
    return q


def first_dir(pts):
    q = expand(pts)
    for a, b in zip(q, q[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        if dx or dy:
            return ((dx > 0) - (dx < 0), (dy > 0) - (dy < 0))
    return (0, 0)


def last_dir(pts):
    """Travel direction of the final non-zero hop."""
    q = expand(pts)
    for a, b in reversed(list(zip(q, q[1:]))):
        dx, dy = b[0] - a[0], b[1] - a[1]
        if dx or dy:
            return ((dx > 0) - (dx < 0), (dy > 0) - (dy < 0))
    return (0, 0)


AIM = {0: (0, -1), 90: (1, 0), 180: (0, 1), 270: (-1, 0)}


def aim_vec(deg):
    return AIM.get(int(round(float(deg))) % 360)


def axis_segments(pts):
    q = expand(pts)
    for a, b in zip(q, q[1:]):
        if a != b:
            yield a, b


def overlap_len(s1, s2):
    (a1, b1), (a2, b2) = s1, s2
    if a1[1] == b1[1] == a2[1] == b2[1]:
        lo1, hi1 = sorted((a1[0], b1[0])); lo2, hi2 = sorted((a2[0], b2[0]))
        return max(0, min(hi1, hi2) - max(lo1, lo2))
    if a1[0] == b1[0] == a2[0] == b2[0]:
        lo1, hi1 = sorted((a1[1], b1[1])); lo2, hi2 = sorted((a2[1], b2[1]))
        return max(0, min(hi1, hi2) - max(lo1, lo2))
    return 0


def idf_list(d):
    out = []
    for p in d.get("idf", []):
        if isinstance(p, dict):
            out.append((p.get("floor") or geom.default_floor(d), geom.xy(p["pos"])))
        else:
            out.append((geom.default_floor(d), geom.xy(p)))
    return out


def detour_m(path, start_floor, d):
    """Cable walked beyond the shortest right-angle route, summed over the floors of one path (metres).

    A plain L / Z route has zero detour; going past a point and coming back (来回布线) does not."""
    fl = geom.floors(d)
    pieces, _, _ = geom.split_path(path, start_floor, d)
    out = 0.0
    for f, pts in pieces:
        if len(pts) < 2:
            continue
        walked = geom.manhattan(expand(pts))
        direct = abs(pts[0][0] - pts[-1][0]) + abs(pts[0][1] - pts[-1][1])
        out += (walked - direct) * float(fl[f]["m_per_px"])
    return out


def _rect_m(a, d, cfg):
    """Axis-aligned panel footprint in metres for aims of 0/90/180/270°, else None."""
    v = aim_vec(a.get("aim_deg", 0))
    if not v:
        return None
    k = float(geom.floors(d)[geom.obj_floor(a, d)]["m_per_px"])
    x, y = a["pos"][0] * k, a["pos"][1] * k
    rng = float(a.get("range_m") or cfg["panel_antenna_range_m"][1])
    hw = float(a.get("half_width_m") or cfg.get("panel_half_width_m", 5))
    if v[0]:
        xs = sorted((x, x + v[0] * rng)); ys = (y - hw, y + hw)
    else:
        ys = sorted((y, y + v[1] * rng)); xs = (x - hw, x + hw)
    return (xs[0], ys[0], xs[1], ys[1])


def _rect_overlap(r1, r2):
    w = min(r1[2], r2[2]) - max(r1[0], r2[0]); h = min(r1[3], r2[3]) - max(r1[1], r2[1])
    return max(0.0, w) * max(0.0, h)


def layout_warnings(d, cfg):
    """Coverage overlap between indoor antennas on the same floor (overlap raises the self-oscillation risk
    and wastes antennas; a little overlap at the edges is fine)."""
    warns = []
    lc = cfg.get("layout_checks") or {}
    ratio = float(lc.get("panel_overlap_warn_ratio", 0.2))
    spacing = float(lc.get("ceiling_min_spacing_ratio", 1.0))
    R = float(cfg["ceiling_antenna"]["radius_m"])
    ants = list(antenna_index(d).values())
    for i in range(len(ants)):
        for j in range(i + 1, len(ants)):
            a, b = ants[i], ants[j]
            fa, fb = geom.obj_floor(a, d), geom.obj_floor(b, d)
            if fa != fb:
                continue
            if a.get("type") == "panel" and b.get("type") == "panel":
                ra, rb = _rect_m(a, d, cfg), _rect_m(b, d, cfg)
                if not ra or not rb:
                    continue
                ov = _rect_overlap(ra, rb)
                small = min((ra[2] - ra[0]) * (ra[3] - ra[1]), (rb[2] - rb[0]) * (rb[3] - rb[1]))
                if small and ov / small > ratio:
                    warns.append(f"panels {a['id']} and {b['id']}: {100 * ov / small:.0f}% of the smaller footprint "
                                 "overlaps – overlap raises the self-oscillation risk; keep only slight edge overlap "
                                 "(move, re-aim or remove one)")
            elif a.get("type", "ceiling") != "panel" and b.get("type", "ceiling") != "panel":
                k = float(geom.floors(d)[fa]["m_per_px"])
                dist = (abs(a["pos"][0] - b["pos"][0]) ** 2 + abs(a["pos"][1] - b["pos"][1]) ** 2) ** 0.5 * k
                if dist < spacing * R:
                    warns.append(f"ceiling antennas {a['id']} and {b['id']} are only {dist:.1f} m apart (< {spacing * R:.0f} m): "
                                 "heavy overlap – spread them or drop one")
    return warns


def lint(d, cfg, results):
    errs, warns = [], []
    fl = geom.floors(d)
    ants = antenna_index(d)
    lim = cfg["antenna_output"]
    lo, hi = lim["min_dbm"], lim["max_dbm"]
    margin = float(lim.get("warn_margin_db", 1.0))
    models = {m["model"]: m for m in cfg.get("booster_models") or []}
    allowed = {b["power_dbm"] for b in cfg.get("boosters") or []}
    proj_bands = [b for b in bands(d, cfg) if b is not None]
    wired = {}

    for a in ants.values():
        if a.get("floor") and a["floor"] not in fl:
            errs.append(f"antenna {a['id']}: unknown floor {a['floor']}")

    for b in d["boosters"]:
        bid = b["id"]
        # ---- booster model / power
        if b.get("model"):
            m = models.get(b["model"])
            if not m:
                errs.append(f"[{bid}] model {b['model']} is not in booster_models of the config")
            else:
                miss = [x for x in proj_bands if x not in [int(v) for v in m.get("bands", [])]]
                if miss:
                    errs.append(f"[{bid}] model {b['model']} does not support required band(s) {miss} MHz")
                if b["power_dbm"] > float(m.get("dl_max_dbm", 1e9)):
                    errs.append(f"[{bid}] {b['power_dbm']} dBm exceeds {b['model']} max DL output {m['dl_max_dbm']} dBm")
                if m.get("power_basis", "total") == "total" and len(proj_bands) > 1 and not b.get("per_band_confirmed"):
                    errs.append(f"[{bid}] {b['model']}: {m.get('dl_max_dbm')} dBm is the TOTAL DL output. Per-band output "
                                "is not confirmed – ask the user, then set power_by_band and per_band_confirmed: true "
                                "(do not split the total evenly by yourself)")
        else:
            if models:
                warns.append(f"[{bid}] no `model` – pick a real model from the project's product table")
            if allowed and b["power_dbm"] not in allowed and not b.get("power_by_band"):
                errs.append(f"[{bid}] booster power {b['power_dbm']} dBm is not in the available list {sorted(allowed)}")

        # ---- how many antennas one unit should feed (user rule: Hi20 ≈ 6–7, Hi23 ≈ 8–9)
        n_ant = count_antennas(b["tree"])
        m = models.get(b.get("model"))
        if m and m.get("antennas_typical"):
            usual, mx = [int(x) for x in m["antennas_typical"]]
            if n_ant > mx:
                errs.append(f"[{bid}] {b['model']} feeds {n_ant} antennas – more than its maximum of {mx}; "
                            "use a stronger model or split the floors between two boosters")
            elif n_ant > usual:
                warns.append(f"[{bid}] {b['model']} feeds {n_ant} antennas – at its upper limit ({usual}–{mx}); "
                             "check the far branches carefully")

        # ---- back-and-forth wiring (来回布线): cable longer than the direct right-angle route
        max_det = float((cfg.get("layout_checks") or {}).get("max_detour_m", 1.5))
        nf0 = node_floors(b, d)

        def detours(n, floor, name):
            for port, br in branches(n):
                det = detour_m(br["path"], floor, d)
                child = br["node"]
                cname = child["id"] if child["type"] == "antenna" else f"{child['type']} {child.get('id', '')}"
                if det > max_det:
                    warns.append(f"[{bid}] {name} {port} → {cname}: {det:.1f} m of back-and-forth cable – move the "
                                 f"{'antenna' if child['type'] == 'antenna' else 'device'} or {name} so the cable "
                                 "arrives directly (no going past and coming back)")
                if child["type"] != "antenna":
                    detours(child, nf0[id(child)], f"{child['type']} {child.get('id', '')}")
        fd = detour_m(b["feed"], geom.obj_floor(b, d), d)
        if fd > max_det:
            warns.append(f"[{bid}] feed: {fd:.1f} m of back-and-forth cable – move the first device to the real branch point")
        detours(b["tree"], nf0[id(b["tree"])], f"{b['tree']['type']} {b['tree'].get('id', '')}")

        if geom.xy(b["feed"][0]) != geom.xy(b["pos"]):
            errs.append(f"[{bid}] feed must start at the booster position")
        if geom.xy(b["feed"][-1]) != geom.xy(node_pos(b["tree"], ants)):
            errs.append(f"[{bid}] feed must end at the first device / antenna")

        nf = node_floors(b, d)

        def walk(n, inpath=None):
            if n["type"] == "antenna":
                wired.setdefault(n["id"], []).append(bid)
                a = ants.get(n["id"])
                if a is None:
                    errs.append(f"[{bid}] antenna {n['id']} is not in antennas[]")
                    return
                af = a.get("floor") or geom.default_floor(d)
                if nf[id(n)] != af:
                    errs.append(f"[{bid}] cable reaches antenna {n['id']} on floor {nf[id(n)]}, but it is on floor {af}")
                if a.get("type") == "panel" and inpath is not None and a.get("aim_deg") is not None:
                    v = aim_vec(a["aim_deg"])
                    if v and last_dir(inpath) != v:
                        warns.append(f"[{bid}] panel {n['id']}: feeder should reach the panel from behind "
                                     "(last short segment in the aim direction)")
                return
            for port, br in branches(n):
                p, child = br["path"], br["node"]
                if child["type"] == "antenna" and child["id"] not in ants:
                    errs.append(f"[{bid}] antenna {child['id']} is not in antennas[]")
                    continue
                if geom.xy(p[0]) != geom.xy(n["pos"]) or geom.xy(p[-1]) != geom.xy(node_pos(child, ants)):
                    errs.append(f"[{bid}] {n['type']} {n.get('id','')} {port}: path must start at the device and end at its child")
                if float(br.get("extra_m", 0) or 0) > 0 and not br.get("extra_approved"):
                    errs.append(f"[{bid}] {n.get('id','')} {port}: extra cable {br['extra_m']} m added to burn power is not "
                                "approved – show the user the length/loss/output change, then set extra_approved: true")
                if n["type"] == "coupler" and port == "coupled" and child["type"] == "antenna" \
                        and ants[child["id"]].get("type", "ceiling") == "ceiling":
                    a = ants[child["id"]]["pos"]
                    if a[0] != n["pos"][0] and a[1] != n["pos"][1]:
                        warns.append(f"[{bid}] coupler {n.get('id','')} is not aligned with antenna {child['id']} "
                                     "(put the coupler directly above/below/beside the antenna)")
                walk(child, p)
            if n["type"] == "splitter":
                dirs = {first_dir(br["path"]) for br in n["outputs"]}
                if len(dirs) > 1:
                    warns.append(f"[{bid}] splitter {n.get('id','')}: all outputs must leave the same long side "
                                 "(first hop of every output in the same direction)")
                elif inpath is not None and last_dir(inpath) != (od := dirs.pop()):
                    hint = (" – the outputs turn back along the input: move the splitter back to where the cables "
                            "actually diverge" if last_dir(inpath) == tuple(-x for x in od) else "")
                    warns.append(f"[{bid}] splitter {n.get('id','')}: input must enter the long side opposite the outputs{hint}")
                ls = [branch_length_m(br, nf[id(n)], d)[0] for br in n["outputs"]]
                if max(ls) - min(ls) > max(8.0, 0.4 * max(ls)):
                    warns.append(f"[{bid}] splitter {n.get('id','')} outputs differ a lot ({min(ls):.0f}–{max(ls):.0f} m): "
                                 "a coupler is usually better when one branch is much longer")
            if n["type"] == "coupler" and inpath is not None:
                arrive = last_dir(inpath)
                if first_dir(n["through"]["path"]) != arrive:
                    warns.append(f"[{bid}] coupler {n.get('id','')}: through port should continue straight on from the input")
                if first_dir(n["coupled"]["path"]) in (arrive, tuple(-x for x in arrive)):
                    warns.append(f"[{bid}] coupler {n.get('id','')}: coupled port should leave at the side (90°)")
        walk(b["tree"], b["feed"])

        # ---- duplicated / parallel runs on the same floor (first hop of splitter outputs = own lane)
        pieces, _ = floor_pieces(b, d)
        segs = []
        for f, pts, split_out in pieces:
            ss = list(axis_segments(pts))
            segs.extend((f, s) for s in (ss[1:] if split_out else ss))
        seen = set()
        for i in range(len(segs)):
            for j in range(i + 1, len(segs)):
                if segs[i][0] != segs[j][0]:
                    continue
                ov = overlap_len(segs[i][1], segs[j][1]) * float(fl[segs[i][0]]["m_per_px"])
                if ov > 2.0:
                    key = (segs[i][0], round(segs[i][1][0][0]), round(segs[i][1][0][1]), round(ov))
                    if key not in seen:
                        seen.add(key)
                        warns.append(f"[{bid}] two cables run along the same line for {ov:.0f} m near {segs[i][1][0]} "
                                     "→ move the coupler/splitter to where the cables actually diverge")

        # ---- IDF rule (same floor)
        idfs = idf_list(d)
        bf = geom.obj_floor(b, d)
        same = [p for f, p in idfs if f == bf]
        if same:
            k = float(fl[bf]["m_per_px"])
            dist = min(abs(b["pos"][0] - p[0]) + abs(b["pos"][1] - p[1]) for p in same) * k
            if dist > 3 and not b.get("location_reason"):
                warns.append(f"[{bid}] booster is {dist:.0f} m from the nearest IDF; place it in the IDF unless "
                             "antennas would drop below the minimum — then add `location_reason`")

        # ---- output window, every band
        for r in results.get(bid, []):
            for bd, v in r["by_band"].items():
                tag = f" @{bd} MHz" if bd is not None else ""
                p = v["out_dbm"]
                if not output_in_window(p, cfg):
                    errs.append(f"[{bid}] antenna {r['antenna']}{tag} output {p:.2f} dBm outside strict range {lo} < P < {hi} dBm")
                elif p - lo < margin or hi - p < margin:
                    side = f"{p - lo:.2f} dB above {lo}" if p - lo < margin else f"{hi - p:.2f} dB below {hi}"
                    warns.append(f"[{bid}] antenna {r['antenna']}{tag} {p:.2f} dBm is close to the limit ({side} dBm) "
                                 "– tell the user and offer one recalculated alternative")
        if any(c.get("value") is None for c in couplers_of(b["tree"])):
            errs.append(f"[{bid}] couplers without value — run optimize")

    # ---- the stronger booster should take the group with the longest runs
    if len(d["boosters"]) > 1 and all(results.get(b["id"]) for b in d["boosters"]):
        worst = {b["id"]: max(r["total_db"] for r in results[b["id"]]) for b in d["boosters"]}
        P = {b["id"]: float(b["power_dbm"]) for b in d["boosters"]}
        for x in d["boosters"]:
            for y in d["boosters"]:
                if P[x["id"]] > P[y["id"]] and worst[x["id"]] + 0.5 < worst[y["id"]]:
                    warns.append(f"[{x['id']}/{y['id']}] the weaker booster {y['id']} ({P[y['id']]:g} dBm) has the longer "
                                 f"runs (worst loss {worst[y['id']]:.1f} dB vs {worst[x['id']]:.1f} dB) – give the stronger "
                                 "unit the group with the longer riser / runs")
    warns.extend(layout_warnings(d, cfg))

    for a in ants:
        if a not in wired:
            errs.append(f"antenna {a} is not connected to any booster")
        elif len(wired[a]) > 1:
            errs.append(f"antenna {a} is connected more than once: {wired[a]}")
    return errs, warns
