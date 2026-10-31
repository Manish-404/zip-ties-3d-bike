# -*- coding: utf-8 -*-
"""Snow-traction strap for the Royal Enfield Hunter 350: parametric FreeCAD model (v2).

A one-piece, zip-tie style anti-skid strap. It wraps the tyre and rim through
the wheel. The head sits just outside the rim's outer lower corner, on the
non-chain / non-disc side. It combines:
  * the 2026-10-23 strap: open-top lock with a floor-rooted, wedge-locking
    two-tooth pawl, a thick root gusset and FDM-friendly 2 mm teeth;
  * the production spec: stepped filleted lugs, oval dishes, tyre-side
    anti-slip texture (raised grip dots, not grooves), 45 deg ramps / 90 deg
    stops, 0.5 mm channel clearance, entry chamfer, rounded tapered tip,
    gradual ramps;
  * the 2026-10-25 design review: closed in-plane ring in the head for
    on-edge printing, longer pawl (lower ratchet strain), pawl teeth that
    mirror the strap teeth, thin fatigue-tolerant band between the lugs,
    tyre-size presets, no teeth where the strap wraps the far rim corner;
  * the 2026-10-27 FEM check (CalculiX): 2.5 mm teeth with 0.4 mm root
    fillets (the tooth roots, not the pawl or head, limit the lock).

Run it either way:
  * FreeCAD GUI: Macro > Macros... > snow_strap_fc.py > Execute. Builds a
    document with parametric straps. Edit properties, then recompute.
  * Headless: "D:\\Software\\FreeCAD\\bin\\freecadcmd.exe" snow_strap_fc.py
    Writes STEP, STL, print STL, .FCStd and info.json to ../out (or to the
    folder in the STRAP_OUT environment variable).

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
    total_len=600.0,        # head back face to tip (presets compute it)
    y_bed=-11.0,            # shared straight edge of all sections
    W=15.0,                 # strap width (neck, toothed strap)
    # head (flat-layout z is the head height)
    H=19.7,                 # pawl top at 18.2, lowest shelf at 15.7: pawl free length 12.1 above the floor
    wall_back=3.0,
    wall_front=3.0,
    wall_side=4.5,          # +y side wall (a solid plate in every printed layer)
    bed_band=5.0,           # -y band: U-frame + pillar around the pawl pocket (FEM: carries the pawl load past the slot)
    floor_h=3.6,            # FEM: 2.4 let the floor ring yield at ~120 N with the head seated only at its front
    clear_side=0.5,         # slot clearance per side, across the strap
    entry_clear=0.5,        # slot clearance over strap thickness incl. teeth
    entry_chamfer=0.8,      # 45 deg lead-in chamfer around the slot entry
    slot_corner_r=1.2,      # rounded slot-end corners (back); 1.7 would touch the tail corner
    chamber_corner_r=0.7,   # back wall / side wall corner (limited by its 0.4/0.5 edge rounds)
    channel_corner_r=0.5,   # rounded corners at the front wall (tail must clear)
    pillar_corner_r=0.0,    # convex pillar corner by the slot; OCC 7.8 cannot round it once the gusset is there
    core_clear=0.45,        # pawl tip to strap core at rest (engagement = tooth_h - this)
    pawl_back_gap=1.8,      # free space behind the pawl at its top
    pawl_t_top=2.75,        # pawl body behind the tooth valleys, at the top
    pawl_teeth=2,
    pawl_tip_flat=0.5,      # pawl tooth mirrors the strap tooth (0.5 flat, 45 deg, 0.8 valley)
    pawl_top_drop=1.5,      # front wall stands this far above the top shelf
    pawl_top_gap=1.0,       # gap between pawl and +y wall (bridge sag room)
    pawl_back_lean=2.0,     # deg, back face lean toward the strap
    pawl_root_t=1.8,        # pawl thickness at the floor
    pawl_root_r=0.8,        # root fillets, both sides
    pawl_shelf_r=0.4,       # fillet where a shelf meets the pawl body (FEM: the critical spot)
    pawl_valley_r=0.4,      # fillet where a ramp meets the pawl body
    pillar_gap=1.0,         # pawl tips to the bed-band pillar, at rest (first layers: elephant's foot)
    pillar_gusset_h=2.6,    # bed-band floor ramps up this much into the pillar (FEM: was the head's hot spot)
    pillar_gusset_len=2.9,  # over this run; starts where the pawl root fillet ends, >= 0.7 mm clear above the floor
    root_h=12.5,            # root gusset height at the head front face
    root_len=17.0,          # gusset ramps down to T_neck over this length
    # strap body
    T_neck=2.6,
    band_start=80.0,        # s where the full-width tread band starts (presets compute it)
    inramp_len=8.0,
    T_band=2.5,             # band between the lugs (thin = low flex strain)
    W_band=22.0,
    n_lugs=5,
    lug_pitch=24.0,
    lug_len1=6.0,           # lower tier length along the strap
    lug_h1=5.0,             # lower tier rises from the band top (2.5) to 7.5
    lug_len2=3.0,           # upper tier length along the strap
    lug_h2=3.0,
    r_lug_base=2.0,
    r_lug_top1=0.8,
    r_lug_step=0.6,
    r_lug_top2=1.0,
    lug_style="STEPPED",    # "RECT" = same two tiers with square corners, as in the reference strap (preset suffix _RECT)
    r_rect_base=1.0,        # RECT: small root fillet (strength)
    r_rect_top=0.3,         # RECT: top and step edges stay almost sharp
    lite=False,             # preset suffix _LITE: about 8 % lighter, same lock (teeth, pawl, head, root untouched)
    lite_w=10.0,            # LITE: strap width where it never enters the head (neck, and before the teeth)
    lite_taper=20.0,        # LITE: length of each width change
    lite_wall=1.3,          # LITE: wall of the lug tunnel along the strap
    lite_floor=1.0,         # LITE: lug tunnel starts this far above the band
    lite_roof=1.0,          # LITE: and stops this far below the lower tier's top
    dish_every=1,           # 1 = a dish in every gap, 2 = alternating gaps
    dish_len=8.0,
    dish_w=16.0,
    dish_depth=0.3,
    dish_C=4.0,             # ellipsoid depth semi-axis (sets the dish slope)
    dot_r=2.0,              # tyre-side grip dots: base radius of each dome
    dot_h=0.74,             # dome height above the tyre side; h / r = 0.37 keeps the printed overhang at 40 deg
    dot_pitch=9.2,          # centre spacing on a staggered (hex) grid; 9.2 = 5.2 mm gap between 4 mm dots, 3 rows across the band; fewer, bigger dots keep the contact area and edge length of the old 8 mm / 3 mm grid
    dot_margin=0.8,         # clear space between a dot's base and the band edge
    rib_n=0,                # old tyre-side V-groove option (recessed, under each lug); 0 = off, dots replace it
    rib_pitch=4.0,
    rib_w=1.0,
    rib_depth=0.45,
    flange_len=14.0,
    teeth_start=0.0,        # 0 = right after the flange ramp (presets set it past the far rim corner)
    T_core=2.4,
    tooth_h=1.2,
    pitch=2.5,              # 2.5 leaves room for 0.4 root fillets (2.0: 0.25, ~30 % higher peak)
    tooth_crest=0.5,
    tooth_ramp_deg=45.0,
    tooth_root_r=0.4,       # stop-face root; 0.05 clear of the pawl tip at rest
    tooth_valley_r=0.4,
    tip_len=35.0,
    tip_W=7.0,
    tip_T=1.8,
    # print coil (on edge)
    coil_rho0=80.0,         # neutral-axis radius where the coil starts
    coil_gap=2.0,           # clear gap between turns
    coil_rigid=22.0,        # head + root up to this s stay straight
)

# Tyre + rim sections. Front sizes take FRONT settings, rear sizes REAR.
TYRES = {
    "METRO_FRONT": dict(label="110/70-17 front, Metro (Dapper, Rebel), cast MT3.00 rim",
                        width=110, aspect=70, rim_in=3.00, spoke=False, wheel="FRONT"),
    "METRO_REAR": dict(label="140/70-17 rear, Metro, cast rim (~MT3.50)",
                       width=140, aspect=70, rim_in=3.50, spoke=False, wheel="REAR"),
    "RETRO_FRONT": dict(label="100/80-17 front, Retro / Factory (spoke) and Base Premium (alloy)",
                        width=100, aspect=80, rim_in=2.15, spoke=True, wheel="FRONT"),
    "RETRO_REAR": dict(label="120/80-17 rear, Retro / Factory (spoke) and Base Premium (alloy)",
                       width=120, aspect=80, rim_in=2.50, spoke=True, wheel="REAR"),
}
WHEEL = {
    "FRONT": dict(n_lugs=4, lug_h2=1.5),   # lower lugs: fixed front mudguard gap
    "REAR": dict(n_lugs=5, lug_h2=3.0),
}
PRESETS = list(TYRES) + ["COUPON"]
COUPON = dict(total_len=230.0, n_lugs=2, band_start=30.0, lug_h2=3.0)

INT_PARAMS = {"pawl_teeth", "n_lugs", "dish_every", "rib_n"}
DENSITY = {"PA12": 1.01, "PA6": 1.14, "PA12_SLS": 0.95, "ONYX": 1.2}  # g/cm3

# Multi-strap print plates for a 330 x 270 x 200 mm bed (Markforged X7). The plate coil is wound
# tighter than the single print file (coil_rho0 = 80, for 180 mm beds) so more coils fit. The
# smallest turn radius stays >= 43 mm, i.e. core bending strain <= 2.8 % (the pawl click design
# value is 2.7 %). Chosen by packing sweeps: one more coil per plate costs about 2 mm of radius.
PLATE_BED = (330.0, 270.0, 200.0)
PLATE_RHO0 = {"METRO_FRONT": 53.0, "METRO_REAR": 54.0, "RETRO_FRONT": 55.0, "RETRO_REAR": 54.0}
PLATE_COUPONS = 6       # test pieces per plate


def section(tyre):
    """Rough strap path around the tyre + rim cross-section (mm, +/-10 %).
    C: tyre contour lip to lip; w: rim lower corner to lip, each side;
    X: across the rim well (hub side) between the two lower corners."""
    t = TYRES[tyre]
    Hs = t["width"] * t["aspect"] / 100.0
    lip_x = t["rim_in"] * 25.4 / 2.0 + (5.0 if t["spoke"] else 7.0)
    lip_z = 12.0 if t["spoke"] else 14.0
    zc = 0.5 * Hs
    a, b = t["width"] / 2.0, Hs - zc
    crown = math.pi / 2.0 * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b)))
    lower = math.hypot(t["width"] / 2.0 - lip_x, zc - lip_z)
    C = crown + 2 * lower
    w = 25.0 if t["spoke"] else 33.0
    dip = 8.0 if t["spoke"] else 10.0
    X = 2 * math.hypot(lip_x, dip)
    return dict(C=C, w=w, X=X, loop=C + 2 * w + X, width=t["width"], Hs=Hs,
                lip_x=lip_x, lip_z=lip_z, zc=zc, dip=dip, spoke=t["spoke"])


def params(preset="METRO_REAR", **over):
    P = dict(BASE)
    while preset.endswith(("_RECT", "_LITE")):      # suffixes in any order
        if preset.endswith("_RECT"):
            preset = preset[:-5]
            P["lug_style"] = "RECT"
            P["dish_depth"] = 0.0    # the oval dish cutter would scoop the flanks of the square lugs
        else:
            preset = preset[:-5]
            P["lite"] = True
    if preset == "COUPON":
        P.update(COUPON)
    else:
        P.update(WHEEL[TYRES[preset]["wheel"]])
    P.update({k: v for k, v in over.items() if k in ("n_lugs", "lug_h2", "lug_pitch", "H", "T_core", "tooth_h")})
    P["preset"] = preset
    if preset != "COUPON":
        L = layout(P)
        sec = section(preset)
        band = P["n_lugs"] * P["lug_pitch"]
        s_corner = L["s_corner"]
        P["band_start"] = round(s_corner + sec["w"] + (sec["C"] - band) / 2.0, 1)
        s_far = s_corner + 2 * sec["w"] + sec["C"]
        s_lock = s_far + sec["X"] + L["z_engage"]
        P["teeth_start"] = round(s_far + 15.0, 1)
        Ls = 1.10 * s_lock + 100.0
        P["total_len"] = 5.0 * math.ceil((Ls + L["head_len"]) / 5.0)
    P.update(over)
    return P


# --------------------------------------------------------------------------
# 2D helpers
# --------------------------------------------------------------------------
def rounded_wire(pts, radii, to3d, max_seg=None):
    """Closed polygon with per-vertex fillet radii -> Part.Wire.

    A positive radius at a convex vertex rounds it off; at a concave vertex the
    same arc adds material, so root fillets come for free. Fillets that would
    overlap on a short edge are shrunk to fit. With max_seg, straight runs are
    split into collinear pieces no longer than max_seg (same geometry, but the
    mesher then has nodes along long edges).
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
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        if seg > 1e-7:
            k = max(1, int(math.ceil(seg / max_seg))) if max_seg else 1
            prev = to3d(*a)
            for m in range(1, k + 1):
                q = b if m == k else (a[0] + (b[0] - a[0]) * m / k, a[1] + (b[1] - a[1]) * m / k)
                nxt = to3d(*q)
                edges.append(Part.LineSegment(prev, nxt).toShape())
                prev = nxt
    w = Part.Wire(edges)
    if not w.isClosed():
        raise ValueError("profile wire is not closed")
    return w


def xz(y0):
    return lambda u, v: App.Vector(u, y0, v)


def xy(z0):
    return lambda u, v: App.Vector(u, v, z0)


def prism_xz(pts, radii, y0, y1, max_seg=None):
    f = Part.Face(rounded_wire(pts, radii, xz(y0), max_seg))
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
    L["z_top"] = P["H"] - P["pawl_top_drop"]                       # top shelf
    L["z_lo"] = L["z_top"] - (P["pawl_teeth"] - 1) * P["pitch"]     # lowest shelf
    L["x_bt"] = P["pawl_back_gap"]                                  # pawl back face, top
    L["x_v"] = L["x_bt"] + P["pawl_t_top"]                          # pawl valleys
    L["x_t"] = L["x_v"] + P["tooth_h"]                              # pawl tooth tips
    L["x_fw"] = L["x_t"] + P["core_clear"] + P["T_core"]            # front wall inner face
    L["tooth_tips_x"] = L["x_fw"] - T_tot
    L["engage"] = L["x_t"] - L["tooth_tips_x"]
    L["x_sb"] = L["tooth_tips_x"] - P["entry_clear"]                # slot back edge
    L["x_br"] = L["x_bt"] - (L["z_top"] - P["floor_h"]) * math.tan(math.radians(P["pawl_back_lean"]))
    L["x_fr"] = L["x_br"] + P["pawl_root_t"]
    L["x_pillar"] = L["x_t"] + P["pillar_gap"]
    L["x_front"] = L["x_fw"] + P["wall_front"]
    L["x_back"] = -P["wall_back"]
    L["head_len"] = L["x_front"] - L["x_back"]
    L["s_off"] = -L["x_front"]
    yb = P["y_bed"]
    L["y_slot0"] = yb + P["bed_band"]
    L["y_slot1"] = L["y_slot0"] + P["W"] + 2 * P["clear_side"]
    L["y_head1"] = L["y_slot1"] + P["wall_side"]
    L["head_W"] = L["y_head1"] - yb
    L["y_pawl1"] = L["y_slot1"] - P["pawl_top_gap"]
    # fitting reference: the rim's outer lower corner sits where the tail's
    # mid-thickness passes the slot, so the tail runs straight off the rim well
    L["s_corner"] = (L["x_sb"] + L["x_fw"]) / 2.0 + L["s_off"] + T_tot / 2.0
    L["z_engage"] = (L["z_top"] + L["z_lo"]) / 2.0
    # strap body stations
    L["L_s"] = P["total_len"] - L["head_len"]
    L["band_end"] = P["band_start"] + P["n_lugs"] * P["lug_pitch"]
    L["flange_end"] = L["band_end"] + P["flange_len"]
    L["tip_start"] = L["L_s"] - P["tip_len"]
    L["ramp_run"] = P["tooth_h"] / math.tan(math.radians(P["tooth_ramp_deg"]))
    L["tooth0"] = max(L["flange_end"] + 1.5, P["teeth_start"])
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
    run = L["ramp_run"]
    rr, rs = P["pawl_root_r"], P["pawl_shelf_r"]
    foot_b = max(0.3, xbr - 1.0)
    foot_f = L["x_sb"]
    seq = [(foot_b, zf, 0), (xbr, zf, rr), (xbt, zt, 0.4)]
    for k in range(P["pawl_teeth"]):
        zk = zt - k * p
        if k > 0:
            seq.append((xv, zk, rs))           # shelf root (tension side under load)
        seq += [(xt, zk, 0), (xt, zk - tf, 0), (xv, zk - tf - run, P["pawl_valley_r"])]
    seq += [(xfr, zf, rr), (foot_f, zf, 0), (foot_f, zf - 1.4, 0), (foot_b, zf - 1.4, 0)]
    return seq


def _vert_edges(shape, x, y, tol=1e-4):
    out = []
    for e in shape.Edges:
        a, b = e.Vertexes[0].Point, e.Vertexes[-1].Point
        if (abs(a.x - x) < tol and abs(b.x - x) < tol and abs(a.y - y) < tol and abs(b.y - y) < tol
                and abs(a.z - b.z) > 1e-6):
            out.append(e)
    return out


def _fillet(shape, r, spots, log):
    edges = []
    for x, y in spots:
        edges += _vert_edges(shape, x, y)
    if not edges or r <= 0:
        return shape
    try:
        out = shape.makeFillet(r, edges)
        if out.isValid():
            return out
    except Exception as ex:  # OCC fillet failure: keep the sharp corner, report it
        log("fillet r=%.2f at %s failed: %s" % (r, spots, ex))
    return shape


def build_head(P, L, log=lambda *a: None):
    yb, ys0, ys1, yh1, yp1 = P["y_bed"], L["y_slot0"], L["y_slot1"], L["y_head1"], L["y_pawl1"]
    xb, xf, xfw, xsb, xp = L["x_back"], L["x_front"], L["x_fw"], L["x_sb"], L["x_pillar"]
    H, zf = P["H"], P["floor_h"]
    side = [(xb, 0, 1.0), (xf, 0, 0), (xf, H, 1.5), (xb, H, 2.0)]
    # bed band: U-frame (back wall, floor under the slot, pillar + front wall)
    # the floor ramps up into the pillar: this strip carries the pawl load around the slot
    gh, gl = P["pillar_gusset_h"], P["pillar_gusset_len"]
    bed_u = [(xb, 0, 1.0), (xf, 0, 0), (xf, H, 1.5), (xp, H, 0.5), (xp, zf + gh, 1.0),
             (xp - gl, zf, 0.4), (0, zf, 0.4), (0, H, 0.5), (xb, H, 2.0)]
    back_l = [(xb, 0, 1.0), (xsb, 0, 0), (xsb, zf, 0), (0, zf, 0.4), (0, H, 0.5), (xb, H, 2.0)]
    front = [(xfw, 0, 0), (xf, 0, 0), (xf, H, 1.5), (xfw, H, 0.5)]
    parts = [
        prism_xz(*split_pts(side), ys1, yh1),
        prism_xz(*split_pts(bed_u), yb, ys0),
        prism_xz(*split_pts(back_l), ys0, ys1),
        prism_xz(*split_pts(front), ys0, ys1),
        prism_xz(*split_pts(pawl_profile(P, L)), yb, yp1),
    ]
    head = parts[0].multiFuse(parts[1:]).removeSplitter()
    if head.ShapeType == "Compound" and len(head.Solids) == 1:
        head = head.Solids[0]
    head = _fillet(head, P["slot_corner_r"], [(xsb, ys0), (xsb, ys1)], log)
    head = _fillet(head, P["chamber_corner_r"], [(0, ys1)], log)
    head = _fillet(head, P["channel_corner_r"], [(xfw, ys0), (xfw, ys1)], log)
    head = _fillet(head, P["pillar_corner_r"], [(xp, ys0)], log)
    c = P["entry_chamfer"]
    if c > 0:
        e = 0.02
        bot = Part.makePolygon([App.Vector(xsb - c - e, ys0 - c - e, -e), App.Vector(xfw + c + e, ys0 - c - e, -e),
                                App.Vector(xfw + c + e, ys1 + c + e, -e), App.Vector(xsb - c - e, ys1 + c + e, -e),
                                App.Vector(xsb - c - e, ys0 - c - e, -e)])
        top = Part.makePolygon([App.Vector(xsb, ys0, c), App.Vector(xfw, ys0, c),
                                App.Vector(xfw, ys1, c), App.Vector(xsb, ys1, c),
                                App.Vector(xsb, ys0, c)])
        head = head.cut(Part.makeLoft([bot, top], True, True))
    head.translate(App.Vector(L["s_off"], 0, 0))
    return head


# --------------------------------------------------------------------------
# Strap body
# --------------------------------------------------------------------------
def side_profile(P, L):
    """Top edge from the head to the tip, then back along the flat tyre side."""
    rh = min(P["root_h"], P["H"] - 2.0)
    seq = [(-1.0, 0, 0), (-1.0, rh + 1.5, 0), (0.0, rh + 1.5, 0), (0.0, rh, 3.0),
           (P["root_len"], P["T_neck"], 25.0)]
    b0, T = P["band_start"], P["T_band"]
    seq += [(b0 - P["inramp_len"], P["T_neck"], 12.0), (b0, T, 12.0)]
    l1, l2, h1, h2 = P["lug_len1"], P["lug_len2"], P["lug_h1"], P["lug_h2"]
    for i in range(P["n_lugs"]):
        c = b0 + P["lug_pitch"] * (i + 0.5)
        if P["lug_style"] == "RECT":    # big rectangle with the small rectangle on top, square corners
            rb, rt = P["r_rect_base"], P["r_rect_top"]
            seq += [(c - l1 / 2, T, rb), (c - l1 / 2, T + h1, rt), (c - l2 / 2, T + h1, rt),
                    (c - l2 / 2, T + h1 + h2, rt), (c + l2 / 2, T + h1 + h2, rt),
                    (c + l2 / 2, T + h1, rt), (c + l1 / 2, T + h1, rt), (c + l1 / 2, T, rb)]
            continue
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
    if P["lite"]:
        # Narrow where the strap never enters the head: the neck, and between the flange and the
        # teeth. The tension stress there stays near 10 MPa at 250 N (teeth, slot and tip are untouched).
        # A zone too short for its two tapers (the coupon) stays full width.
        yL, tp = yb + P["lite_w"], P["lite_taper"]
        t0, fe, ie = L["tooth0"], L["flange_end"], b0 - P["inramp_len"]
        pre = [(t0, yW, 8.0), (t0 - tp, yL, 12.0), (fe + tp, yL, 12.0), (fe, yW, 8.0)]             if t0 - fe > 2 * tp + 10.0 else [(fe, yW, 10.0)]
        neck = [(ie, yW, 10.0), (ie - tp, yL, 12.0), (16.0 + tp, yL, 12.0), (16.0, yW, 10.0)]             if ie - 16.0 > 2 * tp + 10.0 else [(ie, yW, 10.0), (16.0, yW, 10.0)]
        return ([(-1.0, yb, 0), (Ls, yb, r_tip), (Ls, yT, r_tip), (L["tip_start"], yW, 20.0)] + pre
                + [(L["band_end"], yB, 10.0), (b0, yB, 10.0)] + neck
                + [(0.6, yb + L["head_W"], 3.0), (-1.0, yb + L["head_W"], 0)])
    return [(-1.0, yb, 0), (Ls, yb, r_tip), (Ls, yT, r_tip), (L["tip_start"], yW, 20.0),
            (L["flange_end"], yW, 10.0), (L["band_end"], yB, 10.0), (b0, yB, 10.0),
            (b0 - P["inramp_len"], yW, 10.0), (16.0, yW, 10.0), (0.6, yb + L["head_W"], 3.0),
            (-1.0, yb + L["head_W"], 0)]


def ellipsoid(a, b, c, center):
    s = Part.makeSphere(1.0)
    m = App.Matrix()
    m.scale(a, b, c)
    e = s.transformGeometry(m)
    e.translate(center)
    return e


def tyre_dots(P, L, plan_face):
    """Grip dots on the tyre side of the tread band: spherical caps on a staggered
    grid, each dot_h proud of z = 0 and dot_margin clear of the band's edges.
    Raised domes press into the tread rubber from every direction; grooves cannot."""
    r, h, p = P["dot_r"], P["dot_h"], P["dot_pitch"]
    if r <= 0 or h <= 0 or p <= 2 * r:
        return []
    R = (r * r + h * h) / (2.0 * h)                  # sphere the cap is cut from
    z_in = 0.3                                       # the cap overlaps the strap by this much
    cap = Part.makeSphere(R, App.Vector(0, 0, R - h)).common(
        Part.makeBox(2 * R + 2, 2 * R + 2, h + z_in + 0.5, App.Vector(-R - 1, -R - 1, -h - 0.5)))
    keep = r + P["dot_margin"]
    dy = p * math.sqrt(3.0) / 2.0
    n_rows = 2 * int(math.floor((P["W_band"] / 2.0 - keep) / dy)) + 1     # symmetric about the centreline
    yc = P["y_bed"] + P["W_band"] / 2.0
    x_lo, x_hi = P["band_start"] + keep, L["band_end"] - keep             # centres stay inside the band
    n_cols = int((x_hi - x_lo - p / 2.0) // p) + 1                        # odd rows shift by p / 2
    xs = x_lo + ((x_hi - x_lo) - ((n_cols - 1) * p + p / 2.0)) / 2.0      # centre the pattern
    outline = plan_face.OuterWire
    dots = []
    for j in range(n_rows):
        y = yc + (j - (n_rows - 1) / 2.0) * dy
        for k in range(n_cols):
            x = xs + k * p + (p / 2.0 if j % 2 else 0.0)
            pt = App.Vector(x, y, -1.0)               # the plan face lies at z = -1
            if plan_face.isInside(pt, 1e-6, True) and Part.Vertex(pt).distToShape(outline)[0] >= keep:
                d = cap.copy()
                d.translate(App.Vector(x, y, 0.0))
                dots.append(d)
    return dots


def build_body(P, L, max_seg=None):
    sp = side_profile(P, L)
    side = prism_xz(*split_pts(sp), P["y_bed"] - 1.0, P["y_bed"] + L["head_W"] + 1.0, max_seg)
    pp = plan_profile(P, L)
    pf = Part.Face(rounded_wire(*split_pts(pp), xy(-1.0), max_seg))
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
    if P["lite"]:        # a tunnel through each lug, across the whole band (prints as a vertical hole)
        T, w = P["T_band"], P["lug_len1"] - 2 * P["lite_wall"]
        z0, z1 = T + P["lite_floor"], T + P["lug_h1"] - P["lite_roof"]
        if w > 0.8 and z1 - z0 > 0.8:
            for i in range(P["n_lugs"]):
                c = P["band_start"] + P["lug_pitch"] * (i + 0.5)
                tools.append(prism_xz([(c - w / 2, z0), (c - w / 2, z1), (c + w / 2, z1), (c + w / 2, z0)],
                                      [0.4, 0.4, 0.4, 0.4], P["y_bed"] - 1.0, P["y_bed"] + P["W_band"] + 1.0))
    if P["rib_n"] > 0 and P["rib_depth"] > 0:
        hw, dep, ext = P["rib_w"] / 2.0, P["rib_depth"], 0.5
        hb = hw * (dep + ext) / dep
        rl = P["lug_len1"] + 2.0
        for i in range(P["n_lugs"]):
            x0 = P["band_start"] + P["lug_pitch"] * (i + 0.5) - rl / 2.0
            for j in range(P["rib_n"]):
                y = yc + (j - (P["rib_n"] - 1) / 2.0) * P["rib_pitch"]
                tri = Part.makePolygon([App.Vector(x0, y - hb, -ext), App.Vector(x0, y + hb, -ext),
                                        App.Vector(x0, y, dep), App.Vector(x0, y - hb, -ext)])
                tools.append(Part.Face(tri).extrude(App.Vector(rl, 0, 0)))
    if tools:
        body = body.cut(Part.makeCompound(tools))
    dots = tyre_dots(P, L, pf)
    L["n_dots"] = len(dots)
    if dots:
        body = body.multiFuse(dots)
    return body


def build_strap(P, max_seg=None, log=lambda *a: None):
    """Clean solid for CAD/STEP. With max_seg the long faces stay split into
    short strips (identical shape) so meshes bend smoothly in the print coil."""
    L = layout(P)
    head = build_head(P, L, log)
    body = build_body(P, L, max_seg)
    shape = head.fuse(body)
    if not max_seg:
        shape = shape.removeSplitter()
    if shape.ShapeType == "Compound" and len(shape.Solids) == 1:
        shape = shape.Solids[0]
    return shape, L


# --------------------------------------------------------------------------
# Fit report
# --------------------------------------------------------------------------
def fit_report(P, L):
    if P["preset"] not in TYRES:
        return None
    sec = section(P["preset"])
    s_far = L["s_corner"] + 2 * sec["w"] + sec["C"]
    s_lock = s_far + sec["X"] + L["z_engage"]
    t0 = L["tooth0"]
    t1 = L["tooth0"] + (L["n_teeth"] - 1) * P["pitch"]
    crown_mid = L["s_corner"] + sec["w"] + sec["C"] / 2.0
    band_mid = P["band_start"] + P["n_lugs"] * P["lug_pitch"] / 2.0
    return dict(
        tyre=TYRES[P["preset"]]["label"],
        estimated_loop_mm=round(sec["loop"]),
        head_at="rim outer lower corner, %s side" % (
            "non-chain" if TYRES[P["preset"]]["wheel"] == "REAR" else "non-disc"),
        head_axial_reach_beyond_rim_face_mm=P["H"],
        lug_zone_centre_offset_from_crown_mm=round(band_mid - crown_mid, 1),
        lug_zone_half_span_mm=round(P["n_lugs"] * P["lug_pitch"] / 2.0, 1),
        far_rim_corner_at_s=round(s_far),
        teeth_s=[round(t0), round(t1)],
        lock_at_s=round(s_lock),
        lock_if_loop_10pct_short=round(0.9 * s_lock),
        lock_if_loop_10pct_long=round(1.1 * s_lock),
        all_inside_teeth=bool(t0 <= 0.9 * s_lock and 1.1 * s_lock <= t1),
        tail_after_lock_mm=round(L["L_s"] - s_lock),
        # for drawings: section model (z from the bead seat) and stations along the strap
        section_mm={k: (round(v, 2) if isinstance(v, float) else v) for k, v in sec.items()},
        stations_s=dict(corner=round(L["s_corner"], 2), band=[P["band_start"], round(L["band_end"], 1)],
                        far_corner=round(s_far, 1), lock=round(s_lock, 1), tip=round(L["L_s"], 1),
                        head=[round(-L["head_len"], 2), 0.0]),
    )


# --------------------------------------------------------------------------
# Meshes, print coil, STL
# --------------------------------------------------------------------------
def shape_arrays(shape, lin=0.03, ang=0.35):
    import numpy as np
    import MeshPart
    m = MeshPart.meshFromShape(Shape=shape, LinearDeflection=lin, AngularDeflection=ang, Relative=False)
    pts, fac = m.Topology
    V = np.array([[p.x, p.y, p.z] for p in pts], dtype=float)
    T = np.array(fac, dtype=np.int64)
    return V, T


def drop_fins(T):
    """Remove zero-volume fins: two triangles on the same three vertices with opposite
    orientation. OCC leaves them where a fillet ends on a rounded profile corner."""
    import numpy as np
    key = np.sort(T, axis=1)
    _, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
    keep = np.ones(len(T), dtype=bool)
    for g in np.flatnonzero(cnt == 2):
        i, j = np.flatnonzero(inv == g)
        a, b = T[i].tolist(), T[j].tolist()
        k = b.index(a[0])
        if [b[k], b[k - 1], b[k - 2]] == a:      # same cycle, reversed: a fin
            keep[i] = keep[j] = False
    return T[keep]


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
    """Neutral axis of the on-edge print coil as a lookup s -> phi."""
    import numpy as np
    z_n = P["T_core"] / 2.0
    pitch = P["T_core"] + P["tooth_h"] + P["coil_gap"]
    k = pitch / (2 * math.pi)
    rho0 = P["coil_rho0"]
    s0 = P["coil_rigid"]
    length = L["L_s"] - s0 + 5.0
    phi = np.linspace(0.0, length / (rho0 - 30.0) + 1.0, 200000)
    rho = rho0 - k * phi
    ds = np.sqrt(rho ** 2 + k ** 2)
    s = s0 + np.concatenate([[0.0], np.cumsum(0.5 * (ds[1:] + ds[:-1]) * np.diff(phi))])
    return dict(s=s, phi=phi, k=k, z_n=z_n, s0=s0, pitch=pitch)


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


def on_edge(V, P):
    """Straight strap stood on its shared edge: flat y -> print Z (bed at y_bed).
    A rotation about x, so triangle orientation is kept."""
    import numpy as np
    out = np.empty_like(V)
    out[:, 0] = V[:, 0]
    out[:, 1] = -V[:, 2]
    out[:, 2] = V[:, 1] - P["y_bed"]
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
    ("Head", ["H", "wall_back", "wall_front", "wall_side", "bed_band", "floor_h", "clear_side",
              "entry_clear", "entry_chamfer", "slot_corner_r", "chamber_corner_r", "channel_corner_r",
              "pillar_corner_r", "root_h", "root_len"]),
    ("Pawl", ["core_clear", "pawl_back_gap", "pawl_t_top", "pawl_teeth", "pawl_tip_flat",
              "pawl_top_drop", "pawl_top_gap", "pawl_back_lean", "pawl_root_t", "pawl_root_r",
              "pawl_shelf_r", "pawl_valley_r", "pillar_gap", "pillar_gusset_h", "pillar_gusset_len"]),
    ("Tread", ["T_neck", "band_start", "inramp_len", "T_band", "W_band", "flange_len",
               "dish_every", "dish_len", "dish_w", "dish_depth", "dish_C",
               "dot_r", "dot_h", "dot_pitch", "dot_margin",
               "rib_n", "rib_pitch", "rib_w", "rib_depth"]),
    ("Lugs", ["n_lugs", "lug_pitch", "lug_len1", "lug_h1", "lug_len2", "lug_h2",
              "r_lug_base", "r_lug_top1", "r_lug_step", "r_lug_top2"]),
    ("Teeth", ["teeth_start", "T_core", "tooth_h", "pitch", "tooth_crest", "tooth_ramp_deg",
               "tooth_root_r", "tooth_valley_r"]),
    ("Tip", ["tip_len", "tip_W", "tip_T"]),
    ("Coil", ["coil_rho0", "coil_gap", "coil_rigid"]),
]


class SnowStrapFeature:
    """Part::FeaturePython whose properties are the strap parameters.
    band_start, teeth_start and total_len were computed for the preset's tyre;
    change them by hand if you change the lug count or pitch."""

    def __init__(self, obj, preset="METRO_REAR"):
        obj.Proxy = self
        P = params(preset)
        obj.addProperty("App::PropertyString", "Preset", "Overall", ", ".join(PRESETS))
        obj.Preset = preset
        for group, names in GROUPS:
            for nm in names:
                ptype = "App::PropertyInteger" if nm in INT_PARAMS else "App::PropertyFloat"
                obj.addProperty(ptype, nm, group, "mm unless the name says deg")
                setattr(obj, nm, int(P[nm]) if nm in INT_PARAMS else float(P[nm]))
        obj.addProperty("App::PropertyFloat", "Volume_cm3", "Result", "solid volume", 1)
        obj.addProperty("App::PropertyFloat", "Engagement", "Result", "pawl/tooth overlap at rest, mm", 1)
        obj.addProperty("App::PropertyInteger", "Teeth", "Result", "number of strap teeth", 1)
        obj.addProperty("App::PropertyInteger", "Dots", "Result", "number of tyre-side grip dots", 1)

    def execute(self, obj):
        P = dict(BASE)
        P["preset"] = obj.Preset
        for _, names in GROUPS:
            for nm in names:
                v = getattr(obj, nm, BASE[nm])      # documents saved before a parameter existed
                P[nm] = int(v) if nm in INT_PARAMS else float(v)
        shape, L = build_strap(P)
        obj.Shape = shape
        obj.Volume_cm3 = round(shape.Volume / 1000.0, 2)
        obj.Engagement = round(L["engage"], 3)
        obj.Teeth = int(L["n_teeth"])
        if hasattr(obj, "Dots"):
            obj.Dots = int(L.get("n_dots", 0))

    def dumps(self):
        return None

    def loads(self, state):
        return None


def add_features(doc, module):
    objs = []
    for i, pr in enumerate(PRESETS):
        o = doc.addObject("Part::FeaturePython", "Strap_" + pr)
        module.SnowStrapFeature(o, pr)
        o.Placement.Base = App.Vector(0, -40.0 * i, 0)
        if App.GuiUp:
            o.ViewObject.Proxy = 0
            o.ViewObject.ShapeColor = (1.0, 0.42, 0.08)
        objs.append(o)
    doc.recompute()
    return objs


# --------------------------------------------------------------------------
# Export pipeline
# --------------------------------------------------------------------------
def export_preset(preset, outdir, log=print):
    import numpy as np
    P = params(preset)
    shape, L = build_strap(P, log=log)
    tag = "hunter350_%s" % P["preset"].lower()
    if P["lug_style"] == "RECT":
        tag += "_rect"
    if P["lite"]:
        tag += "_lite"
    chk = dict(valid=bool(shape.isValid()), solids=len(shape.Solids), shells=len(shape.Shells),
               faces=len(shape.Faces))
    step = os.path.join(outdir, tag + ".step")
    shape.exportStep(step)
    split_shape, _ = build_strap(P, max_seg=3.0, log=log)
    V, T = shape_arrays(split_shape)
    V, T = refine_along_x(V, drop_fins(T), 3.0)
    stl = os.path.join(outdir, tag + "_straight.stl")
    write_stl(stl, V, T, tag)
    m_straight = mesh_check(T)
    fr = coil_frame(P, L)
    coiled = P["preset"] != "COUPON"
    if coiled:
        Vw = coil_warp(V, P, L, fr)
        pstl = os.path.join(outdir, tag + "_PRINT_on_edge_coil.stl")
        gap = turn_gap(Vw, V[:, 0])
        phi_end = float(np.interp(L["L_s"], fr["s"], fr["phi"]))
    else:
        Vw = on_edge(V, P)
        pstl = os.path.join(outdir, tag + "_PRINT_on_edge.stl")
        gap, phi_end = None, 0.0
    lo, hi = Vw.min(axis=0), Vw.max(axis=0)
    Vw = Vw - [(lo[0] + hi[0]) / 2.0, (lo[1] + hi[1]) / 2.0, lo[2]]
    write_stl(pstl, Vw, T, tag + "_print")
    plate = None
    if os.environ.get("STRAP_PLATES", "1") == "1":
        plate = export_plate(P, L, V, T, outdir, tag, log)
    vol = shape.Volume
    bb = shape.optimalBoundingBox()
    info = dict(
        preset=preset, lug_style=P["lug_style"], lite=P["lite"],
        files=dict(step=os.path.basename(step), stl_straight=os.path.basename(stl),
                   stl_print=os.path.basename(pstl)),
        brep=chk,
        volume_cm3=round(vol / 1000.0, 2),
        mass_g={k: round(vol / 1000.0 * v, 1) for k, v in DENSITY.items()},
        bbox_straight=[round(bb.XMin, 2), round(bb.XMax, 2), round(bb.YMin, 2), round(bb.YMax, 2),
                       round(bb.ZMin, 2), round(bb.ZMax, 2)],
        length_total=round(bb.XLength, 1),
        head=dict(length=round(L["head_len"], 2), height=P["H"], width=round(L["head_W"], 2),
                  slot_s=[round(L["x_sb"] + L["s_off"], 2), round(L["x_fw"] + L["s_off"], 2)],
                  slot_y=[round(L["y_slot0"], 2), round(L["y_slot1"], 2)],
                  pawl_tip_s=round(L["x_t"] + L["s_off"], 2), pawl_top_z=L["z_top"],
                  engagement_at_rest=round(L["engage"], 3), pawl_tip_to_core=P["core_clear"],
                  side_clearance=P["clear_side"], entry_clearance=P["entry_clear"]),
        sections=dict(root=[0, P["root_len"]], neck=[P["root_len"], round(P["band_start"] - P["inramp_len"], 1)],
                      band=[P["band_start"], round(L["band_end"], 1)],
                      flange=[round(L["band_end"], 1), round(L["flange_end"], 1)],
                      teeth=[round(L["tooth0"], 1), round(L["tooth0"] + L["n_teeth"] * P["pitch"], 1)],
                      tip=[round(L["tip_start"], 1), round(L["L_s"], 1)]),
        teeth=L["n_teeth"], lugs=P["n_lugs"],
        lug_height_above_tyre=round(P["T_band"] + P["lug_h1"] + P["lug_h2"], 2),
        grip_dots=dict(count=int(L.get("n_dots", 0)), base_radius=P["dot_r"], height=P["dot_h"],
                       pitch=P["dot_pitch"],
                       overhang_deg_on_edge=round(2 * math.degrees(math.atan(P["dot_h"] / P["dot_r"])), 1),
                       base_coverage_pct=round(100 * math.pi * P["dot_r"] ** 2
                                               / (math.sqrt(3.0) / 2.0 * P["dot_pitch"] ** 2), 1)),
        mesh_straight=dict(triangles=int(len(T)), **m_straight, volume_cm3=round(volume_of(V, T) / 1000, 2)),
        plate=plate,
        mesh_print=dict(triangles=int(len(T)), volume_cm3=round(volume_of(Vw, T) / 1000, 2),
                        footprint_mm=[round(float(hi[0] - lo[0]), 1), round(float(hi[1] - lo[1]), 1)],
                        height_mm=round(float(hi[2] - lo[2]), 2),
                        coiled=coiled,
                        turns=round(phi_end / (2 * math.pi), 2),
                        radius_neutral=[P["coil_rho0"], round(P["coil_rho0"] - fr["k"] * phi_end, 1)] if coiled else None,
                        min_gap_between_turns_mm=None if gap is None else round(gap, 2)),
        fit=fit_report(P, L),
    )
    log("[%s] valid=%s solids=%d vol=%.2f cm3 L=%.0f teeth=%d gap=%s footprint=%s" % (
        preset, chk["valid"], chk["solids"], vol / 1000, bb.XLength, L["n_teeth"],
        info["mesh_print"]["min_gap_between_turns_mm"], info["mesh_print"]["footprint_mm"]))
    return shape, info


def export_plate(P, L, V, T, outdir, tag, log=print):
    """Pack as many straps as fit on the plate (PLATE_BED) and write one STL with all of them.
    Coils use PLATE_RHO0; the coupon is straight, on edge. Returns the info dict."""
    import numpy as np
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import plate_layout as pl
    base = P["preset"]
    if base == "COUPON":
        Vp, rho0, rho_min, gap = on_edge(V, P), None, None, None
        n_max = PLATE_COUPONS
    else:
        rho0 = PLATE_RHO0[base]
        P2 = dict(P, coil_rho0=rho0)
        fr = coil_frame(P2, L)
        Vp = coil_warp(V, P2, L, fr)
        gap = turn_gap(Vp, V[:, 0])
        phi_end = float(np.interp(L["L_s"], fr["s"], fr["phi"]))
        rho_min = rho0 - fr["k"] * phi_end
        n_max = 12
    Vp = Vp - [0.0, 0.0, Vp[:, 2].min()]
    Vm, Tm, placed, skipped = pl.build_plate([(Vp, T)] * n_max, bed=PLATE_BED)
    if Vm is None:
        return None
    hi, lo = Vm.max(axis=0), Vm.min(axis=0)
    assert lo[0] >= pl.MARGIN - 0.5 and lo[1] >= pl.MARGIN - 0.5
    assert hi[0] <= PLATE_BED[0] - pl.MARGIN + 0.5 and hi[1] <= PLATE_BED[1] - pl.MARGIN + 0.5
    pdir = os.path.join(outdir, "plates")
    os.makedirs(pdir, exist_ok=True)
    name = "%s_PLATE_%dup.stl" % (tag, len(placed))
    write_stl(os.path.join(pdir, name), Vm, Tm, tag + "_plate")
    vol = volume_of(Vp, T) / 1000.0
    cg = pl.min_gap(Vm, Tm, placed, [(Vp, T)] * n_max)
    info = dict(
        file="plates/" + name, count=len(placed), bed_mm=list(PLATE_BED), margin_mm=pl.MARGIN,
        clearance_target_mm=pl.CLEAR,
        coil_rho0=rho0, coil_rho_min=None if rho_min is None else round(rho_min, 1),
        core_bend_strain_pct=None if rho_min is None else round(100.0 * (P["T_core"] / 2.0) / rho_min, 2),
        min_gap_turns_mm=None if gap is None else round(gap, 2),
        min_gap_between_straps_mm=None if cg is None else round(cg, 2),
        extent_mm=[round(float(hi[0] - lo[0]), 1), round(float(hi[1] - lo[1]), 1)],
        height_mm=round(float(hi[2] - lo[2]), 2),
        rotations_deg=[int(round(math.degrees(p["rot"]))) for p in placed],
        mass_g_onyx=round(len(placed) * vol * DENSITY["ONYX"], 0),
        mesh=dict(triangles=int(len(Tm)), **mesh_check(Tm)),
    )
    log("[%s] plate: %d straps, extent %s, height %.1f, strap gap %s, turn gap %s, rho_min %s" % (
        tag, info["count"], info["extent_mm"], info["height_mm"], info["min_gap_between_straps_mm"],
        info["min_gap_turns_mm"], info["coil_rho_min"]))
    return info


def head_section(P, s_max=25.0):
    """Head + root cut at y = 0 as (s, z) polylines, plus the lock numbers, for drawings."""
    shape, L = build_strap(P)
    box = Part.makeBox(s_max + 20.0, 40.0, P["H"] + 10.0, App.Vector(-20.0, -20.0, -5.0))
    loops = []
    for w in shape.common(box).slice(App.Vector(0, 1, 0), 0.0):
        loops.append([[round(p.x, 3), round(p.z, 3)] for p in w.discretize(Deflection=0.01)])
    so = L["s_off"]
    lock = dict(x_fw=L["x_fw"] + so, x_t=L["x_t"] + so, x_v=L["x_v"] + so, x_sb=L["x_sb"] + so,
                z_top=L["z_top"], z_lo=L["z_lo"], engage=L["engage"])
    lock.update({k: P[k] for k in ("H", "floor_h", "T_core", "tooth_h", "pitch", "tooth_crest",
                                   "core_clear", "W", "y_bed")})
    return dict(loops=loops, lock=lock)


def main_headless():
    here = os.path.dirname(os.path.abspath(__file__))
    outdir = os.environ.get("STRAP_OUT") or os.path.join(os.path.dirname(here), "out")
    os.makedirs(outdir, exist_ok=True)
    presets = os.environ.get("STRAP_PRESETS", ",".join(PRESETS)).split(",")
    info_path = os.path.join(outdir, "info.json")
    infos = json.load(open(info_path)) if os.path.exists(info_path) else {}   # a partial build keeps the rest
    for pr in presets:
        _, infos[pr.strip()] = export_preset(pr.strip(), outdir)
    with open(info_path, "w") as f:
        json.dump(infos, f, indent=2)
    with open(os.path.join(outdir, "head_section.json"), "w") as f:
        json.dump(head_section(params("COUPON")), f)
    if os.environ.get("STRAP_FCSTD", "1") == "1":
        sys.path.insert(0, here)
        import snow_strap_fc as mod   # the saved proxy must point at this module, not __main__
        doc = App.newDocument("SnowStraps")
        add_features(doc, mod)
        doc.saveAs(os.path.join(outdir, "hunter350_snow_straps.FCStd"))
        App.closeDocument(doc.Name)
    print("done:", outdir)


def main_gui():
    here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else App.getUserMacroDir(True)
    if here not in sys.path:
        sys.path.insert(0, here)
    import snow_strap_fc as mod
    doc = App.newDocument("SnowStraps")
    add_features(doc, mod)
    import FreeCADGui as Gui
    Gui.activeDocument().activeView().viewIsometric()
    Gui.SendMsgToActiveView("ViewFit")


def _invoked_as_script():
    """GUI Macro > Execute runs this file as __main__, but `freecadcmd snow_strap_fc.py`
    imports it by module name. Restoring an .FCStd only imports it. A same-named copy
    earlier on sys.path (e.g. the FreeCAD macro folder) gets imported instead of the
    file given on the command line, so say so rather than silently doing nothing."""
    if __name__ == "__main__":
        return True
    me = os.path.normcase(os.path.abspath(globals().get("__file__", "")))
    for a in sys.argv[1:]:
        if a.lower().endswith(".py") and os.path.basename(a).lower() == os.path.basename(me):
            if os.path.normcase(os.path.abspath(a)) == me:
                return True
            print("snow_strap_fc: freecadcmd loaded %s, not %s (a same-named file comes first on "
                  "sys.path, e.g. in the FreeCAD macro folder). Remove that copy and run again."
                  % (me, os.path.abspath(a)))
    return False


if _invoked_as_script() and not os.environ.get("SNOW_STRAP_RUNNING"):
    os.environ["SNOW_STRAP_RUNNING"] = "1"   # the self-import in main_* must not re-run it
    try:
        if App.GuiUp:
            main_gui()
        else:
            main_headless()
    finally:
        os.environ.pop("SNOW_STRAP_RUNNING", None)
