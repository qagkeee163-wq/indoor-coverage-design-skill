"""Link-budget engine: load config + design, evaluate every antenna in every band, optimise couplers.

Lengths: right-angle routing per floor (geom.py) + real vertical rises + riser + slack + approved extra.
Cable loss can be one value or one value per band (MHz). Every band is checked.
"""
import copy
import itertools
import json
import os

import yaml

from . import geom
from .geom import manhattan, xy  # noqa: F401  (re-exported for older callers)

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(HERE, "..", "..", "config", "equipment.yaml")


class ConfigError(ValueError):
    pass


# ------------------------------------------------------------------ loading
def load_config(path=None):
    with open(path or DEFAULT_CONFIG, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    cfg["couplers"] = {int(k): v for k, v in cfg["couplers"].items()}
    cfg["splitters"] = {int(k): v for k, v in cfg["splitters"].items()}
    loss = cfg["cable"]["loss_db_per_100m"]
    if isinstance(loss, dict):
        cfg["cable"]["loss_db_per_100m"] = {int(k): v for k, v in loss.items()}
    cfg["_path"] = os.path.abspath(path or DEFAULT_CONFIG)
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


# ------------------------------------------------------------------ bands & loss
def bands(d, cfg):
    """Bands to check. None = the single band the config's scalar loss refers to."""
    b = d.get("project", {}).get("bands")
    if b:
        return [int(x) for x in b]
    loss = cfg["cable"]["loss_db_per_100m"]
    if isinstance(loss, dict):
        return sorted(loss)
    return [None]


def loss_rate(cfg, band):
    """dB per metre for this band."""
    loss = cfg["cable"]["loss_db_per_100m"]
    name = cfg["cable"].get("name", "cable")
    if isinstance(loss, dict):
        if band is None:
            raise ConfigError(f"{name}: per-band loss table needs project.bands")
        v = loss.get(int(band))
        if v is None:
            raise ConfigError(f"{name}: loss at {band} MHz is not set in {os.path.basename(cfg.get('_path',''))} "
                              "– get the real datasheet value from the user")
        return float(v) / 100.0
    return float(loss) / 100.0


def ref_band(d, cfg):
    """Band shown in single-value tables: project.design_band, else the band with the highest loss."""
    bs = bands(d, cfg)
    db = d.get("project", {}).get("design_band")
    if db:
        return int(db)
    if bs == [None]:
        return None
    return max(bs, key=lambda b: loss_rate(cfg, b))


def booster_power(b, band, power=None):
    pb = b.get("power_by_band") or {}
    if band is not None and (str(band) in pb or band in pb):
        return float(pb.get(str(band), pb.get(band)))
    return float(b["power_dbm"] if power is None else power)


# ------------------------------------------------------------------ tree helpers
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


def branch_length_m(br, start_floor, d):
    L, end = geom.path_length_m(br["path"], start_floor, d)
    return L + float(br.get("extra_m", 0) or 0), end


# ------------------------------------------------------------------ evaluation
def evaluate_booster(b, d, cfg, power=None, values=None):
    """Per-antenna results for one booster, every band.

    values: optional coupler values in DFS order (overrides node['value']).
    Each result: antenna, pos, floor, length_m, extra_m, device_db, path,
                 by_band {band: {cable_db, total_db, out_dbm}}, plus cable_db/total_db/out_dbm of ref band.
    """
    ants = antenna_index(d)
    c = cfg["cable"]
    bs = bands(d, cfg)
    rates = {bd: loss_rate(cfg, bd) for bd in bs}
    rb = ref_band(d, cfg)
    cps = couplers_of(b["tree"])
    vals = values if values is not None else [n.get("value") for n in cps]
    vmap = {id(n): v for n, v in zip(cps, vals)}
    res = []

    def go(n, dev, L, extra, path, floor):
        if n["type"] == "antenna":
            Lt = L + c["slack_per_antenna_m"]
            by = {}
            for bd in bs:
                cable = Lt * rates[bd]
                by[bd] = dict(cable_db=cable, total_db=cable + dev, out_dbm=booster_power(b, bd, power) - dev - cable)
            r = dict(antenna=n["id"], pos=ants[n["id"]]["pos"], floor=floor, length_m=Lt, extra_m=extra,
                     device_db=dev, path=path, by_band=by)
            r.update(by[rb])
            res.append(r)
            return
        if n["type"] == "coupler":
            v = vmap[id(n)]
            if v is None:
                raise ConfigError(f"Booster {b['id']}: coupler {n.get('id','')} has no value – run optimize")
            spec = cfg["couplers"][int(v)]
            for port, key in (("coupled", "coupled"), ("through", "through")):
                br = n[port]
                bl, ef = branch_length_m(br, floor, d)
                go(br["node"], dev + spec[key], L + bl, extra + float(br.get("extra_m", 0) or 0),
                   path + [("coupler", int(v), port, spec[key])], ef)
        elif n["type"] == "splitter":
            ways = len(n["outputs"])
            sl = cfg["splitters"][ways]["loss"]
            for br in n["outputs"]:
                bl, ef = branch_length_m(br, floor, d)
                go(br["node"], dev + sl, L + bl, extra + float(br.get("extra_m", 0) or 0),
                   path + [("splitter", ways, "", sl)], ef)
        else:
            raise ValueError(f"unknown node type {n['type']}")

    f0 = geom.obj_floor(b, d)
    feedL, ff = geom.path_length_m(b["feed"], f0, d)
    go(b["tree"], 0.0, c["riser_m"] + feedL, 0.0, [], ff)
    return res


def evaluate_all(d, cfg):
    return {b["id"]: evaluate_booster(b, d, cfg) for b in d["boosters"]}


def all_outputs(res):
    return [v["out_dbm"] for r in res for v in r["by_band"].values()]


def output_in_window(power, cfg):
    lim = cfg["antenna_output"]
    return lim["min_dbm"] < power < lim["max_dbm"]


def feasible_window(res, cfg):
    """Booster output window (lo, hi) per band that keeps every antenna strictly inside the limits.

    With total loss L_i per antenna: lo = max(L_i) + min_dbm, hi = min(L_i) + max_dbm (both open).
    """
    lim = cfg["antenna_output"]
    out = {}
    bs = list(res[0]["by_band"]) if res else []
    for bd in bs:
        Ls = [r["by_band"][bd]["total_db"] for r in res]
        out[bd] = (max(Ls) + lim["min_dbm"], min(Ls) + lim["max_dbm"])
    return out


# ------------------------------------------------------------------ optimiser
def _rank_outputs(results, cfg):
    """Rank by feasibility first, then by balance (higher is better)."""
    levels = all_outputs(results)
    lim = cfg["antenna_output"]
    low, high = lim["min_dbm"], lim["max_dbm"]
    invalid = sum(not output_in_window(x, cfg) for x in levels)
    distance = sum(max(low - x, x - high, 0) for x in levels)
    mean = sum(levels) / len(levels)
    o = cfg["optimizer"]
    spread = max(levels) - min(levels)
    mad = sum(abs(x - mean) for x in levels) / len(levels)
    quality = min(levels) - o["w_spread"] * spread - o["w_mad"] * mad
    return (-distance, -invalid, quality)


def optimise_booster(b, d, cfg, powers=None):
    """Lowest requested power with a feasible coupler assignment → (quality, power, values) or None."""
    cps = couplers_of(b["tree"])
    options = [[n["value"]] if n.get("lock") and n.get("value") is not None else sorted(cfg["couplers"]) for n in cps]
    for power in sorted(set(powers or [b["power_dbm"]])):
        def rank(values):
            return _rank_outputs(evaluate_booster(b, d, cfg, power, list(values)), cfg)

        if len(cps) <= cfg["optimizer"]["brute_force_max_couplers"]:
            best = max((rank(v), tuple(v)) for v in itertools.product(*options))
        else:
            cands = []
            for use_min in (False, True):
                values = [ch[0] if use_min else ch[-1] for ch in options]
                cur = rank(values)
                improved = True
                while improved:
                    improved = False
                    for i, ch in enumerate(options):
                        for v in ch:
                            t = values.copy(); t[i] = v
                            r = rank(t)
                            if r > cur:
                                values, cur, improved = t, r, True
                cands.append((cur, tuple(values)))
            best = max(cands)
        ranks, values = best
        if ranks[1] == 0:
            return ranks[2], power, list(values)
    return None


def apply_values(b, vals):
    for n, v in zip(couplers_of(b["tree"]), vals):
        n["value"] = int(v)


# ------------------------------------------------------------------ counting
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


def all_branches(b):
    """Every physical cable of a booster: the feed plus each branch (list of dicts with 'path')."""
    out = [{"path": b["feed"], "_feed": True}]

    def walk(n):
        for _, br in branches(n):
            out.append(br)
            walk(br["node"])
    walk(b["tree"])
    return out


def all_segments(b, d=None):
    """Raw polylines (feed + branches). Kept for older callers."""
    return [br["path"] for br in all_branches(b)]


def floor_pieces(b, d):
    """[(floor, [(x,y)...], is_splitter_output)], [rises] for drawing and lint."""
    pieces, rises = [], []

    def add(path, floor, split_out=False):
        ps, rs, end = geom.split_path(path, floor, d)
        for i, (f, pts) in enumerate(ps):
            pieces.append((f, pts, split_out and i == 0))
        rises.extend(rs)
        return end

    f0 = geom.obj_floor(b, d)
    ff = add(b["feed"], f0)

    def walk(n, floor):
        for _, br in branches(n):
            ef = add(br["path"], floor, n["type"] == "splitter")
            walk(br["node"], ef)
    walk(b["tree"], ff)
    return pieces, rises


def node_floors(b, d):
    """{id(node): floor} for every node of the tree."""
    out = {}
    f0 = geom.obj_floor(b, d)
    ff = geom.end_floor(b["feed"], f0, d)

    def walk(n, floor):
        out[id(n)] = floor
        for _, br in branches(n):
            walk(br["node"], geom.end_floor(br["path"], floor, d))
    walk(b["tree"], ff)
    return out


def count_antennas(n):
    if n["type"] == "antenna":
        return 1
    return sum(count_antennas(br["node"]) for _, br in branches(n))


def deep(x):
    return copy.deepcopy(x)
