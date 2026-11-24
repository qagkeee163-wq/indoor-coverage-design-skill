"""Floors and path geometry.

A design may have one plan (`project.floorplan`, `project.m_per_px`) or several `floors`.
Path points are `[x, y]` (same floor as the previous point) or `[x, y, "FLOOR_ID"]` (switch floor).
Between two points on different floors the cable rises/drops by the elevation difference; the
x/y jump is only drawing alignment and is not counted. Within a floor, length is right-angle
(Manhattan) distance × that floor's metres-per-pixel.
"""

SINGLE = "_"


def floors(d):
    fl = d.get("floors")
    if not fl:
        p = d["project"]
        return {SINGLE: {"id": SINGLE, "floorplan": p.get("floorplan"), "m_per_px": p["m_per_px"],
                         "elevation_m": 0.0, "name": p.get("floor_name", "")}}
    return {f["id"]: f for f in fl}


def default_floor(d):
    return next(iter(floors(d)))


def xy(p):
    return (p[0], p[1])


def pt_floor(p):
    return p[2] if len(p) > 2 else None


def obj_floor(obj, d):
    return obj.get("floor") or default_floor(d)


def split_path(path, start_floor, d):
    """Return (pieces, rises, end_floor).

    pieces: list of (floor_id, [(x, y), ...]) drawn on that floor
    rises:  list of dict(from_floor, to_floor, at_from=(x,y), at_to=(x,y), length_m)
    """
    fl = floors(d)
    pieces, rises = [], []
    cur = pt_floor(path[0]) or start_floor
    piece = [xy(path[0])]
    for p in path[1:]:
        f = pt_floor(p) or cur
        if f != cur:
            if f not in fl:
                raise ValueError(f"unknown floor '{f}' in path")
            pieces.append((cur, piece))
            h = abs(float(fl[f].get("elevation_m", 0)) - float(fl[cur].get("elevation_m", 0)))
            rises.append(dict(from_floor=cur, to_floor=f, at_from=piece[-1], at_to=xy(p), length_m=h))
            cur, piece = f, [xy(p)]
        else:
            piece.append(xy(p))
    pieces.append((cur, piece))
    return pieces, rises, cur


def manhattan(pts):
    return sum(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in zip(pts, pts[1:]))


def path_length_m(path, start_floor, d):
    fl = floors(d)
    pieces, rises, end = split_path(path, start_floor, d)
    L = sum(manhattan(pts) * float(fl[f]["m_per_px"]) for f, pts in pieces)
    return L + sum(r["length_m"] for r in rises), end


def end_floor(path, start_floor, d):
    return split_path(path, start_floor, d)[2]
