# -*- coding: utf-8 -*-
"""Preview images and fitting diagrams from the exported files (no FreeCAD needed).

Run with FreeCAD's Python (it has numpy + matplotlib):
  "D:\\Software\\FreeCAD\\bin\\python.exe" render_previews.py [out_dir] [images_dir]

Reads out_dir/info.json and the STL files next to it. Writes
  preview_<preset>.png  for every coiled preset,
  fit_diagram.png       the strap path around each tyre + rim section,
into images_dir (default: out_dir).
"""
import json
import math
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ORANGE = np.array([1.0, 0.45, 0.10])
BED_MM = 180.0     # smallest common bed (Prusa Mini, Bambu A1 mini)


def read_stl(path):
    with open(path, "rb") as f:
        f.read(80)
        n = int(np.frombuffer(f.read(4), "<u4")[0])
        rec = np.frombuffer(f.read(n * 50), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    return rec["v"].astype(float)


def shade(tris, light=(0.4, -0.6, 0.7)):
    nrm = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    ln = np.linalg.norm(nrm, axis=1, keepdims=True)
    nrm = np.divide(nrm, ln, out=np.zeros_like(nrm), where=ln > 0)
    L = np.array(light) / np.linalg.norm(light)
    k = 0.35 + 0.65 * np.clip(nrm @ L, 0, 1)
    return np.clip(ORANGE[None, :] * k[:, None] + 0.08, 0, 1)


def view3d(ax, tris, elev, azim, lims=None, light=(0.4, -0.6, 0.7), zoom=1.1):
    if lims is not None:
        (x0, x1), (y0, y1), (z0, z1) = lims
        c = tris.mean(axis=1)
        keep = (c[:, 0] >= x0) & (c[:, 0] <= x1) & (c[:, 1] >= y0) & (c[:, 1] <= y1) & (c[:, 2] >= z0) & (c[:, 2] <= z1)
        tris = tris[keep]
    pc = Poly3DCollection(tris, facecolors=shade(tris, light), edgecolors="none", linewidths=0)
    ax.add_collection3d(pc)
    lo, hi = tris.reshape(-1, 3).min(axis=0), tris.reshape(-1, 3).max(axis=0)
    ax.set_xlim(lo[0], hi[0])
    ax.set_ylim(lo[1], hi[1])
    ax.set_zlim(lo[2], hi[2])
    ax.set_box_aspect(np.maximum(hi - lo, 1e-3), zoom=zoom)   # true scale, no empty cube
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()


def preview(out, img_dir, key, info):
    sec = info["sections"]
    straight = read_stl(os.path.join(out, info["files"]["stl_straight"]))
    printed = read_stl(os.path.join(out, info["files"]["stl_print"]))
    b0, t0 = sec["band"][0], sec["teeth"][0]
    lug_h = info["lug_height_above_tyre"]
    fig = plt.figure(figsize=(14, 15))
    ax = fig.add_subplot(3, 2, 1, projection="3d")
    view3d(ax, straight, 26, -72, lims=((-16, 20), (-12, 16), (-1, 21)), light=(0.2, -0.9, 0.5), zoom=1.1)
    ax.set_title("Head from the open side: wedge pawl, U-frame, root gusset")
    ax = fig.add_subplot(3, 2, 2, projection="3d")
    view3d(ax, straight, 32, -58, lims=((b0 - 8, b0 + 76), (-12, 12), (-1, 12)))
    ax.set_title("Tread: stepped lugs (%.1f mm tall), shallow oval dishes" % lug_h)
    ax = fig.add_subplot(3, 2, 3, projection="3d")
    view3d(ax, straight, -38, -58, lims=((b0 - 8, b0 + 76), (-12, 12), (-1, 12)), light=(0.4, -0.6, -0.7))
    ax.set_title("Tyre side: micro-rib grooves under each lug")
    ax = fig.add_subplot(3, 2, 4, projection="3d")
    view3d(ax, straight, 30, -70, lims=((t0 - 20, t0 + 22), (-12, 12), (-1, 6)))
    pitch = (sec["teeth"][1] - sec["teeth"][0]) / info["teeth"]
    ax.set_title("Teeth start: %.1f mm pitch, 45 deg ramp / 90 deg stop" % pitch)
    ax = fig.add_subplot(3, 2, 5, projection="3d")
    view3d(ax, printed, 38, -50, zoom=1.0)
    ax.set_title("Print file: on edge as an upright coil")
    ax = fig.add_subplot(3, 2, 6)
    tri2 = printed[:, :, :2]
    ax.add_collection(PolyCollection(tri2, facecolors=(1.0, 0.5, 0.15), edgecolors="none"))
    lo, hi = tri2.reshape(-1, 2).min(axis=0), tri2.reshape(-1, 2).max(axis=0)
    c = (lo + hi) / 2
    ax.add_patch(plt.Rectangle((c[0] - BED_MM / 2, c[1] - BED_MM / 2), BED_MM, BED_MM, fill=False,
                               ls="--", lw=1.2, ec="0.35"))
    ax.text(c[0] - BED_MM / 2 + 3, c[1] + BED_MM / 2 - 8, "%.0f x %.0f mm bed" % (BED_MM, BED_MM), color="0.35")
    ax.set_xlim(c[0] - BED_MM / 2 - 8, c[0] + BED_MM / 2 + 8)
    ax.set_ylim(c[1] - BED_MM / 2 - 8, c[1] + BED_MM / 2 + 8)
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    mp = info["mesh_print"]
    ax.set_title("Coil on the bed: %.0f x %.0f mm, %.0f mm tall" % (hi[0] - lo[0], hi[1] - lo[1], mp["height_mm"]))
    fig.suptitle("%s  (%.0f mm, %d lugs, %d teeth, %.1f cm3)" % (
        info["fit"]["tyre"] if info.get("fit") else key, info["length_total"], info["lugs"], info["teeth"],
        info["volume_cm3"]), fontsize=13)
    fig.tight_layout()
    name = "preview_%s.png" % key.lower()
    fig.savefig(os.path.join(img_dir, name), dpi=80)
    plt.close(fig)
    return name


def section_path(sm):
    """Strap path around the section model, starting at the head-side rim corner.
    u = across the wheel (+ = head side), v = radial from the bead seat."""
    a, b = sm["width"] / 2.0, sm["Hs"] - sm["zc"]
    lx, lz, w, dip, zc = sm["lip_x"], sm["lip_z"], sm["w"], sm["dip"], sm["zc"]
    vc = lz - w
    t = np.linspace(0.0, math.pi, 181)
    pts = [(lx, vc), (lx, lz), (a, zc)]
    pts += [(a * math.cos(q), zc + b * math.sin(q)) for q in t[1:-1]]
    pts += [(-a, zc), (-lx, lz), (-lx, vc), (0.0, vc - dip), (lx, vc)]
    P = np.array(pts)
    s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    return P, s


def at(P, s, q):
    q = min(max(q, 0.0), s[-1])
    return np.array([np.interp(q, s, P[:, 0]), np.interp(q, s, P[:, 1])])


def normal_out(P, s, q):
    a, b = at(P, s, q - 0.5), at(P, s, q + 0.5)
    d = (b - a) / max(np.linalg.norm(b - a), 1e-9)
    return np.array([d[1], -d[0]])     # path runs anticlockwise round the section: right = outside


def fit_panel(ax, key, info):
    fit = info["fit"]
    sm, st = fit["section_mm"], fit["stations_s"]
    P, s = section_path(sm)
    rim_half = sm["lip_x"] - (5.0 if sm["spoke"] else 7.0)
    lx, lz, vc = sm["lip_x"], sm["lip_z"], sm["lip_z"] - sm["w"]
    rim = [(rim_half, 0), (lx, lz), (lx, vc), (-lx, vc), (-lx, lz), (-rim_half, 0)]
    ax.add_patch(plt.Polygon(rim, closed=True, fc="0.78", ec="0.45", lw=1))
    a, b, zc = sm["width"] / 2.0, sm["Hs"] - sm["zc"], sm["zc"]
    t = np.linspace(0, math.pi, 91)
    tyre = [(lx, lz), (a, zc)] + [(a * math.cos(q), zc + b * math.sin(q)) for q in t] + [(-lx, lz), (-rim_half, 0), (rim_half, 0)]
    ax.add_patch(plt.Polygon(tyre, closed=True, fc="0.22", ec="0.1", lw=1))
    c0 = st["corner"]
    rel = lambda q: q - c0
    # strap body: head front face (s = 0) to the lock
    q = np.linspace(rel(0.0), rel(st["lock"]) - 0.0, 600)
    q = q[q <= s[-1]]
    xy = np.array([at(P, s, v) for v in q])
    nrm = np.array([normal_out(P, s, v) for v in q])
    xy = xy + 1.8 * nrm
    ax.plot(xy[:, 0], xy[:, 1], color=(1.0, 0.45, 0.1), lw=3.2, solid_capstyle="butt", zorder=4)
    # teeth zone shown lighter
    t0, t1 = rel(info["sections"]["teeth"][0]), min(rel(info["sections"]["teeth"][1]), s[-1])
    qt = np.linspace(t0, t1, 200)
    xyt = np.array([at(P, s, v) for v in qt]) + 1.8 * np.array([normal_out(P, s, v) for v in qt])
    ax.plot(xyt[:, 0], xyt[:, 1], color=(1.0, 0.78, 0.45), lw=3.2, zorder=5)
    # lugs
    b0, b1 = st["band"]
    n = info["lugs"]
    pitch = (b1 - b0) / n
    for i in range(n):
        qq = rel(b0 + pitch * (i + 0.5))
        p, nn = at(P, s, qq), normal_out(P, s, qq)
        tang = np.array([-nn[1], nn[0]])
        h = info["lug_height_above_tyre"]
        poly = [p + 1.8 * nn - 3 * tang, p + 1.8 * nn + 3 * tang, p + h * nn + 1.5 * tang, p + h * nn - 1.5 * tang]
        ax.add_patch(plt.Polygon(poly, closed=True, fc=(0.85, 0.33, 0.05), ec="none", zorder=6))
    # head on the rim side, slot just past the rim edge; tail runs through it and out
    h0, h1 = st["head"]
    ax.add_patch(plt.Rectangle((lx, vc + rel(h0)), 18.0, h1 - h0, fc=(0.95, 0.4, 0.05), ec="0.1", lw=1.2, zorder=7))
    ax.plot([lx, lx + 18.0], [vc, vc], color=(1.0, 0.78, 0.45), lw=2.6, zorder=8)
    ax.plot([lx + 18.0, lx + 48.0], [vc, vc], color=(1.0, 0.78, 0.45), lw=2.6, ls=(0, (3, 2)), zorder=8)
    ax.text(lx + 50, vc, "tail ~%d mm:\ncut flush" % fit["tail_after_lock_mm"], va="center", fontsize=8)
    # labels
    crown = at(P, s, rel((b0 + b1) / 2))
    ax.annotate("%d lugs centred\non the crown" % n, crown + [0, 14], xytext=crown + [0, 34],
                ha="center", fontsize=8, arrowprops=dict(arrowstyle="-", color="0.3"))
    ax.annotate("HEAD on the rim side\n(%s)" % fit["head_at"].split(", ")[1].replace(" side", ""),
                (lx + 18, vc + rel(h0)), xytext=(lx + 26, vc - 32), fontsize=8,
                arrowprops=dict(arrowstyle="-", color="0.3"))
    far = at(P, s, rel(st["far_corner"]))
    ax.annotate("teeth start past\nthe far rim corner", far + [-2, -2], xytext=far + [-62, -30], fontsize=8,
                arrowprops=dict(arrowstyle="-", color="0.3"))
    ax.set_title("%s\nloop ~%d mm (+/-10 %% still locks), strap %d mm" % (
        fit["tyre"], fit["estimated_loop_mm"], info["length_total"]), fontsize=9)
    ax.set_aspect("equal")
    ax.set_xlim(-sm["width"] / 2 - 75, sm["width"] / 2 + 95)
    ax.set_ylim(vc - 50, sm["Hs"] + 50)
    ax.axis("off")


def fit_diagram(img_dir, infos):
    keys = [k for k, v in infos.items() if v.get("fit")]
    if not keys:
        return None
    cols = 2
    rows = int(math.ceil(len(keys) / cols))
    fig, axs = plt.subplots(rows, cols, figsize=(13, 6.2 * rows))
    for ax, k in zip(np.ravel(axs), keys):
        fit_panel(ax, k, infos[k])
    for ax in np.ravel(axs)[len(keys):]:
        ax.axis("off")
    fig.suptitle("Where the strap goes (wheel cross-section, through the wheel; schematic, mm scale)", fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(img_dir, "fit_diagram.png"), dpi=80)
    plt.close(fig)
    return "fit_diagram.png"


def lock_section(img_dir, hs):
    """Cut through the head at the strap's mid-width, with the tail threaded and locked."""
    k = hs["lock"]
    fig, ax = plt.subplots(figsize=(10, 6.4))
    for loop in hs["loops"]:
        ax.add_patch(plt.Polygon(loop, closed=True, fc="0.80", ec="0.25", lw=1.0, zorder=2))
    xc, h, c, p = k["x_fw"] - k["T_core"], k["tooth_h"], k["tooth_crest"], k["pitch"]
    z0, z1 = -7.0, k["H"] + 6.0
    zk = k["z_lo"] - p * math.ceil((k["z_lo"] - z0) / p)
    pts = [(k["x_fw"], z0), (xc, z0)]
    while zk < z1 - p:
        if zk > z0:
            pts += [(xc, zk), (xc - h, zk), (xc - h, zk + c), (xc, zk + c + h)]
        zk += p
    pts += [(xc, z1), (k["x_fw"], z1)]
    ax.add_patch(plt.Polygon(pts, closed=True, fc=(1.0, 0.55, 0.2), ec=(0.6, 0.25, 0.0), lw=1.0, alpha=0.85, zorder=3))
    kw = dict(fontsize=9, arrowprops=dict(arrowstyle="-", color="0.3", lw=0.8), zorder=5)
    ax.annotate("pawl, rooted on the floor:\nthe pull wedges it into the teeth",
                (k["x_v"] - 1.0, 9.0), xytext=(-27, 11), **kw)
    ax.annotate("90 deg shelves carry the load;\n45 deg ramps let teeth click past",
                (k["x_t"], k["z_top"]), xytext=(-27, 21.5), **kw)
    ax.annotate("tail: teeth face the pawl,\nback runs on the front wall", (k["x_fw"] - 0.8, k["H"] + 4),
                xytext=(4, 22.5), **kw)
    ax.annotate("strap core props the pawl\nafter %.2f mm (lock gets stiffer)" % k["core_clear"],
                (k["x_t"] + 0.2, k["z_lo"] - 0.2), xytext=(4, 13.5), **kw)
    ax.annotate("%.2f mm tooth overlap" % k["engage"], (k["x_t"] - 0.4, k["z_lo"] + 0.1), xytext=(-27, 4.5), **kw)
    ax.annotate("tail enters from the rim side\n(entry chamfer, %.1f mm clearance)" % 0.5, (k["x_sb"] + 2.0, -1.5),
                xytext=(4, -6.5), **kw)
    ax.annotate("", xy=(k["x_fw"] - 1.8, -6.0), xytext=(k["x_fw"] - 1.8, -1.5),
                arrowprops=dict(arrowstyle="-|>", color=(0.75, 0.1, 0.1), lw=2), zorder=6)
    ax.text(k["x_fw"] - 1.4, -5.2, "loop\ntension", color=(0.75, 0.1, 0.1), fontsize=9, zorder=6)
    ax.annotate("root gusset into the strap", (8.0, 6.0), xytext=(12, 9.5), **kw)
    ax.set_aspect("equal")
    ax.set_xlim(-30, 26)
    ax.set_ylim(-9, 25)
    ax.set_xlabel("along the strap (mm)")
    ax.set_ylabel("head height (mm)")
    ax.grid(alpha=0.25)
    ax.set_title("How it locks: cut through the head at the strap's mid-width")
    fig.tight_layout()
    fig.savefig(os.path.join(img_dir, "lock_section.png"), dpi=90)
    plt.close(fig)
    return "lock_section.png"


def smooth_path(P, step=0.5, sigma=4.0, keep=8.0):
    """Resample the section path and round its kinks (a strap does not fold sharply).
    The first and last `keep` mm stay straight: the head and the tail entering it."""
    s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    q = np.arange(0.0, s[-1] + 1e-9, step)
    R = np.c_[np.interp(q, s, P[:, 0]), np.interp(q, s, P[:, 1])]
    k = int(3 * sigma / step)
    g = np.exp(-0.5 * (np.arange(-k, k + 1) * step / sigma) ** 2)
    g /= g.sum()
    pad = np.r_[R[-k - 1:-1], R, R[1:k + 1]]          # closed loop
    S = np.c_[np.convolve(pad[:, 0], g, "valid"), np.convolve(pad[:, 1], g, "valid")]
    w = np.clip(np.minimum(q, q[-1] - q) / keep - 1.0, 0.0, 1.0)[:, None]
    S = (1 - w) * R + w * S
    s2 = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(S, axis=0).T))])
    return S, s2


def loop_pose(tris, info, proud=3.0):
    """Straight strap -> installed around the section model. Output axes: x across the
    wheel (+ = head side), z radial (up), y along the tyre. The tail goes through the
    slot and is shown trimmed `proud` mm above the head top (collapsed, still closed)."""
    fit = info["fit"]
    sm, st = fit["section_mm"], fit["stations_s"]
    P, _ = section_path(sm)
    S, s = smooth_path(P)
    T = np.gradient(S, s, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    N = np.c_[T[:, 1], -T[:, 0]]                       # outward for the anticlockwise loop
    lx, vc = sm["lip_x"], sm["lip_z"] - sm["w"]
    loop = s[-1]
    far = st["far_corner"] - st["corner"]
    V = tris.reshape(-1, 3)
    sr = np.minimum(V[:, 0] - st["corner"], loop + 18.0 + proud)
    z = V[:, 2]
    out = np.empty_like(V)
    on = (sr >= 0) & (sr <= loop)
    c = np.c_[np.interp(sr[on], s, S[:, 0]), np.interp(sr[on], s, S[:, 1])]
    n = np.c_[np.interp(sr[on], s, N[:, 0]), np.interp(sr[on], s, N[:, 1])]
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    out[on, 0], out[on, 2] = (c + z[on, None] * n).T
    pre = sr < 0                                       # head part past the rim edge: straight on
    out[pre, 0] = S[0, 0] + z[pre] * N[0, 0] + sr[pre] * T[0, 0]
    out[pre, 2] = S[0, 1] + z[pre] * N[0, 1] + sr[pre] * T[0, 1]
    post = sr > loop                                   # tail through the slot, teeth toward the pawl
    out[post, 0] = lx + (sr[post] - loop)
    out[post, 2] = vc + 0.25 - z[post]
    hd = info["head"]
    width = hd["slot_y"][1] - hd["slot_y"][0] - 2 * hd["side_clearance"]
    dy = 0.5 * (hd["slot_y"][0] + hd["slot_y"][1]) - (info["bbox_straight"][2] + width / 2)
    f = np.clip((sr - far) / max(loop - far, 1.0), 0.0, 1.0)
    out[:, 1] = V[:, 1] + dy * f * f * (3 - 2 * f)     # tail moves over to line up with the slot
    tris = out.reshape(-1, 3, 3)
    vol = np.einsum("ij,ij->i", tris[:, 0], np.cross(tris[:, 1], tris[:, 2])).sum()
    return tris if vol > 0 else tris[:, ::-1]           # the bend swaps two axes: keep normals outward


def write_stl(path, tris, name="snow_strap"):
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    nrm = np.cross(b - a, c - a)
    ln = np.linalg.norm(nrm, axis=1, keepdims=True)
    nrm = np.divide(nrm, ln, out=np.zeros_like(nrm), where=ln > 0)
    rec = np.zeros(len(tris), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = nrm, tris
    with open(path, "wb") as f:
        f.write(name.encode("ascii")[:80].ljust(80, b" "))
        f.write(np.uint32(len(tris)).tobytes())
        f.write(rec.tobytes())


def main(out, img_dir):
    os.makedirs(img_dir, exist_ok=True)
    infos = json.load(open(os.path.join(out, "info.json")))
    for key, info in infos.items():
        if info["mesh_print"]["coiled"]:
            print("wrote", preview(out, img_dir, key, info))
    hs_path = os.path.join(out, "head_section.json")
    if os.path.exists(hs_path):
        print("wrote", lock_section(img_dir, json.load(open(hs_path))))
    if all("section_mm" in (v.get("fit") or {}) for v in infos.values() if v.get("fit")):
        print("wrote", fit_diagram(img_dir, infos))
        for key, info in infos.items():
            if info.get("fit"):
                tris = read_stl(os.path.join(out, info["files"]["stl_straight"]))
                name = info["files"]["stl_straight"].replace("_straight.stl", "_installed_pose.stl")
                write_stl(os.path.join(out, name), loop_pose(tris, info), name[:-4])
                print("wrote", name)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(here), "out")
    main(out_dir, sys.argv[2] if len(sys.argv) > 2 else out_dir)
