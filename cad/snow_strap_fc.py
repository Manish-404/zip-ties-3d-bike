# -*- coding: utf-8 -*-
"""Snow-traction strap for the Royal Enfield Hunter 350: parametric FreeCAD model.

A one-piece, zip-tie style anti-skid strap that wraps the tyre and rim through
the wheel. It combines the 2026-10-23 strap (wedge-locking two-tooth pawl,
thick root, FDM-friendly teeth) with the production spec (stepped filleted
lugs, oval flex dishes, tyre-side micro-ribs, 45 deg ramps, 90 deg stops,
0.5 mm channel tolerance, entry chamfer, rounded tip, gradual ramps).

Run it either way:
  * FreeCAD GUI: Macro > Macros... > (this file) > Execute. Builds a document
    with parametric REAR / FRONT / COUPON straps. Edit any property in the
    Property view and recompute.
  * Headless: "D:\\Software\\FreeCAD\\bin\\freecadcmd.exe" snow_strap_fc.py
    Writes STEP, STL, the print-ready coil STL, an .FCStd and info.json to
    ../out (or to the folder in the STRAP_OUT environment variable).

Axes of the straight model (mm):
  s / x  along the strap. The head sits at s < 0 with its front face at s = 0.
  y      across the strap. Every section shares one straight edge at y = -11.
         That edge goes on the bed when the strap is printed on edge.
  z      thickness. z = 0 is the tyre side; teeth and lugs face +z (outside).
"""

import json
import math
import os
import sys

import FreeCAD as App
import Part

# --------------------------------------------------------------------------
# Parameters
# --------------------------------------------------------------------------
BASE = dict(
    # overall
    total_len=600.0,        # head back face to tip
    y_bed=-11.0,            # shared straight edge of all sections
    W=15.0,                 # strap width (neck, toothed strap)
    # head (flat-layout z is the head height)
    H=15.0,
    head_W=22.0,
    wall_back=3.0,
    wall_front=3.0,
    wall_side=3.5,          # only on +y; the -y side is open (bed side)
    floor_h=2.4,
    clear_side=0.5,         # slot clearance per side, across the strap
    entry_clear=0.5,        # slot clearance over strap thickness incl. teeth
    entry_chamfer=0.8,      # 45 deg lead-in chamfer around the slot entry
    core_clear=0.35,        # pawl tip to strap core (engagement = tooth_h - this)
    pawl_back_gap=2.4,      # free space behind the pawl at its top
    pawl_t_top=2.2,         # pawl thickness behind the tooth valleys
    pawl_teeth=2,
    pawl_tip_flat=0.15,
    pawl_top_drop=0.4,      # pawl top below the head top
    pawl_top_gap=1.0,       # gap between pawl and +y wall (bridge sag room)
    pawl_back_lean=5.4,     # deg, back face lean toward the strap
    pawl_root_r=0.8,        # root fillets, both sides
    pawl_root_margin=1.0,   # floor left between pawl front root and slot edge
    pawl_shelf_r=0.2,       # fillet where a shelf meets the pawl body
    root_h=10.5,            # root gusset height at the head front face
    root_len=17.0,          # root gusset ramps down to T_neck over this length
    # strap body
    T_neck=3.0,
    band_start=40.0,        # s where the full-width tread band starts
    inramp_len=8.0,
    T_band=4.0,
    W_band=22.0,
    n_lugs=7,
    lug_pitch=20.0,
    lug_len1=9.0,           # lower tier length along the strap
    lug_h1=3.5,
    lug_len2=4.5,           # upper tier length along the strap
    lug_h2=3.0,
    r_lug_base=1.5,
    r_lug_top1=0.8,
    r_lug_step=0.6,
    r_lug_top2=1.2,
    dish_every=1,           # 1 = a dish in every gap, 2 = alternating gaps
    dish_len=6.4,
    dish_w=16.0,
    dish_depth=1.0,
    dish_C=4.0,             # ellipsoid depth semi-axis (sets the dish slope)
    rib_n=5,
    rib_pitch=4.0,
    rib_w=1.2,
    rib_depth=0.5,
    flange_len=14.0,
    T_core=2.4,
    tooth_h=1.2,
    pitch=2.0,
    tooth_crest=0.4,
    tooth_ramp_deg=45.0,
    tooth_root_r=0.2,
    tooth_valley_r=0.3,
    tip_len=35.0,
    tip_W=7.0,
    tip_T=1.8,
    # print coil (on edge)
    coil_rho0=62.0,         # neutral-axis radius where the coil starts
    coil_gap=2.0,           # clear gap between turns
    coil_rigid=22.0,        # head + root up to this s stay straight
)

PRESETS = {
    # 140/70-17 (Metro) and 120/80-17 (Retro) rear tyres
    "REAR": dict(total_len=600.0, n_lugs=7, band_start=40.0),
    # 110/70-17 (Metro) and 100/80-17 (Retro) front tyres
    "FRONT": dict(total_len=520.0, n_lugs=5, band_start=32.0),
    # short piece to test the lock before printing full straps
    "COUPON": dict(total_len=230.0, n_lugs=2, band_start=32.0),
}

INT_PARAMS = {"pawl_teeth", "n_lugs", "dish_every", "rib_n"}

DENSITY = {"PA12": 1.01, "PA6": 1.14, "PA12_SLS": 0.95}  # g/cm3


def params(preset="REAR", **over):
    P = dict(BASE)
    P.update(PRESETS[preset])
    P.update(over)
    P["preset"] = preset
    return P


# --------------------------------------------------------------------------
# 2D helpers
# --------------------------------------------------------------------------
def rounded_wire(pts, radii, to3d):
    """Closed polygon with per-vertex fillet radii -> Part.Wire.

    A positive radius at a convex vertex rounds it off; at a concave vertex the
    same arc adds material, so root fillets come for free. Fillets that would
    overlap on a short edge are shrunk to fit.
    """
    n = len(pts)
    P = [(float(a), float(b)) for a, b in pts]
    t_want = [0.0] * n
    geo = [None] * n
    for i in range(n):
        r = float(radii[i])
        if r <= 0:
            continue
        (px, py), (cx, cy), (nx, ny) = P[i - 1], P[i], P[(i + 1) % n]
        l1 = math.hypot(px - cx, py - cy)
        l2 = math.hypot(nx - cx, ny - cy)
        if l1 < 1e-9 or l2 < 1e-9:
            continue
        u1 = ((px - cx) / l1, (py - cy) / l1)
        u2 = ((nx - cx) / l2, (ny - cy) / l2)
        ang = math.acos(max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1])))
        if ang < 1e-6 or math.pi - ang < 1e-4:
            continue
        t_want[i] = r / math.tan(ang / 2.0)
        geo[i] = (u1, u2, ang)
    scale = [1.0] * n
    for i in range(n):
        j = (i + 1) % n
        L = math.hypot(P[j][0] - P[i][0], P[j][1] - P[i][1])
        need = t_want[i] + t_want[j]
        if need > 0.98 * L:
            f = 0.98 * L / need
            scale[i] = min(scale[i], f)
            scale[j] = min(scale[j], f)
    start, end, arcs = [None] * n, [None] * n, [None] * n
    for i in range(n):
        c = P[i]
        if geo[i] is None:
            start[i] = end[i] = c
            continue
        u1, u2, ang = geo[i]
        t = t_want[i] * scale[i]
        r = t * math.tan(ang / 2.0)
        T1 = (c[0] + u1[0] * t, c[1] + u1[1] * t)
        T2 = (c[0] + u2[0] * t, c[1] + u2[1] * t)
        bx, by = u1[0] + u2[0], u1[1] + u2[1]
        bl = math.hypot(bx, by)
        bx, by = bx / bl, by / bl
        d = r / math.sin(ang / 2.0)
        ctr = (c[0] + bx * d, c[1] + by * d)
        M = (ctr[0] - bx * r, ctr[1] - by * r)
        start[i], end[i], arcs[i] = T1, T2, M
    edges = []
    for i in range(n):
        if arcs[i] is not None:
            edges.append(Part.Arc(to3d(*start[i]), to3d(*arcs[i]), to3d(*end[i])).toShape())
        j = (i + 1) % n
        a, b = end[i], start[j]
        if math.hypot(b[0] - a[0], b[1] - a[1]) > 1e-7:
            edges.append(Part.LineSegment(to3d(*a), to3d(*b)).toShape())
    w = Part.Wire(edges)
    if not w.isClosed():
        raise ValueError("profile wire is not closed")
    return w


def xz(y0):
    return lambda u, v: App.Vector(u, y0, v)


def xy(z0):
    return lambda u, v: App.Vector(u, v, z0)


def yz(x0):
    return lambda u, v: App.Vector(x0, u, v)


def prism_xz(pts, radii, y0, y1):
    f = Part.Face(rounded_wire(pts, radii, xz(y0)))
    return f.extrude(App.Vector(0, y1 - y0, 0))


def split_pts(seq):
    return [(a, b) for a, b, _ in seq], [r for _, _, r in seq]


# --------------------------------------------------------------------------
# Derived layout
# --------------------------------------------------------------------------
def layout(P):
    """Positions everything depends on. Head-local x starts at the chamber's
    back wall (inner face); s = x + s_off."""
    L = {}
    T_tot = P["T_core"] + P["tooth_h"]
    L["x_fw"] = (P["pawl_back_gap"] + P["pawl_t_top"] + P["tooth_h"]
                 + P["core_clear"] + P["T_core"])          # front wall inner face
    L["x_t"] = L["x_fw"] - P["T_core"] - P["core_clear"]  # pawl tooth tips
    L["x_v"] = L["x_t"] - P["tooth_h"]                    # pawl valleys
    L["x_bt"] = L["x_v"] - P["pawl_t_top"]                # pawl back face, top
    L["x_sb"] = L["x_fw"] - T_tot - P["entry_clear"]      # slot back edge
    L["x_fr"] = L["x_sb"] - P["pawl_root_margin"]         # pawl front root
    L["z_top"] = P["H"] - P["pawl_top_drop"]
    L["x_br"] = L["x_bt"] - (L["z_top"] - P["floor_h"]) * math.tan(math.radians(P["pawl_back_lean"]))
    L["x_front"] = L["x_fw"] + P["wall_front"]
    L["x_back"] = -P["wall_back"]
    L["head_len"] = L["x_front"] - L["x_back"]
    L["s_off"] = -L["x_front"]
    L["tooth_tips_x"] = L["x_fw"] - T_tot
    L["engage"] = L["x_t"] - L["tooth_tips_x"]
    yb = P["y_bed"]
    L["y_slot0"] = yb + P["head_W"] - P["wall_side"] - (P["W"] + 2 * P["clear_side"])
    L["y_slot1"] = L["y_slot0"] + P["W"] + 2 * P["clear_side"]
    L["y_head1"] = yb + P["head_W"]
    L["y_pawl1"] = L["y_slot1"] - P["pawl_top_gap"]
    # strap body stations
    L["L_s"] = P["total_len"] - L["head_len"]
    L["band_end"] = P["band_start"] + P["n_lugs"] * P["lug_pitch"]
    L["flange_end"] = L["band_end"] + P["flange_len"]
    L["tip_start"] = L["L_s"] - P["tip_len"]
    L["ramp_run"] = P["tooth_h"] / math.tan(math.radians(P["tooth_ramp_deg"]))
    L["tooth0"] = L["flange_end"] + 1.5
    L["n_teeth"] = int(math.floor((L["tip_start"] - 1.0 - L["tooth0"]
                                   - P["tooth_crest"] - L["ramp_run"]) / P["pitch"])) + 1
    return L


# --------------------------------------------------------------------------
# Head
# --------------------------------------------------------------------------
def pawl_profile(P, L):
    zf, zt = P["floor_h"], L["z_top"]
    xt, xv, xbt, xbr, xfr = L["x_t"], L["x_v"], L["x_bt"], L["x_br"], L["x_fr"]
    h, tf, p = P["tooth_h"], P["pawl_tip_flat"], P["pitch"]
    rr, rs = P["pawl_root_r"], P["pawl_shelf_r"]
    foot_b = max(0.25, xbr - 1.0)
    foot_f = L["x_sb"]
    seq = [(foot_b, zf, 0), (xbr, zf, rr), (xbt, zt, 0.4)]
    for k in range(P["pawl_teeth"]):
        zk = zt - k * p
        if k > 0:
            seq.append((xv, zk, rs))           # shelf root (tension side)
        seq += [(xt, zk, 0), (xt, zk - tf, 0), (xv, zk - tf - h, 0.25)]
    seq += [(xfr, zf, rr), (foot_f, zf, 0), (foot_f, zf - 1.4, 0), (foot_b, zf - 1.4, 0)]
    return seq


def build_head(P, L):
    yb, ys0, ys1, yh1, yp1 = P["y_bed"], L["y_slot0"], L["y_slot1"], L["y_head1"], L["y_pawl1"]
    xb, xf, xfw, xsb = L["x_back"], L["x_front"], L["x_fw"], L["x_sb"]
    H, zf = P["H"], P["floor_h"]
    side = [(xb, 0, 1.0), (xf, 0, 0), (xf, H, 1.5), (xb, H, 2.0)]
    back_l = [(xb, 0, 1.0), (xsb, 0, 0), (xsb, zf, 0), (0, zf, 0.4), (0, H, 0.5), (xb, H, 2.0)]
    front = [(xfw, 0, 0), (xf, 0, 0), (xf, H, 1.5), (xfw, H, 0.5)]
    floor_u = [(xb, 0, 1.0), (xf, 0, 0), (xf, H, 1.5), (xfw, H, 0.5), (xfw, zf, 0.4),
               (0, zf, 0.4), (0, H, 0.5), (xb, H, 2.0)]
    parts = [
        prism_xz(*split_pts(side), ys1, yh1),
        prism_xz(*split_pts(back_l), ys0, ys1),
        prism_xz(*split_pts(front), ys0, ys1),
        prism_xz(*split_pts(floor_u), yb, ys0),
        prism_xz(*split_pts(pawl_profile(P, L)), yb, yp1),
    ]
    head = parts[0].multiFuse(parts[1:])
    c = P["entry_chamfer"]
    if c > 0:
        e = 0.02
        bot = Part.makePolygon([App.Vector(xsb - c - e, ys0 - c - e, -e), App.Vector(xfw + c + e, ys0 - c - e, -e),
                                App.Vector(xfw + c + e, ys1 + c + e, -e), App.Vector(xsb - c - e, ys1 + c + e, -e),
                                App.Vector(xsb - c - e, ys0 - c - e, -e)])
        top = Part.makePolygon([App.Vector(xsb, ys0, c), App.Vector(xfw, ys0, c),
                                App.Vector(xfw, ys1, c), App.Vector(xsb, ys1, c),
                                App.Vector(xsb, ys0, c)])
        tool = Part.makeLoft([bot, top], True, True)
        head = head.cut(tool)
    head.translate(App.Vector(L["s_off"], 0, 0))
    return head


# --------------------------------------------------------------------------
# Strap body
# --------------------------------------------------------------------------
def side_profile(P, L):
    """Top edge from the head to the tip, then back along the flat tyre side."""
    seq = [(-1.0, 0, 0), (-1.0, 13.0, 0), (0.0, 13.0, 0), (0.0, P["root_h"], 3.0),
           (P["root_len"], P["T_neck"], 25.0)]
    b0, T = P["band_start"], P["T_band"]
    seq += [(b0 - P["inramp_len"], P["T_neck"], 12.0), (b0, T, 12.0)]
    l1, l2, h1, h2 = P["lug_len1"], P["lug_len2"], P["lug_h1"], P["lug_h2"]
    for i in range(P["n_lugs"]):
        c = b0 + P["lug_pitch"] * (i + 0.5)
        seq += [(c - l1 / 2, T, P["r_lug_base"]), (c - l1 / 2, T + h1, P["r_lug_top1"]),
                (c - l2 / 2, T + h1, P["r_lug_step"]), (c - l2 / 2, T + h1 + h2, P["r_lug_top2"]),
                (c + l2 / 2, T + h1 + h2, P["r_lug_top2"]), (c + l2 / 2, T + h1, P["r_lug_step"]),
                (c + l1 / 2, T + h1, P["r_lug_top1"]), (c + l1 / 2, T, P["r_lug_base"])]
    Tc, th = P["T_core"], P["tooth_h"]
    seq += [(L["band_end"], T, 15.0), (L["flange_end"], Tc, 15.0)]
    run, cr = L["ramp_run"], P["tooth_crest"]
    for k in range(L["n_teeth"]):
        a = L["tooth0"] + k * P["pitch"]
        seq += [(a, Tc, P["tooth_root_r"]), (a, Tc + th, 0), (a + cr, Tc + th, 0),
                (a + cr + run, Tc, P["tooth_valley_r"])]
    Ls = L["L_s"]
    seq += [(L["tip_start"], Tc, 20.0), (Ls, P["tip_T"], 0.8), (Ls, 0, 0.5)]
    return seq


def plan_profile(P, L):
    yb = P["y_bed"]
    yW, yB, yT = yb + P["W"], yb + P["W_band"], yb + P["tip_W"]
    b0, Ls = P["band_start"], L["L_s"]
    r_tip = P["tip_W"] / 2.0
    return [(-1.0, yb, 0), (Ls, yb, r_tip), (Ls, yT, r_tip), (L["tip_start"], yW, 20.0),
            (L["flange_end"], yW, 10.0), (L["band_end"], yB, 10.0), (b0, yB, 10.0),
            (b0 - P["inramp_len"], yW, 10.0), (14.0, yW, 10.0), (0.6, yb + P["head_W"], 3.0),
            (-1.0, yb + P["head_W"], 0)]


def ellipsoid(a, b, c, center):
    s = Part.makeSphere(1.0)
    m = App.Matrix()
    m.scale(a, b, c)
    e = s.transformGeometry(m)
    e.translate(center)
    return e


def build_body(P, L):
    sp = side_profile(P, L)
    side = prism_xz(*split_pts(sp), P["y_bed"] - 1.0, P["y_bed"] + P["head_W"] + 1.0)
    pp = plan_profile(P, L)
    pf = Part.Face(rounded_wire(*split_pts(pp), xy(-1.0)))
    plan = pf.extrude(App.Vector(0, 0, P["H"] + 3.0))
    body = side.common(plan)
    tools = []
    yc = P["y_bed"] + P["W_band"] / 2.0
    d, C = P["dish_depth"], P["dish_C"]
    if d > 0 and P["dish_every"] > 0:
        k = math.sqrt(2 * d / C - (d / C) ** 2)
        for g in range(P["n_lugs"] - 1):
            if g % P["dish_every"]:
                continue
            sc = P["band_start"] + P["lug_pitch"] * (g + 1)
            tools.append(ellipsoid(P["dish_len"] / 2 / k, P["dish_w"] / 2 / k, C,
                                   App.Vector(sc, yc, P["T_band"] + C - d)))
    if P["rib_n"] > 0 and P["rib_depth"] > 0:
        hw, dep, ext = P["rib_w"] / 2.0, P["rib_depth"], 0.5
        hb = hw * (dep + ext) / dep
        x0, x1 = P["band_start"] + 1.0, L["band_end"] - 1.0
        for i in range(P["rib_n"]):
            y = yc + (i - (P["rib_n"] - 1) / 2.0) * P["rib_pitch"]
            tri = Part.makePolygon([App.Vector(x0, y - hb, -ext), App.Vector(x0, y + hb, -ext),
                                    App.Vector(x0, y, dep), App.Vector(x0, y - hb, -ext)])
            tools.append(Part.Face(tri).extrude(App.Vector(x1 - x0, 0, 0)))
    if tools:
        body = body.cut(Part.makeCompound(tools))
    return body


def build_strap(P):
    L = layout(P)
    head = build_head(P, L)
    body = build_body(P, L)
    shape = head.fuse(body).removeSplitter()
    if shape.ShapeType == "Compound" and len(shape.Solids) == 1:
        shape = shape.Solids[0]
    return shape, L


# --------------------------------------------------------------------------
# Fit estimate (tyre + rim cross-section loop)
# --------------------------------------------------------------------------
def _half_ellipse(a, b):
    return math.pi / 2.0 * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b)))


def loop_estimate(width, aspect, rim_in, spoke=False):
    """Rough strap path around tyre + rim (mm). Good to about +/-10 %."""
    Hs = width * aspect / 100.0
    lip_x = rim_in * 25.4 / 2.0 + (5.0 if spoke else 7.0)
    lip_z = 12.0 if spoke else 14.0
    zc = 0.5 * Hs
    lower = math.hypot(width / 2.0 - lip_x, zc - lip_z)
    crown = _half_ellipse(width / 2.0, Hs - zc)
    well = 8.0 if spoke else 10.0
    cross = 2 * math.hypot(lip_x, well)
    wrap = 2 * (25.0 if spoke else 33.0)
    return 2 * lower + crown + cross + wrap, crown + 2 * lower


TYRES = [
    ("Hunter Metro front 110/70-17 (MT3.00, alloy)", 110, 70, 3.00, False, "FRONT"),
    ("Hunter Metro rear 140/70-17 (alloy)", 140, 70, 3.50, False, "REAR"),
    ("Hunter Retro front 100/80-17 (spoke)", 100, 80, 2.15, True, "FRONT"),
    ("Hunter Retro rear 120/80-17 (spoke)", 120, 80, 2.50, True, "REAR"),
]


def fit_table(P, L):
    rows = []
    teeth_lo = L["tooth0"]
    teeth_hi = L["tooth0"] + (L["n_teeth"] - 1) * P["pitch"]
    for name, w, a, rim, spoke, preset in TYRES:
        if preset != P["preset"]:
            continue
        loop, tyre_arc = loop_estimate(w, a, rim, spoke)
        lock = loop + 5.0
        rows.append(dict(tyre=name, loop_mm=round(loop), lock_at_s=round(lock),
                         teeth_cover=[round(teeth_lo), round(teeth_hi)],
                         in_teeth=bool(teeth_lo <= lock <= teeth_hi),
                         tail_left_mm=round(L["L_s"] - lock)))
    return rows


# --------------------------------------------------------------------------
# Meshes, print coil, STL
# --------------------------------------------------------------------------
def shape_arrays(shape, lin=0.02, ang=0.25):
    import numpy as np
    import MeshPart
    m = MeshPart.meshFromShape(Shape=shape, LinearDeflection=lin, AngularDeflection=ang, Relative=False)
    pts, fac = m.Topology
    V = np.array([[p.x, p.y, p.z] for p in pts], dtype=float)
    T = np.array(fac, dtype=np.int64)
    return V, T


def refine_along_x(V, T, max_dx):
    """Split triangle edges until no edge spans more than max_dx in x.
    Keeps the mesh watertight (shared edges get the same midpoint)."""
    import numpy as np
    for _ in range(40):
        e = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
        e.sort(axis=1)
        dx = np.abs(V[e[:, 0], 0] - V[e[:, 1], 0])
        long_mask = dx > max_dx
        if not long_mask.any():
            return V, T
        le = np.unique(e[long_mask], axis=0)
        mids = 0.5 * (V[le[:, 0]] + V[le[:, 1]])
        base = len(V)
        V = np.vstack([V, mids])
        key = {(int(a), int(b)): base + i for i, (a, b) in enumerate(le)}
        out = []
        for a, b, c in T.tolist():
            m_ab = key.get((a, b) if a < b else (b, a))
            m_bc = key.get((b, c) if b < c else (c, b))
            m_ca = key.get((c, a) if c < a else (a, c))
            k = (m_ab is not None) + (m_bc is not None) + (m_ca is not None)
            if k == 0:
                out.append((a, b, c))
            elif k == 3:
                out += [(a, m_ab, m_ca), (m_ab, b, m_bc), (m_ca, m_bc, c), (m_ab, m_bc, m_ca)]
            elif k == 1:
                if m_ab is not None:
                    out += [(a, m_ab, c), (m_ab, b, c)]
                elif m_bc is not None:
                    out += [(a, b, m_bc), (a, m_bc, c)]
                else:
                    out += [(a, b, m_ca), (m_ca, b, c)]
            else:
                if m_ab is None:      # bc and ca split
                    out += [(m_ca, m_bc, c), (a, b, m_bc), (a, m_bc, m_ca)]
                elif m_bc is None:    # ab and ca split
                    out += [(a, m_ab, m_ca), (m_ab, b, c), (m_ab, c, m_ca)]
                else:                 # ab and bc split
                    out += [(m_ab, b, m_bc), (a, m_ab, m_bc), (a, m_bc, c)]
        T = np.array(out, dtype=np.int64)
    raise RuntimeError("edge refinement did not converge")


def coil_frame(P, L):
    """Neutral axis of the on-edge print coil as a lookup s -> (point, tangent, normal)."""
    import numpy as np
    z_n = P["T_core"] / 2.0
    t_max = P["T_core"] + P["tooth_h"]
    pitch = t_max + P["coil_gap"]
    k = pitch / (2 * math.pi)
    rho0 = P["coil_rho0"]
    s0 = P["coil_rigid"]
    length = L["L_s"] - s0 + 5.0
    phi = np.linspace(0.0, length / (rho0 - 30.0) + 1.0, 200000)
    rho = rho0 - k * phi
    ds = np.sqrt(rho ** 2 + k ** 2)
    s = s0 + np.concatenate([[0.0], np.cumsum(0.5 * (ds[1:] + ds[:-1]) * np.diff(phi))])
    return dict(s=s, phi=phi, rho=rho, k=k, z_n=z_n, s0=s0, pitch=pitch)


def coil_warp(V, P, L, fr):
    """Straight strap -> upright coil. Flat y becomes print Z (bed at y_bed);
    flat z (thickness) becomes radial; length along the neutral axis is kept."""
    import numpy as np
    s, y, z = V[:, 0], V[:, 1], V[:, 2]
    out = np.empty_like(V)
    out[:, 2] = y - P["y_bed"]
    k, z_n, s0 = fr["k"], fr["z_n"], fr["s0"]

    def frame(phi):
        rho = P["coil_rho0"] - k * phi
        c, sn = np.cos(phi), np.sin(phi)
        N = np.stack([rho * c, rho * sn], axis=-1)
        T = np.stack([-k * c - rho * sn, -k * sn + rho * c], axis=-1)
        T /= np.linalg.norm(T, axis=-1, keepdims=True)
        n = np.stack([T[..., 1], -T[..., 0]], axis=-1)
        return N, T, n

    bent = s >= s0
    phi = np.interp(s[bent], fr["s"], fr["phi"])
    N, T, n = frame(phi)
    out[bent, :2] = N + (z[bent] - z_n)[:, None] * n
    N0, T0, n0 = frame(np.array(0.0))
    rig = ~bent
    out[rig, :2] = N0 + (s[rig] - s0)[:, None] * T0 + (z[rig] - z_n)[:, None] * n0
    return out


def mesh_check(T):
    """Closed, consistently oriented: every directed edge once, its reverse once."""
    import numpy as np
    e = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    nv = int(T.max()) + 1
    fwd = e[:, 0] * nv + e[:, 1]
    rev = e[:, 1] * nv + e[:, 0]
    u, cnt = np.unique(fwd, return_counts=True)
    dup = int((cnt != 1).sum())
    missing = int((~np.isin(rev, u)).sum())
    return dict(directed_edge_dupes=dup, unmatched_edges=missing, closed=(dup == 0 and missing == 0))


def volume_of(V, T):
    import numpy as np
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)


def turn_gap(Vw, Vs, min_ds=150.0, chunk=60.0, probe=20.0):
    """Smallest distance between points of the coil that are far apart along
    the strap (different turns, or head vs inner turn). None if no two parts
    come within `probe` mm of each other."""
    import numpy as np
    from scipy.spatial import cKDTree
    best = np.inf
    a = float(Vs.min())
    while a <= Vs.max():
        sel = (Vs >= a) & (Vs < a + chunk)
        far = (Vs < a - min_ds) | (Vs > a + chunk + min_ds)
        if sel.any() and far.any():
            d, _ = cKDTree(Vw[far]).query(Vw[sel], k=1, distance_upper_bound=probe)
            best = min(best, float(d.min()))
        a += chunk
    return None if not np.isfinite(best) else best


def on_edge(V, P):
    """Straight strap stood on its shared edge: flat y -> print Z (bed at y_bed).
    A rotation about x, so triangle orientation is kept."""
    import numpy as np
    out = np.empty_like(V)
    out[:, 0] = V[:, 0]
    out[:, 1] = -V[:, 2]
    out[:, 2] = V[:, 1] - P["y_bed"]
    return out


def write_stl(path, V, T, name="snow_strap"):
    import numpy as np
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    nrm = np.cross(b - a, c - a)
    ln = np.linalg.norm(nrm, axis=1, keepdims=True)
    nrm = np.divide(nrm, ln, out=np.zeros_like(nrm), where=ln > 0)
    rec = np.zeros(len(T), dtype=[("n", "<f4", 3), ("a", "<f4", 3), ("b", "<f4", 3),
                                  ("c", "<f4", 3), ("attr", "<u2")])
    rec["n"], rec["a"], rec["b"], rec["c"] = nrm, a, b, c
    with open(path, "wb") as f:
        f.write(name.encode("ascii")[:80].ljust(80, b" "))
        f.write(np.uint32(len(T)).tobytes())
        f.write(rec.tobytes())


# --------------------------------------------------------------------------
# Parametric FreeCAD object
# --------------------------------------------------------------------------
GROUPS = [
    ("Overall", ["total_len", "y_bed", "W"]),
    ("Head", ["H", "head_W", "wall_back", "wall_front", "wall_side", "floor_h", "clear_side",
              "entry_clear", "entry_chamfer", "root_h", "root_len"]),
    ("Pawl", ["core_clear", "pawl_back_gap", "pawl_t_top", "pawl_teeth", "pawl_tip_flat",
              "pawl_top_drop", "pawl_top_gap", "pawl_back_lean", "pawl_root_r",
              "pawl_root_margin", "pawl_shelf_r"]),
    ("Tread", ["T_neck", "band_start", "inramp_len", "T_band", "W_band", "flange_len",
               "dish_every", "dish_len", "dish_w", "dish_depth", "dish_C",
               "rib_n", "rib_pitch", "rib_w", "rib_depth"]),
    ("Lugs", ["n_lugs", "lug_pitch", "lug_len1", "lug_h1", "lug_len2", "lug_h2",
              "r_lug_base", "r_lug_top1", "r_lug_step", "r_lug_top2"]),
    ("Teeth", ["T_core", "tooth_h", "pitch", "tooth_crest", "tooth_ramp_deg",
               "tooth_root_r", "tooth_valley_r"]),
    ("Tip", ["tip_len", "tip_W", "tip_T"]),
    ("Coil", ["coil_rho0", "coil_gap", "coil_rigid"]),
]


class SnowStrapFeature:
    """Part::FeaturePython whose properties are the strap parameters."""

    def __init__(self, obj, preset="REAR"):
        obj.Proxy = self
        P = params(preset)
        obj.addProperty("App::PropertyString", "Preset", "Overall", "REAR, FRONT or COUPON")
        obj.Preset = preset
        for group, names in GROUPS:
            for nm in names:
                ptype = "App::PropertyInteger" if nm in INT_PARAMS else "App::PropertyFloat"
                obj.addProperty(ptype, nm, group, "mm unless the name says deg")
                setattr(obj, nm, int(P[nm]) if nm in INT_PARAMS else float(P[nm]))
        obj.addProperty("App::PropertyFloat", "Volume_cm3", "Result", "solid volume", 1)
        obj.addProperty("App::PropertyFloat", "Engagement", "Result", "pawl/tooth overlap mm", 1)
        obj.addProperty("App::PropertyInteger", "Teeth", "Result", "number of strap teeth", 1)

    def execute(self, obj):
        P = params(obj.Preset if obj.Preset in PRESETS else "REAR")
        for _, names in GROUPS:
            for nm in names:
                P[nm] = int(getattr(obj, nm)) if nm in INT_PARAMS else float(getattr(obj, nm))
        shape, L = build_strap(P)
        obj.Shape = shape
        obj.Volume_cm3 = round(shape.Volume / 1000.0, 2)
        obj.Engagement = round(L["engage"], 3)
        obj.Teeth = int(L["n_teeth"])

    def dumps(self):
        return None

    def loads(self, state):
        return None


def make_feature(doc, name, preset):
    obj = doc.addObject("Part::FeaturePython", name)
    SnowStrapFeature(obj, preset)
    if App.GuiUp:
        obj.ViewObject.Proxy = 0
        obj.ViewObject.ShapeColor = (1.0, 0.42, 0.08)
    return obj


# --------------------------------------------------------------------------
# Export pipeline
# --------------------------------------------------------------------------
def export_preset(preset, outdir, log=print):
    import numpy as np
    P = params(preset)
    shape, L = build_strap(P)
    tag = "hunter350_%s" % preset.lower()
    if preset == "COUPON":
        tag = "hunter350_lock_test_coupon"
    chk = dict(valid=bool(shape.isValid()), solids=len(shape.Solids), shells=len(shape.Shells),
               faces=len(shape.Faces))
    step = os.path.join(outdir, tag + ".step")
    shape.exportStep(step)
    V, T = shape_arrays(shape)
    stl = os.path.join(outdir, tag + "_straight.stl")
    write_stl(stl, V, T, tag)
    m_straight = mesh_check(T)
    # print file: on edge, coiled (long straps) or straight (coupon)
    fr = coil_frame(P, L)
    coiled = preset != "COUPON"
    if coiled:
        Vr, Tr = refine_along_x(V, T, 1.0)
        Vw = coil_warp(Vr, P, L, fr)
        coil_stl = os.path.join(outdir, tag + "_PRINT_on_edge_coil.stl")
        gap = turn_gap(Vw, Vr[:, 0])
        phi_end = float(np.interp(L["L_s"], fr["s"], fr["phi"]))
    else:
        Tr = T
        Vw = on_edge(V, P)
        coil_stl = os.path.join(outdir, tag + "_PRINT_on_edge.stl")
        gap, phi_end = None, 0.0
    lo, hi = Vw.min(axis=0), Vw.max(axis=0)
    Vw = Vw - [(lo[0] + hi[0]) / 2.0, (lo[1] + hi[1]) / 2.0, lo[2]]
    write_stl(coil_stl, Vw, Tr, tag + "_print")
    m_coil = mesh_check(Tr)
    bb = shape.BoundBox
    vol = shape.Volume
    info = dict(
        preset=preset,
        files=dict(step=os.path.basename(step), stl_straight=os.path.basename(stl),
                   stl_print_coil=os.path.basename(coil_stl)),
        brep=chk,
        volume_cm3=round(vol / 1000.0, 2),
        mass_g={k: round(vol / 1000.0 * v, 1) for k, v in DENSITY.items()},
        bbox_straight=[round(bb.XMin, 2), round(bb.XMax, 2), round(bb.YMin, 2), round(bb.YMax, 2),
                       round(bb.ZMin, 2), round(bb.ZMax, 2)],
        length_total=round(bb.XLength, 2),
        head=dict(length=round(L["head_len"], 2), height=P["H"], width=P["head_W"],
                  slot_x=[round(L["x_sb"] + L["s_off"], 2), round(L["x_fw"] + L["s_off"], 2)],
                  slot_y=[round(L["y_slot0"], 2), round(L["y_slot1"], 2)],
                  pawl_tip_s=round(L["x_t"] + L["s_off"], 2),
                  engagement=round(L["engage"], 3), pawl_tip_to_core=P["core_clear"],
                  side_clearance=P["clear_side"], entry_clearance=P["entry_clear"]),
        sections=dict(root=[0, P["root_len"]], neck=[P["root_len"], P["band_start"] - P["inramp_len"]],
                      band=[P["band_start"], L["band_end"]], flange=[L["band_end"], L["flange_end"]],
                      teeth=[round(L["tooth0"], 2), round(L["tooth0"] + L["n_teeth"] * P["pitch"], 2)],
                      tip=[round(L["tip_start"], 2), round(L["L_s"], 2)]),
        teeth=L["n_teeth"], lugs=P["n_lugs"],
        mesh_straight=dict(triangles=int(len(T)), **m_straight, volume_cm3=round(volume_of(V, T) / 1000, 2)),
        mesh_coil=dict(triangles=int(len(Tr)), **m_coil, volume_cm3=round(volume_of(Vw, Tr) / 1000, 2),
                       footprint_mm=[round(float(hi[0] - lo[0]), 1), round(float(hi[1] - lo[1]), 1)],
                       height_mm=round(float(hi[2] - lo[2]), 2),
                       coiled=coiled,
                       turns=round(phi_end / (2 * math.pi), 2),
                       radius_neutral=[P["coil_rho0"], round(P["coil_rho0"] - fr["k"] * phi_end, 1)] if coiled else None,
                       min_gap_between_turns_mm=None if gap is None else round(gap, 2)),
        fit=fit_table(P, L),
    )
    log("[%s] valid=%s solids=%d vol=%.2f cm3 teeth=%d gap=%s footprint=%s" % (
        preset, chk["valid"], chk["solids"], vol / 1000, L["n_teeth"],
        info["mesh_coil"]["min_gap_between_turns_mm"], info["mesh_coil"]["footprint_mm"]))
    return shape, info


def build_document(doc_path=None):
    doc = App.newDocument("SnowStraps")
    objs = {}
    for i, pr in enumerate(["REAR", "FRONT", "COUPON"]):
        o = make_feature(doc, "Strap_" + pr, pr)
        o.Placement.Base = App.Vector(0, -40.0 * i, 0)
        objs[pr] = o
    doc.recompute()
    if doc_path:
        doc.saveAs(doc_path)
    return doc, objs


def main_headless():
    here = os.path.dirname(os.path.abspath(__file__))
    outdir = os.environ.get("STRAP_OUT") or os.path.join(os.path.dirname(here), "out")
    os.makedirs(outdir, exist_ok=True)
    presets = os.environ.get("STRAP_PRESETS", "REAR,FRONT,COUPON").split(",")
    infos = {}
    for pr in presets:
        _, infos[pr] = export_preset(pr.strip(), outdir)
    with open(os.path.join(outdir, "info.json"), "w") as f:
        json.dump(infos, f, indent=2)
    if os.environ.get("STRAP_FCSTD", "1") == "1":
        sys.path.insert(0, here)
        import snow_strap_fc as mod   # so the saved proxy points at this module, not __main__
        doc = App.newDocument("SnowStraps")
        for i, pr in enumerate(["REAR", "FRONT", "COUPON"]):
            o = doc.addObject("Part::FeaturePython", "Strap_" + pr)
            mod.SnowStrapFeature(o, pr)
            o.Placement.Base = App.Vector(0, -40.0 * i, 0)
        doc.recompute()
        doc.saveAs(os.path.join(outdir, "hunter350_snow_straps.FCStd"))
        App.closeDocument(doc.Name)
    print("done:", outdir)


def main_gui():
    here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else App.getUserMacroDir(True)
    if here not in sys.path:
        sys.path.insert(0, here)
    import snow_strap_fc as mod
    doc = App.newDocument("SnowStraps")
    for i, pr in enumerate(["REAR", "FRONT", "COUPON"]):
        o = doc.addObject("Part::FeaturePython", "Strap_" + pr)
        mod.SnowStrapFeature(o, pr)
        o.Placement.Base = App.Vector(0, -40.0 * i, 0)
        o.ViewObject.Proxy = 0
        o.ViewObject.ShapeColor = (1.0, 0.42, 0.08)
    doc.recompute()
    import FreeCADGui as Gui
    Gui.activeDocument().activeView().viewIsometric()
    Gui.SendMsgToActiveView("ViewFit")


if __name__ == "__main__":
    if App.GuiUp:
        main_gui()
    else:
        main_headless()
