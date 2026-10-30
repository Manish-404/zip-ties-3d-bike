# -*- coding: utf-8 -*-
"""Pack several print coils onto one build plate (numpy + scipy, no FreeCAD needed).

Every coil is printed on edge, so its footprint on the bed is the plan outline of
its wall. Each coil is rasterised to a 1 mm grid, grown by half the clearance, and
placed bottom-left first at the best of several rotations. A coil may sit inside
the empty middle of another one, as long as the clearance holds.

Default plate: Markforged X7 (330 x 270 x 200 mm), 5 mm kept free round the edge.
"""
import math

import numpy as np
from scipy.ndimage import binary_dilation
from scipy.signal import fftconvolve

BED = (330.0, 270.0, 200.0)   # mm, X7 build volume
MARGIN = 5.0                  # mm kept free at the plate edge
CLEAR = 4.0                   # mm between parts (twice the dilation)
CELL = 1.0                    # mm per raster cell
ROTS = 24                     # trial rotations per coil (every 15 deg)


def _disk(r):
    n = int(math.ceil(r))
    yy, xx = np.mgrid[-n:n + 1, -n:n + 1]
    return (xx * xx + yy * yy) <= r * r


def raster(V, T, rot=0.0, clear=CLEAR, cell=CELL):
    """Plan outline of a mesh rotated by `rot` about its centre, as a boolean grid grown by
    clear / 2. Returns (grid, origin_xy, centre_xy): grid[j, i] covers
    x = origin_x + i * cell, y = origin_y + j * cell of the rotated, centred mesh."""
    xy = V[:, :2]
    c = (xy.min(axis=0) + xy.max(axis=0)) / 2.0
    ca, sa = math.cos(rot), math.sin(rot)
    q = (xy - c) @ np.array([[ca, sa], [-sa, ca]])
    a, b, d = q[T[:, 0]], q[T[:, 1]], q[T[:, 2]]
    pts = []
    for p0, p1 in ((a, b), (b, d), (d, a)):
        n = np.maximum(1, np.ceil(np.linalg.norm(p1 - p0, axis=1) / (cell * 0.5)).astype(int))
        for k in range(int(n.max()) + 1):
            sel = n >= k
            pts.append(p0[sel] + (p1[sel] - p0[sel]) * (k / n[sel])[:, None])
    pts = np.concatenate(pts)
    pad = int(math.ceil(clear / 2.0 / cell)) + 2
    lo = np.floor(pts.min(axis=0) / cell).astype(int) - pad
    hi = np.ceil(pts.max(axis=0) / cell).astype(int) + pad
    g = np.zeros((hi[1] - lo[1] + 1, hi[0] - lo[0] + 1), dtype=bool)
    ij = np.floor(pts / cell).astype(int) - lo
    g[ij[:, 1], ij[:, 0]] = True
    g = binary_dilation(g, structure=_disk(clear / 2.0 / cell))
    return g, lo * cell, c


def pack(items, bed=BED, margin=MARGIN, clear=CLEAR, rots=ROTS, strategy="bl", seed=0, stop_on_fail=True):
    """items: list of (V, T) print coils (z = 0 at the bed). Places them in order.
    strategy: "bl" bottom-left, "lb" left-bottom, "rand" a random free spot (seeded).
    Returns a list of dict(index, rot, centre, shift) for every item that fits (shift moves the
    mesh to its plate position after rotating about its own centre), and the list of item
    indices that did not fit. With stop_on_fail the first item that does not fit ends the run
    (right for identical items; pass False for a mixed list)."""
    W, H = int(round(bed[0] - 2 * margin)), int(round(bed[1] - 2 * margin))
    occ = np.zeros((H, W), dtype=bool)
    rng = np.random.RandomState(seed)
    placed, skipped, cache = [], [], {}
    angles = [2 * math.pi * k / rots for k in range(rots)]
    for idx, (V, T) in enumerate(items):
        best = None
        for ang in angles:
            ck = (id(V), ang)
            if ck not in cache:
                cache[ck] = raster(V, T, ang, clear)
            g, org, c = cache[ck]
            gh, gw = g.shape
            if gh > H or gw > W:
                continue
            hit = fftconvolve(occ.astype(float), g[::-1, ::-1].astype(float), mode="valid")
            ok = np.argwhere(hit < 0.5)           # (row, col) offsets of the grid's corner
            if len(ok) == 0:
                continue
            if strategy == "rand":
                r, cidx = ok[rng.randint(len(ok))]
                key = rng.rand()
            elif strategy == "lb":
                r, cidx = ok[np.lexsort((ok[:, 0], ok[:, 1]))[0]]
                key = (cidx + gw, r + gh)
            else:
                r, cidx = ok[np.lexsort((ok[:, 1], ok[:, 0]))[0]]
                key = (r + gh, cidx + gw)
            if best is None or key < best[0]:
                best = (key, ang, g, org, c, r, cidx)
        if best is None:
            skipped.extend(range(idx, len(items)) if stop_on_fail else [idx])
            if stop_on_fail:
                break
            continue
        _, ang, g, org, c, r, cidx = best
        occ[r:r + g.shape[0], cidx:cidx + g.shape[1]] |= g
        # rotated-centred mesh coordinate (org + index * cell) -> plate coordinate (margin + index * cell)
        shift = np.array([margin + cidx * CELL, margin + r * CELL]) - org
        placed.append(dict(index=idx, rot=ang, centre=c, shift=shift))
    return placed, skipped


def place(V, rot, centre, shift):
    """Move a mesh to its plate position (same transform `pack` assumed)."""
    ca, sa = math.cos(rot), math.sin(rot)
    out = V.copy()
    out[:, :2] = (V[:, :2] - centre) @ np.array([[ca, sa], [-sa, ca]]) + shift
    return out


def build_plate(items, bed=BED, margin=MARGIN, clear=CLEAR, tries=6, stop_on_fail=True):
    """Pack (best of bottom-left, left-bottom and `tries` random layouts) and merge.
    Returns (V, T, placements, skipped) with all placed coils in one mesh."""
    runs = [pack(items, bed, margin, clear, strategy=st, stop_on_fail=stop_on_fail) for st in ("bl", "lb")]
    runs += [pack(items, bed, margin, clear, strategy="rand", seed=k, stop_on_fail=stop_on_fail) for k in range(tries)]
    placed, skipped = max(runs, key=lambda r: len(r[0]))
    Vs, Ts, off = [], [], 0
    for p in placed:
        V, T = items[p["index"]]
        Vs.append(place(V, p["rot"], p["centre"], p["shift"]))
        Ts.append(T + off)
        off += len(V)
    if not Vs:
        return None, None, placed, skipped
    return np.concatenate(Vs), np.concatenate(Ts), placed, skipped


def min_gap(Vplate, Tplate, placed, items):
    """Smallest distance between two different coils on the plate (mm), from surface vertices."""
    from scipy.spatial import cKDTree
    n = [len(items[p["index"]][0]) for p in placed]
    ends = np.cumsum([0] + n)
    best = np.inf
    for i in range(len(placed)):
        tree = cKDTree(Vplate[ends[i]:ends[i + 1]])
        for j in range(i + 1, len(placed)):
            d, _ = tree.query(Vplate[ends[j]:ends[j + 1]], k=1)
            best = min(best, float(d.min()))
    return None if not np.isfinite(best) else best
