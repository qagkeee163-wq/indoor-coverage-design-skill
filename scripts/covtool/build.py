"""Helpers for writing design trees in Python instead of raw JSON.

    from covtool.build import ant, coupler, splitter, row
"""


def ant(i):
    return {"type": "antenna", "id": i}


def coupler(cid, pos, coupled_path, coupled_node, through_path, through_node, value=None, lock=False):
    n = {"type": "coupler", "id": cid, "pos": list(pos), "value": value,
         "coupled": {"path": [list(p) for p in coupled_path], "node": coupled_node},
         "through": {"path": [list(p) for p in through_path], "node": through_node}}
    if lock:
        n["lock"] = True
    return n


def splitter(sid, pos, outputs, orient=None):
    """outputs: list of (path, node)."""
    n = {"type": "splitter", "id": sid, "pos": list(pos),
         "outputs": [{"path": [list(p) for p in pa], "node": nd} for pa, nd in outputs]}
    if orient:
        n["orient"] = orient
    return n


def row(ids, coords, line, ant_coord, horizontal=True):
    """Chain of couplers along a cable line parallel to a row of antennas.

    ids        antenna ids, ordered from the feed end to the far end
    coords     their x (horizontal row) or y (vertical row), same order
    line       y (or x) of the cable line, a few metres off the antenna row
    ant_coord  y (or x) of the antennas
    Couplers sit on the line at each antenna except the last; the last antenna takes the final through.
    """
    P = (lambda a, b: [a, b]) if horizontal else (lambda a, b: [b, a])
    node = ant(ids[-1])
    for i in range(len(ids) - 2, -1, -1):
        c, nc = coords[i], coords[i + 1]
        through = [P(c, line), P(nc, line)] + ([P(nc, ant_coord)] if i == len(ids) - 2 else [])
        node = coupler("c" + ids[i], P(c, line), [P(c, line), P(c, ant_coord)], ant(ids[i]), through, node)
    return node
