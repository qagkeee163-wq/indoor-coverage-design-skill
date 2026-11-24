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


def output_in_window(power, cfg):
    limits = cfg["antenna_output"]
    return limits["min_dbm"] < power < limits["max_dbm"]


def _rank_outputs(results, cfg):
    """Rank by feasibility first, then by the previous balance score."""
    levels = [row["out_dbm"] for row in results]
    limits = cfg["antenna_output"]
    low, high = limits["min_dbm"], limits["max_dbm"]
    invalid = sum(not output_in_window(level, cfg) for level in levels)
    distance = sum(max(low - level, level - high, 0) for level in levels)
    mean = sum(levels) / len(levels)
    optimizer = cfg["optimizer"]
    spread = max(levels) - min(levels)
    mean_deviation = sum(abs(level - mean) for level in levels) / len(levels)
    quality = min(levels) - optimizer["w_spread"] * spread - optimizer["w_mad"] * mean_deviation
    return (-distance, -invalid, quality)


def optimise_booster(b, d, cfg, powers=None, fixed=True):
    """Find the lowest requested power with a feasible coupler assignment."""
    couplers = couplers_of(b["tree"])
    options = [
        [node["value"]] if node.get("lock") and node.get("value") is not None
        else sorted(cfg["couplers"])
        for node in couplers
    ]
    for power in sorted(set(powers or [b["power_dbm"]])):
        def rank(values):
            return _rank_outputs(evaluate_booster(b, d, cfg, power, list(values)), cfg)

        if len(couplers) <= cfg["optimizer"]["brute_force_max_couplers"]:
            best = max((rank(values), values) for values in itertools.product(*options))
        else:
            candidates = []
            for use_minimum in (False, True):
                values = [choices[0] if use_minimum else choices[-1] for choices in options]
                current = rank(values)
                improved = True
                while improved:
                    improved = False
                    for index, choices in enumerate(options):
                        for value in choices:
                            trial = values.copy()
                            trial[index] = value
                            candidate = rank(trial)
                            if candidate > current:
                                values = trial
                                current = candidate
                                improved = True
                candidates.append((current, tuple(values)))
            best = max(candidates)
        ranks, values = best
        if ranks[1] == 0:
            return ranks[2], power, list(values)
    return None


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
