"""Design-rule checks. Each rule comes from a real correction made during design reviews."""
from .engine import antenna_index, branches, node_pos, manhattan, all_segments, couplers_of


def expand(pts):
    """Same expansion the renderer uses: a diagonal hop is drawn horizontal-first."""
    q = [tuple(pts[0])]
    for a in pts[1:]:
        b = q[-1]
        if a[0] != b[0] and a[1] != b[1]:
            q.append((a[0], b[1]))
        q.append(tuple(a))
    return q


def first_dir(pts):
    q = expand(pts)
    for a, b in zip(q, q[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        if dx or dy:
            return ((dx > 0) - (dx < 0), (dy > 0) - (dy < 0))
    return (0, 0)


def axis_segments(pts):
    q = expand(pts)
    for a, b in zip(q, q[1:]):
        if a != b:
            yield a, b


def overlap_len(s1, s2):
    (a1, b1), (a2, b2) = s1, s2
    if a1[1] == b1[1] == a2[1] == b2[1]:   # same horizontal line
        lo1, hi1 = sorted((a1[0], b1[0])); lo2, hi2 = sorted((a2[0], b2[0]))
        return max(0, min(hi1, hi2) - max(lo1, lo2))
    if a1[0] == b1[0] == a2[0] == b2[0]:   # same vertical line
        lo1, hi1 = sorted((a1[1], b1[1])); lo2, hi2 = sorted((a2[1], b2[1]))
        return max(0, min(hi1, hi2) - max(lo1, lo2))
    return 0


def lint(d, cfg, results):
    errs, warns = [], []
    k = d["project"]["m_per_px"]
    ants = antenna_index(d)
    lo, hi = cfg["antenna_output"]["min_dbm"], cfg["antenna_output"]["max_dbm"]
    allowed = {b["power_dbm"] for b in cfg["boosters"]}
    wired = {}

    for b in d["boosters"]:
        bid = b["id"]
        if b["power_dbm"] not in allowed:
            errs.append(f"[{bid}] booster power {b['power_dbm']} dBm is not in the allowed list {sorted(allowed)}")
        # one cable out of the booster
        if tuple(b["feed"][0]) != tuple(b["pos"]):
            errs.append(f"[{bid}] feed must start at the booster position")
        if tuple(b["feed"][-1]) != tuple(node_pos(b["tree"], ants)):
            errs.append(f"[{bid}] feed must end at the first device / antenna")

        def walk(n, inpath=None):
            if n["type"] == "antenna":
                wired.setdefault(n["id"], []).append(bid)
                return
            for port, br in branches(n):
                p, child = br["path"], br["node"]
                if tuple(p[0]) != tuple(n["pos"]) or tuple(p[-1]) != tuple(node_pos(child, ants)):
                    errs.append(f"[{bid}] {n['type']} {n.get('id','')} {port}: path must start at the device and end at its child")
                if n["type"] == "coupler" and port == "coupled" and child["type"] == "antenna":
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
                elif inpath is not None and first_dir(list(reversed(inpath))) != tuple(-x for x in dirs.pop()):
                    warns.append(f"[{bid}] splitter {n.get('id','')}: input must enter the long side opposite the outputs")
            if n["type"] == "coupler" and inpath is not None:
                arrive = tuple(-x for x in first_dir(list(reversed(inpath))))
                if first_dir(n["through"]["path"]) != arrive:
                    warns.append(f"[{bid}] coupler {n.get('id','')}: through port should continue straight on from the input")
                if first_dir(n["coupled"]["path"]) in (arrive, tuple(-x for x in arrive)):
                    warns.append(f"[{bid}] coupler {n.get('id','')}: coupled port should leave at the side (90°)")
            if n["type"] == "splitter":
                ls = [manhattan(br["path"]) * k for br in n["outputs"]]
                if max(ls) - min(ls) > max(8.0, 0.4 * max(ls)):
                    warns.append(f"[{bid}] splitter {n.get('id','')} outputs differ a lot ({min(ls):.0f}–{max(ls):.0f} m): "
                                 "a coupler is usually better when one branch is much longer")
        walk(b["tree"], b["feed"])

        # duplicated / parallel runs (same booster). The first hop of each splitter output is drawn
        # as its own parallel lane, so it is excluded.
        segs = []
        skip = set()

        def mark(n):
            if n["type"] == "splitter":
                for br in n["outputs"]:
                    skip.add(id(br["path"]))
            for _, br in branches(n):
                mark(br["node"])
        mark(b["tree"])
        for poly in all_segments(b, d):
            ss = list(axis_segments(poly))
            segs.extend(ss[1:] if id(poly) in skip else ss)
        seen = set()
        for i in range(len(segs)):
            for j in range(i + 1, len(segs)):
                ov = overlap_len(segs[i], segs[j]) * k
                if ov > 2.0:
                    key = (round(segs[i][0][0]), round(segs[i][0][1]), round(ov))
                    if key not in seen:
                        seen.add(key)
                        warns.append(f"[{bid}] two cables run along the same line for {ov:.0f} m near {segs[i][0]} "
                                     "→ move the coupler/splitter to where the cables actually diverge")

        # IDF rule
        idfs = d.get("idf", [])
        if idfs:
            dist = min(abs(b["pos"][0] - p[0]) + abs(b["pos"][1] - p[1]) for p in idfs) * k
            if dist > 3 and not b.get("location_reason"):
                warns.append(f"[{bid}] booster is {dist:.0f} m from the nearest IDF; place it in the IDF unless "
                             "antennas would drop below the minimum — then add `location_reason`")

        for r in results.get(bid, []):
            p = round(r["out_dbm"], 1)
            if p > hi:
                errs.append(f"[{bid}] antenna {r['antenna']} output {p} dBm > {hi} dBm")
            if p < lo:
                errs.append(f"[{bid}] antenna {r['antenna']} output {p} dBm < {lo} dBm")
        if any(c.get("value") is None for c in couplers_of(b["tree"])):
            errs.append(f"[{bid}] couplers without value — run optimize")

    for a in ants:
        if a not in wired:
            errs.append(f"antenna {a} is not connected to any booster")
        elif len(wired[a]) > 1:
            errs.append(f"antenna {a} is connected more than once: {wired[a]}")
    return errs, warns
