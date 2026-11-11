"""Link-budget engine: load config + design, evaluate every antenna, optimise couplers.

Design coordinates are pixels of the floor-plan image; `project.m_per_px` converts to metres.
All cable lengths use right-angle (Manhattan) routing.
"""
import copy
import itertools
import json
import os

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(HERE, "..", "..", "config", "equipment.yaml")


def load_config(path=None):
    with open(path or DEFAULT_CONFIG, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    cfg["couplers"] = {int(k): v for k, v in cfg["couplers"].items()}
    cfg["splitters"] = {int(k): v for k, v in cfg["splitters"].items()}
    return cfg


def load_design(path):
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    d["_path"] = os.path.abspath(path)
    d["_dir"] = os.path.dirname(d["_path"])
    return d


def save_design(d, path=None):
    out = {k: v for k, v in d.items() if not k.startswith("_")}
    with open(path or d["_path"], "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)


def manhattan(pts):
    return sum(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in zip(pts, pts[1:]))


def antenna_index(d):
    return {a["id"]: a for a in d.get("antennas", [])}


def node_pos(n, ants):
    if n["type"] == "antenna":
        return ants[n["id"]]["pos"]
    return n["pos"]


def branches(n):
    """Yield (port_name, branch) for every outgoing branch of a device node."""
    if n["type"] == "coupler":
        yield "coupled", n["coupled"]
        yield "through", n["through"]
    elif n["type"] == "splitter":
        for i, b in enumerate(n["outputs"]):
            yield f"out{i + 1}", b


def couplers_of(n, acc=None):
    acc = [] if acc is None else acc
    if n["type"] == "coupler":
        acc.append(n)
    for _, b in branches(n):
        couplers_of(b["node"], acc)
    return acc


def evaluate_booster(b, d, cfg, power=None, values=None):
    """Return list of per-antenna results for one booster.

    values: optional list of coupler values in DFS order (overrides node['value']).
    """
    P = b["power_dbm"] if power is None else power
    ants = antenna_index(d)
    k = d["project"]["m_per_px"]
    loss = cfg["cable"]["loss_db_per_100m"] / 100.0
    cps = couplers_of(b["tree"])
    vals = values if values is not None else [c.get("value") for c in cps]
    vmap = {id(c): v for c, v in zip(cps, vals)}
    res = []

    def go(n, dev, L, path):
        if n["type"] == "antenna":
            Lt = L + cfg["cable"]["slack_per_antenna_m"]
            cable = Lt * loss
            res.append(dict(antenna=n["id"], pos=ants[n["id"]]["pos"], length_m=Lt, cable_db=cable,
                            device_db=dev, total_db=cable + dev, out_dbm=P - dev - cable, path=path))
            return
        if n["type"] == "coupler":
            v = vmap[id(n)]
            spec = cfg["couplers"][int(v)]
            go(n["coupled"]["node"], dev + spec["coupled"], L + manhattan(n["coupled"]["path"]) * k,
               path + [("coupler", int(v), "coupled", spec["coupled"])])
            go(n["through"]["node"], dev + spec["through"], L + manhattan(n["through"]["path"]) * k,
               path + [("coupler", int(v), "through", spec["through"])])
        elif n["type"] == "splitter":
            ways = len(n["outputs"])
            sl = cfg["splitters"][ways]["loss"]
            for br in n["outputs"]:
                go(br["node"], dev + sl, L + manhattan(br["path"]) * k, path + [("splitter", ways, "", sl)])
        else:
            raise ValueError(f"unknown node type {n['type']}")

    go(b["tree"], 0.0, cfg["cable"]["riser_m"] + manhattan(b["feed"]) * k, [])
    return res


def score(res, cfg):
    ps = [r["out_dbm"] for r in res]
    if round(max(ps), 1) > cfg["antenna_output"]["max_dbm"]:
        return None
    mu = sum(ps) / len(ps)
    o = cfg["optimizer"]
    return min(ps) - o["w_spread"] * (max(ps) - min(ps)) - o["w_mad"] * sum(abs(p - mu) for p in ps) / len(ps)


def optimise_booster(b, d, cfg, powers=None, fixed=True):
    """Pick coupler values (and power if powers given) maximising the score.

    Couplers whose node has "lock": true keep their value.
    Returns (score, power, values) or None if no combination respects max_dbm.
    """
    cps = couplers_of(b["tree"])
    opts = [[c["value"]] if c.get("lock") and c.get("value") else sorted(cfg["couplers"]) for c in cps]
    powers = powers or [b["power_dbm"]]
    best = None
    for P in powers:
        if len(cps) <= cfg["optimizer"]["brute_force_max_couplers"]:
            for vals in itertools.product(*opts):
                s = score(evaluate_booster(b, d, cfg, P, list(vals)), cfg)
                if s is not None and (best is None or s > best[0]):
                    best = (s, P, list(vals))
        else:  # coordinate descent from all-10 dB (lowest through loss, safest start is all-5? try both)
            for start in (max(cfg["couplers"]), min(cfg["couplers"])):
                vals = [o[0] if len(o) == 1 else start for o in opts]
                cur = score(evaluate_booster(b, d, cfg, P, vals), cfg)
                improved = True
                while improved:
                    improved = False
                    for i, o in enumerate(opts):
                        for v in o:
                            t = vals[:]; t[i] = v
                            s = score(evaluate_booster(b, d, cfg, P, t), cfg)
                            if s is not None and (cur is None or s > cur + 1e-9):
                                vals, cur, improved = t, s, True
                if cur is not None and (best is None or cur > best[0]):
                    best = (cur, P, vals)
    return best


def apply_values(b, vals):
    for c, v in zip(couplers_of(b["tree"]), vals):
        c["value"] = int(v)


def evaluate_all(d, cfg):
    out = {}
    for b in d["boosters"]:
        if any(c.get("value") is None for c in couplers_of(b["tree"])):
            raise ValueError(f"Booster {b['id']}: some couplers have no value; run `optimize` first")
        out[b["id"]] = evaluate_booster(b, d, cfg)
    return out


def device_counts(n, acc=None):
    from collections import Counter
    acc = Counter() if acc is None else acc
    if n["type"] == "coupler":
        acc[("coupler", int(n["value"]))] += 1
    elif n["type"] == "splitter":
        acc[("splitter", len(n["outputs"]))] += 1
    for _, br in branches(n):
        device_counts(br["node"], acc)
    return acc


def all_segments(b, d):
    """Every drawn polyline of a booster: feed + each branch path (in px)."""
    segs = [b["feed"]]

    def walk(n):
        for _, br in branches(n):
            segs.append(br["path"])
            walk(br["node"])
    walk(b["tree"])
    return segs


def count_antennas(n):
    if n["type"] == "antenna":
        return 1
    return sum(count_antennas(br["node"]) for _, br in branches(n))


def deep(x):
    return copy.deepcopy(x)
