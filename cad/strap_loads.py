# -*- coding: utf-8 -*-
"""Load model for the snow strap: tooth pressure and wheel torque by Royal Enfield model.

Plain Python + matplotlib (no FreeCAD). Run:  python cad/strap_loads.py docs/images
Writes out/loads.json, out/loads.md and <dir>/loads_by_model.png.

This is a hand model with stated assumptions, not a measurement. The only
FEM inputs are the numbers in HANDOFF.md section 8.5 (CalculiX, PA12).

Model
-----
1. Traction ceiling. The strap cannot pass more tangential force than the tyre
   can put into the snow:  F_t = mu_snow * N_rear,  N_rear = share * (m_bike + m_rider) * g.
   Wheel torque at that limit = F_t * r_roll.
2. Slip of one strap. The strap width runs along the tyre circumference, so the
   tangential force acts edgewise on the strap. It is held by friction: the loop
   (tension T) presses on tyre and rim with a total normal force T * theta.
       F_hold = mu_f * T * theta
   Required loop tension for no slip:  T_req = F_share / (mu_f * theta).
3. Lock. Loop tension T is carried by the pawl's 2 teeth, T/2 each.
   Bearing pressure on a tooth face = (T/2) / (overlap * engaged width).
   Root shear = (T/2) / (tooth base * width). Peak stress at the fillet scales
   linearly from the FEM point (39 MPa at 300 N shared), valid below yield.
"""

import json
import math
import os
import sys

G = 9.81

# Strap geometry (cad/snow_strap_fc.py BASE, out/info.json)
OVERLAP = 0.75        # mm, tooth overlap with the pawl at rest
WIDTH_ENG = 14.5      # mm, engaged width
TOOTH_BASE = 0.5 + 1.2  # mm, crest + 45 deg ramp run
CORE_AREA = 2.4 * 15.0  # mm2, strap core at the tooth valley
FEM_PEAK_300 = 39.0   # MPa, tooth-root fillet, 300 N shared (HANDOFF 8.5)
RATING_N = 300.0      # N, PA12 rating from the FEM
PA12_TENSILE = 45.0   # MPa, HANDOFF 8.5 / FITTING 5

# Assumptions
MU_SNOW = 0.35        # packed snow, lugged strap
MU_ICE = 0.15
MU_F = 0.40           # nylon strap on rubber / alloy, damp
THETA = 4.5           # rad of wrap of the loop on tyre + rim
REAR_SHARE = 0.55
RIDER_KG = 75.0

# name, cc, torque Nm, kerb kg, rear tyre text, rim in, section width mm, aspect, has preset
BIKES = [
    ("Hunter 350 Retro", 349, 27, 177, "120/80-17", 17, 120, 80, "RETRO_REAR"),
    ("Hunter 350 Metro", 349, 27, 181, "140/70-17", 17, 140, 70, "METRO_REAR"),
    ("Meteor 350", 349, 27, 191, "140/70-17", 17, 140, 70, None),
    ("Classic 350", 349, 27, 195, "120/80-18", 18, 120, 80, None),
    ("Himalayan 450", 452, 40, 196, "140/80-17", 17, 140, 80, None),
    ("Continental GT 650", 648, 52.3, 202, "130/70-18", 18, 130, 70, None),
    ("Interceptor 650", 648, 52, 213, "130/70-18", 18, 130, 70, None),
    ("Super Meteor 650", 648, 52.3, 241, "150/80-16", 16, 150, 80, None),
]


def tooth_table(forces=(100, 200, 300)):
    rows = []
    for T in forces:
        f = T / 2.0
        rows.append(dict(
            loop_tension_N=T,
            per_tooth_N=f,
            bearing_MPa=round(f / (OVERLAP * WIDTH_ENG), 1),
            root_shear_MPa=round(f / (TOOTH_BASE * WIDTH_ENG), 1),
            fem_fillet_peak_MPa=round(FEM_PEAK_300 * T / 300.0, 1),
            core_tension_MPa=round(T / CORE_AREA, 1),
            one_tooth_bearing_MPa=round(T / (OVERLAP * WIDTH_ENG), 1),
        ))
    return rows


def bike_row(b):
    name, cc, tq, kerb, tyre, rim, w, asp, preset = b
    r = rim * 25.4 / 2.0 + w * asp / 100.0       # mm, unloaded radius
    r_roll = r * 0.97 / 1000.0                    # m, loaded
    n_rear = REAR_SHARE * (kerb + RIDER_KG) * G
    out = dict(model=name, cc=cc, torque_Nm=tq, kerb_kg=kerb, rear_tyre=tyre,
               preset=preset, rolling_radius_mm=round(r_roll * 1000), rear_load_N=round(n_rear))
    for tag, mu in (("snow", MU_SNOW), ("ice", MU_ICE)):
        ft = mu * n_rear
        out[tag] = dict(
            traction_force_N=round(ft),
            wheel_torque_Nm=round(ft * r_roll),
            loop_tension_1strap_N=round(ft / (MU_F * THETA)),
            loop_tension_2strap_N=round(ft / 2 / (MU_F * THETA)),
        )
    hold = MU_F * THETA * RATING_N
    out["hold_1strap_N"] = round(hold)
    out["max_torque_1strap_Nm"] = round(hold * r_roll)
    out["max_torque_2strap_Nm"] = round(2 * hold * r_roll)
    t1 = out["snow"]["loop_tension_1strap_N"]
    out["snow_utilisation_1strap_pct"] = round(100.0 * t1 / RATING_N)
    return out


def main(img_dir):
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(here, "..", "out")
    rows = [bike_row(b) for b in BIKES]
    teeth = tooth_table()
    with open(os.path.join(out_dir, "loads.json"), "w") as f:
        json.dump(dict(assumptions=dict(mu_snow=MU_SNOW, mu_ice=MU_ICE, mu_f=MU_F, theta_rad=THETA,
                                        rear_share=REAR_SHARE, rider_kg=RIDER_KG, rating_N=RATING_N),
                       teeth=teeth, bikes=rows), f, indent=1)
    with open(os.path.join(out_dir, "loads.md"), "w") as f:
        f.write("| Loop tension | Per tooth | Bearing | Root shear | Fillet peak (FEM-scaled) | Core tension |\n|---|---|---|---|---|---|\n")
        for t in teeth:
            f.write(f"| {t['loop_tension_N']} N | {t['per_tooth_N']:.0f} N | {t['bearing_MPa']} MPa | "
                    f"{t['root_shear_MPa']} MPa | {t['fem_fillet_peak_MPa']} MPa | {t['core_tension_MPa']} MPa |\n")
        f.write("\n| Model | cc | Engine torque | Kerb | Rear tyre | Rear load | Traction force (snow) | Wheel torque (snow) | Loop tension, 1 strap | 2 straps | Wheel torque the lock can hold (1 / 2 straps) |\n|---|---|---|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            s = r["snow"]
            f.write(f"| {r['model']} | {r['cc']} | {r['torque_Nm']} Nm | {r['kerb_kg']} kg | {r['rear_tyre']} | {r['rear_load_N']} N | "
                    f"{s['traction_force_N']} N | {s['wheel_torque_Nm']} Nm | {s['loop_tension_1strap_N']} N | "
                    f"{s['loop_tension_2strap_N']} N | {r['max_torque_1strap_Nm']} / {r['max_torque_2strap_Nm']} Nm |\n")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(11, 5.2), dpi=140)
    x = range(len(rows))
    w = 0.38
    b1 = ax.bar([i - w / 2 for i in x], [r["snow"]["loop_tension_1strap_N"] for r in rows], w,
                label="one strap carries the whole pull (worst case)", color="#e8590c")
    b2 = ax.bar([i + w / 2 for i in x], [r["snow"]["loop_tension_2strap_N"] for r in rows], w,
                label="two straps share it", color="#ffa94d")
    ax.axhline(RATING_N, color="#222", ls="--", lw=1.4)
    ax.text(-0.45, RATING_N + 8, "PA12 lock rating, 300 N", ha="left", fontsize=9)
    for b in list(b1) + list(b2):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 5, f"{b.get_height():.0f}", ha="center", fontsize=8)
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"{r['model']}\n{r['cc']} cc" for r in rows], fontsize=8)
    ax.set_ylabel("loop tension needed per strap to hold, N")
    ax.set_title("Loop tension a strap needs so it does not slip at the snow traction limit (mu 0.35, rider 75 kg)", fontsize=10)
    ax.legend(loc="upper left", fontsize=8)
    ax.set_ylim(0, 420)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(img_dir, "loads_by_model.png"), facecolor="white")
    print(open(os.path.join(out_dir, "loads.md")).read())


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "images"))
