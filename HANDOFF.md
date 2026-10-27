# Handoff: 3D-printable snow traction strap (zip-tie style)

This file carries an earlier Claude session (claude.ai, 23 October 2026) over to an IDE session. It holds:

- the user's requests and Claude's replies, word for word;
- what was built and how;
- the verified numbers;
- the spec review;
- what is still open.

Every script and file it mentions is in this folder.

**To continue:** open this folder in your IDE and tell the assistant: *"Read HANDOFF.md and continue from where it left off."* Claude Code also loads `CLAUDE.md` automatically, and that file points here.

---

## 0. Status at handoff

> **Update, 27 October 2026:** the current design is the Hunter 350 strap v2: FreeCAD, STEP + STL, one preset per tyre, FEM-checked. **Read §8 first.**
> - §1–§7 describe the original 23 October design. Its files are in `legacy/`.
> - The v1 Hunter build from 25 October is superseded; its files are in git history.

- **Done:** an original strap was designed and delivered: parametric, and it prints without supports. The deliverables were two STL files and a preview image, all in `out/`.
- **Done:** the user then pasted a detailed production spec (§2.1) and asked whether the STL meets it, saying **"do not modify anything right just let me know"**.
  - The answer was that it only partly meets the spec; the list of deviations is in §2.2.
  - **Nothing was changed after that review.** The scripts in this folder are byte-identical to the ones that produced the delivered STLs.
- **Offered, not started (waiting on the user):**
  - Write the spec as a real CAD script (FreeCAD or CadQuery) that exports STEP and STL. The earlier sandbox blocked package installs, so it had no CAD kernel; on a normal machine this should work (§6).
  - Size the strap for the user's tire (for example 205/55 R16). No tire size has been given.
- **Unknown:**
  - the user's printer and bed size (200 × 200 mm was assumed);
  - the material;
  - whether the spec is aimed at home FDM printing, an SLS/MJF print service, or molding.

## 1. First request and what was delivered

### 1.1 Request (verbatim)

> Help me create a zip ties like this that can survive -10°c in snow create a 3d file I have attached a picture of it. It should be strong.

### 1.2 Reference images (`reference/`)

The user attached four screenshots of orange anti-skid tire traction cable ties:

| File | Shows |
|---|---|
| `01_snow_photo.jpg` | Gloved hands threading a strap through an alloy wheel in falling snow, with the lugged section across the tread. |
| `02_installation_steps.jpg` | "Installation process": 01 through the wheel hole, 02 through the lock hole, 03 lock and cut off the excess. A tire with four straps fitted. |
| `03_strap_and_wheel_fit.jpg` | The whole strap: head, lug section and long toothed tail. Open-spoke wheels ✓; closed or dually-style wheel ✗. |
| `04_features.jpg` | Close-ups labeled "Tighten teeth", "Locking port" and "Anti-slip bumps", plus the lugged section on a tire. |

The model is an original design that works the same way; it does not copy the listed product.

### 1.3 Delivered files (`out/`)

| File | What it is |
|---|---|
| `snow_strap_900mm_spiral.stl` | The full 900 mm strap, coiled into a spiral so it prints flat on a 200 × 200 mm bed. Footprint 174.4 × 161.3 mm, 12 mm tall. Binary STL in mm. |
| `snow_strap_lock_test_180mm.stl` | A straight 180 mm piece with the same head and lock, 3 lugs and 21 teeth. It checks the fit before a full strap is printed. |
| `snow_strap_preview.png` | Three views: the head and first lugs in 3D; a cross-section of the lock with the tail inserted; the coil on a 200 mm bed. |
| `info.json` | Key dimensions of the full strap, written by `run_all.py`. |

### 1.4 Reply sent with the files (verbatim)

> I made two print-ready STL files. Both are watertight meshes, and both print flat with no supports.
>
> - **snow_strap_900mm_spiral.stl** is the full 900 mm strap, coiled so it fits on a 200 × 200 mm print bed (it takes up 174 × 161 mm). It is beefier than the strap in your pictures:
>   - 12 mm wide tail with 223 ratchet teeth
>   - 16 mm wide grip section with 12 tapered lugs, each 4 mm tall
>   - a thickened root where the strap meets the head, so it doesn't snap there
>   - a two-tooth locking pawl that wedges tighter the harder the strap is pulled
> - **snow_strap_lock_test_180mm.stl** is a short version with the same lock. Print this one first to check the fit before you spend about 45 g of filament on a full strap.
>
> **Surviving –10 °C**
> - **Best material:** nylon (PA12 or PA6). It stays tough in the cold. Dry it before printing, then leave the printed part in normal room air for a day or two. Nylon that has absorbed a little moisture is much less brittle.
> - **Stronger still:** upload the spiral STL to a printing service and order it in SLS or MJF PA12. Parts made that way are about as strong as molded ones.
> - **Avoid PLA and PETG.** They crack when cold.
> - **Print settings:** 100% infill, 4 or more perimeters, and a brim to stop warping. Print it flat, exactly as the file is laid out.
>
> **Using it**
> - 900 mm fits most car and SUV tires (up to about 265 mm wide). Cut off the extra tail after locking.
> - Thread the tail in from the underside of the head, the same way as step 02 of your pictures.
> - If the test piece is too tight or too loose, tell me and I'll adjust the clearance.
> - These are emergency traction aids:
>   - Drive at 30–40 km/h or less.
>   - Make sure the strap clears the brake caliper.
>   - Use 6–10 straps per drive wheel.
>   - Carry spares, because a printed strap is weaker than a molded one.
>
> If you tell me your tire size (for example 205/55 R16), I can make the strap the exact length for it.

## 2. Spec review

### 2.1 Second request (verbatim, with invisible zero-width characters removed)

> Does the above created 3d stl file incorporate below do not modify anything right just let me know does it satisfy below requirement of not list the deviations
>
> a fully parametric, production-ready 3D CAD model (STEP and STL formats) of a heavy-duty automotive emergency anti-skid tire traction cable tie. The design consists of four monolithic, seamlessly connected sections:
>
> Locking Head (Buckle/Port):
>
> A rectangular, reinforced housing positioned at the proximal end.
>
> Internal channel dimensioned with a 0.5 mm tolerance to allow smooth feed of the strap.
>
> An integrated, resilient single-direction ratcheting pawl with a 45° lead-in ramp and a 90° locking shelf, designed to lock against the strap's ratchet teeth under high tensile load.
>
> Traction Tread / Cleat Segment (Center Section):
>
> A thickened, load-bearing band (approx. 20–25 mm wide, 3.5–4.5 mm base thickness, 200–250 mm long to span standard car tire widths).
>
> Top (Road-Facing) Surface: A repeating linear array of heavy-duty, stepped rectangular cleat lugs (8–10 mm tall, 12–15 mm wide, spaced evenly). Each lug features a chamfered base and rounded top edges to resist shearing under road friction. Between alternating lugs, include an oval weight-reduction/flex groove.
>
> Bottom (Tire-Facing) Surface: Low-profile anti-slip micro-ribs to bite into the tire tread rubber without cutting into the tire carcass.
>
> Ratcheted Strap Body:
>
> A flexible strap (approx. 12–15 mm wide, 2.0–2.5 mm thick, 650–700 mm long).
>
> The outer face features a continuous ladder of directional ratchet teeth (1.0 mm pitch, 45° slope on the insertion edge, vertical 90° stop face) that mate securely with the buckle's internal pawl.
>
> Tapered Insertion Tail:
>
> Smooth, un-toothed lead-in segment tapering to a rounded tip (30–40 mm length) to facilitate threading through wheel spokes and the locking port while wearing gloves.
>
> Total Length: ~900–950 mm.
>
> Geometry Constraint: Optimized for flat-bed additive manufacturing with no sharp interior corners to prevent notch-stress failure."
>
> Component Anatomy & Design Details
>
> Locking Port (Head):
>
> Must withstand severe centrifugal and outward radial pulling forces. The entry opening needs a slight lead-in chamfer. The internal locking pawl requires sufficient spring travel to flex as each tooth passes, but enough root thickness so it will not shear backward under tension.
>
> Anti-Slip Cleats (Tread Zone):
>
> The raised rectangular blocks take the full vehicle weight and ground impact on snow/ice. The base where the block meets the flat strap must have fillets (minimum 1.0–1.5 mm radius) to prevent layer-line delamination under shear stress.
>
> Ratchet Teeth:
>
> Positioned on the exterior surface. They should be sharp and well-defined along the locking face so they don't cam out of the pawl when torqued down.
>
> Strap Flange:
>
> The transition zone where the thick cleat section tapers down into the thin strap must be a gradual ramp to prevent stress concentration.

### 2.2 Answer given (verbatim)

> **No, it doesn't fully meet this spec.** The overall layout matches, but many of the specified dimensions and features are different or missing. Nothing has been changed.
>
> **Formats and overall**
> - Only STL is provided. There is no STEP and no true parametric CAD model; it was generated by a Python script in my workspace, which you don't have.
> - There's an extra 40 mm plain neck (with a thickened root) between the head and the tread, so it's not strictly four sections.
> - It has sharp interior corners throughout, at the lug bases, tooth roots, pawl root and head floor. The spec asks for none.
>
> **Locking head**
> - The channel clearance is 0.4 mm on the sides and 0.35 mm at the pawl, not 0.5 mm.
> - The pawl's lead-in ramp is about 30°, not 45°. The 90° locking shelf does match.
> - There's no lead-in chamfer at the entry opening.
>
> **Traction tread**
> - It's 16 mm wide, not 20–25 mm.
> - The base is 3.0 mm thick, not 3.5–4.5 mm.
> - The lugs are 4 mm tall, not 8–10 mm.
> - The lugs are single tapered blocks, not stepped. They are 15 mm wide at the base, narrowing to 11 mm at the top.
> - The lug bases have no 1.0–1.5 mm fillets, and the lug tops have no rounded edges.
> - There are no oval flex grooves between the lugs.
> - The bottom is flat, with no micro-ribs.
>
> **Ratcheted strap**
> - The toothed length is about 560 mm, not 650–700 mm.
> - The tooth pitch is 2.5 mm, not 1.0 mm.
> - The insertion slope is about 32°, not 45°.
> - The teeth are 1.2 mm tall on a 2.2 mm core, so the strap is 3.4 mm thick at the tooth tips.
>
> **Tail**
> - It's 25 mm long, not 30–40 mm.
> - The tip is square, not rounded.
>
> **What does match:** it's one piece, prints flat with no supports, and is 900 mm long overall. The head is a rectangular housing at the end with a one-way pawl and a 90° shelf. The tread is 240 mm long with evenly spaced lugs. The strap is 12 mm wide with a 2.2 mm core, and the teeth are on the outer face with vertical stop faces. The tail is smooth and tapered, and there's a gradual 10 mm ramp from the tread down to the strap.
>
> I can't install a CAD kernel in this workspace, so I can't make a real STEP file here. I could write the full spec as a FreeCAD script that you run yourself; it would build the model and export both STEP and STL.

**Correction found while preparing this handoff, and passed on to the user with it:** the lugs are **16 mm** wide at the base, not 15 mm. Their sloped sides start right at the edges of the 16 mm tread, so the base spans the full width. The 11 mm top width is correct.

## 3. The design as built

### 3.1 Axes and print orientation

The axes below describe the straight layout, before the spiral warp. Units are mm.

- `s` (the x axis) runs along the strap. The head sits at s < 0, with its front face at s = 0.
- `y` runs across the strap, centered on 0.
- `z` points up, with the print bed at z = 0.

The part prints flat on its z = 0 face with no supports. The steepest overhangs are the pawl faces, at 17° and 28.6° from vertical.

### 3.2 Sections along the strap (full strap, default parameters)

| s (mm) | Section | Width | Thickness | Notes |
|---|---|---|---|---|
| −13.35 to 0 | Locking head | 17.8 | 12.0 | Slot and pawl, see §3.3 |
| 0 to 12 | Root ramp | 12 | 7.0 → 2.6 | Linear; reinforces the joint with the head |
| 12 to 40 | Neck | 12 | 2.6 | Plain |
| 40 to 50 | Transition | 12 → 16 | 2.6 → 3.0 | Linear ramp |
| 50 to 290 | Tread | 16 | 3.0 | 12 lugs centered at s = 60, 80 … 280, see §3.4 |
| 290 to 300 | Flange | 16 → 12 | 3.0 → 2.2 | Linear ramp down to the strap |
| 300 to 861.65 | Toothed strap | 12 | 2.2 core + 1.2 teeth | 223 teeth at 2.5 mm pitch from s = 301 to 858.5, see §3.5 |
| 861.65 to 886.65 | Tip | 12 → 6 | 2.2 → 1.6 | No teeth; square end |

The total is 900 mm: a 13.35 mm head plus 886.65 mm of strap. The ramps are straight lines with a crease at each end, not smooth blends.

### 3.3 Locking head

The dimensions here use head-local `x`, which converts as s = x − 10.85, together with `z`.

- **Outer box:** x from −2.5 to 10.85, y ±8.9, z from 0 to 12. The walls are 2.5 mm thick and the floor 2.4 mm.
- **Chamber:** x from 0 (the back wall) to 8.35 (the front wall), y ±6.4, open at the top.
- **Floor:** covers x from 0 to 4.5.
- **Entry slot** through the floor, x from 4.5 to 8.35:
  - Along x it is 3.85 mm, for a strap 3.4 mm thick over the teeth (0.45 mm clearance).
  - Across y it is 12.8 mm, for the 12 mm strap (0.4 mm per side).
- **Pawl:** a single leaning cantilever.
  - It is 11.8 mm wide (y ±5.9), leaving 0.5 mm on each side.
  - It rises from a 2.4 mm root on the floor (x 1.1 to 3.5) to z = 11.6.
  - Its outline in x–z is `(1.1,2.4) → (3.5,2.4) → (4.6,6.0) → (4.6,6.6) → (5.8,8.8) → (5.8,9.1) → (4.6,9.1) → (5.8,11.3) → (5.8,11.6) → (2.6,11.6) →` back to `(1.1,2.4)`.
  - That outline gives two teeth, each 1.2 mm deep, with a lead-in ramp at 28.6° from vertical. Each tooth ends in a flat shelf facing up: one at z = 9.1 and one at the top face, z = 11.6.
  - Its back face leans 9.3° from vertical, so the pawl thickens toward its root: it is about 2.4 mm thick behind the upper tooth valley and 2.9 mm behind the lower one. At the top it has 2.6 mm of free space behind it to flex into.
- **With the tail inserted:**
  - The tail's smooth face rests against the front wall (x = 8.35), and its teeth face the pawl.
  - The strap's tooth tips sit at x = 4.95 and the pawl tips at x = 5.8, so they overlap by 0.85 mm.
  - The pawl tips clear the strap core by 0.35 mm.
- **How it locks:**
  1. The tail goes in from the underside (the bed side) and up through the slot, as in step 02 of the reference pictures.
  2. Pulling the tail up tightens the strap. Each tooth's ramp pushes the pawl back, and the pawl flexes to let it pass.
  3. Under load, the loop pulls the tail back down. The teeth's vertical lock faces, which point down at that point, land on the pawl's shelves.
  4. The pawl is anchored at its bottom and leans toward the strap, so the load wedges it in tighter instead of prying it open.

### 3.4 Lugs

- Each lug is a single tapered block, 4 mm tall on the 3.0 mm tread (7.0 mm in total).
- Along the strap it is 10 mm long at the base and 6 mm at the top, with end ramps at 26.6° from vertical.
- Across the strap it is 16 mm wide at the base (the full tread width) and 11 mm at the top, with sides at 32° from vertical.
- The lugs repeat every 20 mm, which leaves 10 mm between their bases.
- All edges are sharp: there are no fillets, rounding or steps. The underside is flat.

### 3.5 Ratchet teeth and tip

The teeth are on the top face in the flat layout, which becomes the outer face of the loop in use. Each 2.5 mm pitch is made up of:

- a vertical lock face on the head side (−s). It is modeled as a 0.02 mm-wide step so the loft cross-section stays single-valued;
- a flat crest 0.28 mm long;
- a ramp 1.9 mm long, at 32.3° to the strap surface;
- a flat valley 0.3 mm long.

The teeth are 1.2 mm tall on a 2.2 mm core.

The tip has no teeth. Over its 25 mm length it narrows to 6 mm wide and 1.6 mm thick, and it ends square.

### 3.6 Spiral print layout

`spiral_warp()` bends the straight model onto an Archimedean spiral:

- The pitch is 19.5 mm.
- The spiral starts at radius 83.4 mm at s = 0 and winds counter-clockwise inward to 38 mm at the tip.
- The head sits on the outside, placed rigidly along the spiral's tangent at s = 0.
- XY is re-centered on the origin.

The frame is right-handed, so normals keep pointing outward. The smallest gap between neighboring turns is 5.47 mm, and the head clears the nearest turn by 5.77 mm.

## 4. Code

### 4.1 Files

| File | Role |
|---|---|
| `strap.py` | The generator. `DEF` holds the default parameters. `build(params)` returns `(V, T, info)`: vertices, triangles and key dimensions in the straight layout. `check(V, T)` validates the mesh, `write_stl(path, V, T)` writes binary STL, and `spiral_warp(V, L)` returns the coiled vertices plus spiral info. |
| `run_all.py` | The full pipeline. Builds and checks the full strap, coils it and checks the gaps between turns, then builds the test piece. Writes both STLs, `out/meshes.npz` and `out/info.json`. |
| `run_test.py` | A quick check of the 180 mm test piece. Prints the mesh check, `info` and the bounding box; writes no files. |
| `render.py` | Draws `out/snow_strap_preview.png` from `out/meshes.npz`, so run `run_all.py` first. Also prints the head clearance. |
| `requirements.txt` | numpy; scipy (`cKDTree` for the gap checks); matplotlib (the preview). |

### 4.2 Running it

```bash
cd snow-strap                      # the scripts use paths relative to this folder, and out/ must exist
python -m pip install -r requirements.txt
python run_test.py                 # under a second
python run_all.py                  # 1–2 s; rewrites out/*.stl, out/meshes.npz, out/info.json
python render.py                   # a few seconds; rewrites out/snow_strap_preview.png
```

Expected output from `run_all.py`:

- full straight strap: 21474 triangles, 10737 vertices, `bad_edges` 0, `degenerate` 0, volume about 40359 mm³;
- spiral bounding box 174.4 × 161.3 × 12 mm;
- `min gap between turns (mm): 5.47`;
- `vol full cm3 40.4 test 9.8`.

With the parameters unchanged, the STLs come out byte-identical to the delivered ones. This was tested with Python 3.13, numpy 2.5.3, scipy 1.18.1 and matplotlib 3.11.2.

### 4.3 How `build()` makes the mesh (no CAD kernel, no CSG)

- **Head.** Outlines in the x–z plane are extruded across five y bands:
  - the outer walls, as a full rectangle;
  - the 0.5 mm gaps beside the pawl, as an L shape (back wall plus floor) plus the front wall;
  - the center band, as the same L shape with the pawl attached, plus the front wall.

  Cap faces close the bands where they meet: at y = ±8.9 (outside), ±6.4 (slot walls) and ±5.9 (pawl sides). The head's front face is a U-shaped polygon that wraps around the strap's root cross-section.
- **Strap.** A loft of one 6-vertex cross-section, `[(-w/2,0),(w/2,0),(w/2,Tb),(hw,Tb+hl),(-hw,Tb+hl),(-w/2,Tb)]`. `Tb` is the band thickness plus the tooth height and `hl` is the lug height. Stations sit at most 0.8 mm apart, plus one at every feature breakpoint. The far end is closed with a fan cap.
- **Stitching.** Any vertex lying inside another polygon's edge is inserted into that edge, which removes T-junctions. Each polygon is then triangulated by ear clipping. Vertices are rounded to 6 decimals and merged.
- **Validation.** `check()` requires every directed edge to occur exactly once, and its reverse exactly once, so the mesh is closed and consistently oriented. It also reports the volume, the smallest triangle area and the number of degenerate triangles.
- **Bug fixed earlier.** Ear clipping failed with "no ear found" when rounded candidate vertices were inserted beside unrounded edge endpoints. The fix rounds the polygon vertices first and skips candidates within 1e-5 mm of either endpoint; see the `da`/`db` lines in `build()`.

### 4.4 Parameters (`DEF` in `strap.py`, mm)

| Name | Default | Meaning |
|---|---|---|
| `total_len` | 900 | Overall length, including the head |
| `W` | 12 | Strap width (neck and toothed strap) |
| `root_T`, `root_len` | 7.0, 12 | Thickness where the strap leaves the head, and the length over which it ramps down to `T_neck` |
| `T_neck`, `neck_len` | 2.6, 40 | Neck thickness, and the s at which the neck ends |
| `trans_len` | 10 | Length of each ramp into and out of the tread |
| `W_grip`, `T_grip`, `grip_len` | 16, 3.0, 240 | Tread width, base thickness and length |
| `lug_pitch` | 20 | Lug spacing, center to center |
| `lug_base_len`, `lug_top_len` | 10, 6 | Lug length along the strap at the base and at the top |
| `lug_h` | 4 | Lug height above the tread |
| `lug_inset` | 0.5 | Extra inset of the lug top from the tread edges, beyond the side slope |
| `T_core`, `tooth_h`, `pitch` | 2.2, 1.2, 2.5 | Core thickness of the toothed strap, tooth height and tooth pitch |
| `tip_len`, `tip_W`, `tip_T` | 25, 6, 1.6 | Tip length, and the width and thickness at its end |
| `H`, `wall`, `floor_h` | 12, 2.5, 2.4 | Head height, wall thickness and floor thickness |
| `clear_y` | 0.4 | Slot clearance on each side, across the strap |
| `clear_x` | 0.35 | Clearance from the pawl tip to the strap core |
| `entry_clear` | 0.45 | Floor-slot clearance over the strap's thickness at the teeth |
| `pawl_gap_y` | 0.5 | Gap on each side between the pawl and the slot wall |
| `pawl_t` | 2.0 | Pawl thickness behind the tooth valleys, measured at the top; it gets thicker toward the root |
| `pawl_back_gap` | 2.6 | Free space behind the pawl for it to flex into |
| `pawl_teeth` | 2 | Number of pawl teeth |
| `root_back_gap`, `root_w` | 1.1, 2.4 | Distance from the chamber's back wall to the start of the pawl root, and the root's width on the floor |
| `max_ds` | 0.8 | Largest spacing between loft stations |

The test piece uses these overrides: `dict(total_len=180, neck_len=15, trans_len=8, grip_len=60, tip_len=20)`.

If you change parameters, update two hard-coded spots as well:

- `render.py` draws its tail overlay with `Tc=2.2, h=1.2, p=2.5`;
- `run_all.py` uses widths of 12 and 16 in its gap check between turns.

### 4.5 Limits of this approach

The strap is a single fixed 6-vertex cross-section lofted along a straight line. None of the following can be added without rewriting the mesher:

- fillets and rounded edges;
- stepped lugs;
- oval grooves through the band;
- ribs on the underside;
- a rounded tip;
- chamfers inside the head.

Those are exactly what the spec asks for (§2.2), which is why a real CAD kernel is the suggested route (§6).

## 5. Verified numbers

| Item | Value |
|---|---|
| Full strap, straight | 21,474 triangles, 10,737 vertices, 0 bad edges, 0 degenerate, 40,359 mm³ |
| Mass | about 41 g in PA12, 46 g in PA6, 49 g in TPU |
| Spiral | 174.4 × 161.3 × 12 mm; 0 bad edges, 0 degenerate; smallest gap between turns 5.47 mm; head clearance 5.77 mm |
| Test piece | 3,474 triangles, 1,737 vertices, 0 bad edges, 9,799 mm³; s from −13.35 to 166.65, y ±8.9, z 0 to 12 |
| Lock | 0.85 mm tooth overlap; 0.35 mm from pawl tip to core; 0.4 mm side clearance; 0.45 mm entry clearance |

## 6. Why there is no STEP, and what to use now

The earlier session ran in a sandbox whose network proxy blocked PyPI and npm. No CAD kernel (CadQuery/OCP, build123d or FreeCAD) could be installed, so the mesh was built with numpy alone and only STL could be written.

On your own machine, `python -m pip install cadquery` (or `build123d`), or FreeCAD's built-in Python, can build a real solid and export both STEP and STL from the same script.

## 7. Notes for a rebuild to the spec (only if the user asks for one)

Raise these points with the user before building, because the spec leaves them open or contradicts itself:

1. **Length budget.** The sections add up to more than the total allows:
   - head (about 15 mm) + tread 200–250 + strap 650–700 + tail 30–40 = about 895–1,005 mm;
   - the total is supposed to be about 900–950 mm;
   - so the upper ends of the ranges can't all be used at once. For example, 15 + 220 + 660 + 35 = 930 mm, before adding the flange ramp.
2. **1.0 mm tooth pitch.** Sharp teeth at a 1.0 mm pitch with 90° stop faces are finer than a 0.4 mm FDM nozzle prints cleanly. They would need SLS/MJF printing, or a larger pitch.
3. **Ambiguities.** Does "2.0–2.5 mm thick" include the teeth? Is the 0.5 mm channel tolerance per side or in total?
4. **Bed fit.** The current coil pitch of 19.5 mm was sized so the 16 mm tread clears the 12 mm strap on the next turn. A 20–25 mm tread needs a wider pitch, which makes the coil bigger, and it may no longer fit on 200 × 200 mm unless the pitch changes along the strap. Confirm the bed size first.
5. **Strength.** No one has calculated or tested whether the head survives "severe centrifugal and outward radial pulling forces". Say so plainly rather than calling the part production-ready.

## 8. Hunter 350 strap v2 (sessions of 25–27 October 2026, FreeCAD)

### 8.1 Requests (verbatim)

> make the best of both strong can be fitted on hunter 350 tyre over the rims try to incooperate the best i have freecad already running

> go ahead continue

> go ahead complete it

"Both" means the strap from §1 and the production spec in §2.1. The user also circled three features in new reference photos: stepped lugs, oval recesses between the lugs, and the buckle head.

### 8.2 What exists now

| Path | What it is |
|---|---|
| `cad/snow_strap_fc.py` | The generator: FreeCAD 1.1, OCC 7.8 B-rep. It runs as a GUI macro (one `Part::FeaturePython` per preset, every parameter a property) or headless (`freecadcmd cad/snow_strap_fc.py`, about 100 s). |
| `cad/render_previews.py` | Plain numpy + matplotlib. It makes `preview_<preset>.png`, `fit_diagram.png` and `lock_section.png`, and writes `out/*_installed_pose.stl`. |
| `out/` | For each preset: `.step`, `_straight.stl`, `_PRINT_on_edge_coil.stl` (coupon: `_PRINT_on_edge.stl`) and `_installed_pose.stl`. Plus `hunter350_snow_straps.FCStd`, `info.json` (all numbers and checks) and `head_section.json`. |
| `FITTING.md` | The guide: which file, print settings, fitting steps, clearance check, riding rules, strength table. |
| `README.md`, `docs/` | Updated for v2: the page's models, specs, 360° video and poster. `docs/viewer.js` now frames each model by its bounding sphere. |

### 8.3 Design: what came from where

| Feature | Source | v2 value |
|---|---|---|
| Lock | First strap (§3.3), upgraded | Open-top chamber; floor-rooted two-tooth wedge pawl, 2° lean, 1.8 mm root with 0.8 mm root fillets. The pawl teeth mirror the strap teeth. 0.75 mm engagement; pawl tip to strap core 0.45 mm. Under load the strap core props the pawl; without the prop it would deflect about 4 mm at 300 N. |
| Head | Spec, plus a printability ring | 14.6 × 25.5 × 19.7 mm, with a 3.6 mm floor. Bed-band U-frame (5.0 mm) with a pillar and a 2.6 mm gusset ramping the floor into it. Solid 4.5 mm +y wall, 0.5 mm channel clearances, 0.8 mm entry chamfer. Slot, chamber and channel corners rounded at 1.2 / 0.7 / 0.5 mm. The convex pillar corner stays sharp, because OCC cannot round it next to the gusset. Root gusset 12.5 mm high, running 17 mm into the strap. These dimensions come from the 3D FEM (§8.5). |
| Teeth | Spec 45°/90°, pitch changed | 2.5 mm pitch, 1.2 mm tall, 0.5 mm crest, 45° ramp, 90° stop face, 0.4 mm root and valley fillets. They start 15 mm past the far rim corner. 1.0 mm pitch (the spec) cannot be printed sharp by FDM. 2.0 mm pitch only left room for 0.25 mm fillets (§8.5). |
| Tread | Spec + photos | Band 22 mm wide, 2.5 mm thick between lugs. Stepped full-width lugs at 24 mm pitch: lower tier 6 × 5 mm, upper tier 3 × 3 mm (front 3 × 1.5 mm), so 10.5 / 9 mm above the tyre. Fillets 2.0 / 0.8 / 0.6 / 1.0 mm. Oval dishes 0.3 mm deep in every gap. Staggered grip dots on the tyre side (3 mm domes, 0.55 mm tall, 5 mm pitch, 90–115 per strap) replace the V-grooves. 12 mm radius in-ramp and 15 mm flange ramp. |
| Tip | Spec | 35 mm long, tapering to 7 mm wide and 1.8 mm thick, rounded. |
| Printing | New | On edge as an upright coil. Flat y becomes print Z and every section shares the bed edge (y = −11), so tension, teeth and pawl flex all lie in the layer plane. Coil radius 80 mm, 2 mm between turns. The coil warp keeps the neutral-axis length; the head prints straight. This fixes the §3.6 flat spiral, which bent the strap edgewise and could not be straightened. |
| Sizing | New | One preset per tyre (§8.4). |
| Use | New | Single-use: cut to remove. There is no release tab. |

### 8.4 Sizing model

The strap's path around a tyre-plus-rim section is modelled as:

- the tyre contour C, from rim lip to rim lip: a half-ellipse crown plus straight lower sidewalls;
- the rim's side face w on each side: 33 mm for cast wheels, 25 mm for spoke wheels;
- the crossing X under the rim, between the two lower corners: 2·√(lip_x² + dip²).

The head sits at the rim's outer lower corner (`s_corner = −3.25`), on the side away from the chain (rear) or the disc (front). From that:

- the lug band is centred on the crown;
- the teeth start at the far corner + 15 mm;
- the lock sits about 17 mm up the channel once the loop closes (z_engage);
- `total_len = ceil5(1.1·s_lock + 100 + head)`.

`fit_report()` checks that the lock stays on the teeth for loops 10 % shorter or longer.

| Preset | Tyre | Loop | Strap | Lugs | Teeth | Volume | Tail after lock |
|---|---|---|---|---|---|---|---|
| METRO_FRONT | 110/70-17, MT3.00 cast | 359 mm | 525 mm | 4 (9 mm) | 78 | 31.8 cm³ | 137 mm |
| METRO_REAR | 140/70-17, ~MT3.50 cast | 438 mm | 615 mm | 5 (10.5 mm) | 87 | 36.9 cm³ | 148 mm |
| RETRO_FRONT | 100/80-17, 2.15 spoke | 325 mm | 490 mm | 4 (9 mm) | 68 | 30.3 cm³ | 137 mm |
| RETRO_REAR | 120/80-17, 2.50 spoke | 381 mm | 550 mm | 5 (10.5 mm) | 73 | 34.2 cm³ | 141 mm |
| COUPON | none | none | 230 mm | 2 | 34 | 18.1 cm³ | none |

Mass in PA12 is about 1.01 g per cm³. The coils are 177–178.5 × 164–166 mm and 25.5 mm tall. The smallest gap between turns is 2.0 mm (METRO_REAR); the shorter straps make only about one turn.

### 8.5 Verification

**CAD**
- Every preset is one valid solid.
- Meshes are closed and consistently oriented after `drop_fins()`. OCC leaves zero-length edges where fillets end on 2D-rounded profile corners, and the tessellator turns them into zero-volume fins.
- The straight STL is built from a split B-rep (`max_seg = 3`) and refined along x, so it bends smoothly into the coil without fan triangles.

**FEM (CalculiX 2.22 from FreeCAD)**
- 2D plane-strain NLGEOM model of the pawl section at y = 0, 6-node triangles. The strap-core prop uses active-set contact: the tip nodes are held at the 0.45 mm gap, and nodes that pull are released.
- Material: PA12 at E = 1500 MPa (2500 MPa cold), ν = 0.4.
- Loads are spread over the 14.5 mm engaged width (click force over the 20 mm pawl).
- Click: lateral force plus (1 + μ)/(1 − μ) times as much vertical force (μ = 0.3), scaled to 0.9 mm tip travel, as in the beam model.
- Mesh convergence: click strain 2.67 / 2.69 % (16 k / 83 k nodes). Linear fillet peak 82.6 / 81.7 MPa (17 k / 88 k nodes).
- Scripts are in the session scratchpad (`fem/`), not the repo.

| Case (final geometry) | Pawl root / body (von Mises) | Teeth peak | Notes |
|---|---|---|---|
| Click, 0.9 mm | 2.68 % max principal strain at the front root fillet | none | Pull-through 48 N warm, 80 N cold |
| 300 N on the top tooth | 25 / 28 MPa | 44 MPa tension, 96 MPa compression (valley fillet) | Prop force 39 N |
| 300 N shared by both teeth | 23 / 30 MPa | 39 MPa tension (lower shelf-root fillet) | Prop force 54 N |
| 300 N shared, cold (E 2500) | 22 / 31 MPa | 38.5 MPa | none |
| 300 N on the lower tooth only | 24 / 33 MPa | 87 MPa local peak | Local yield, then the load shares onto the other tooth |
| 500 N shared | 51 / 51 MPa (59 MPa compression at the root) | 66 MPa | Beyond FDM PA12 |
| 3D head seated on the rim, 300 N | Head frame 43–49 MPa local peaks (slot corner, pawl root at the floor); walls ≤ 36 MPa; across print layers ≤ 30 MPa | 69 MPa in the teeth zone (over-constrained tips) | Rim carries 395–400 N; max displacement 0.7–0.8 mm |
| 3D head seated on the rim, 500 N | Head frame 68–72 MPa; walls ≤ 57 MPa | 88 MPa | Beyond PA12 |

**Tooth-root variant study** (300 N shared / lower tooth only / click strain):

| Variant | Shared | Lower only | Click |
|---|---|---|---|
| 2.0 mm pitch, 0.25 mm fillets | 54 MPa | about 110 MPa | 2.67 % |
| 0.35 mm shelf fillet | 49 MPa | 104 MPa | 2.68 % |
| 2.2 mm pitch | 42 MPa | 92 MPa | 2.78 % |
| **2.5 mm pitch, head 18.5 mm (chosen)** | **38–39 MPa** | **84–87 MPa** | **2.73 %** |

**3D head model.**
- 160–183 k-node C3D10 meshes (gmsh Delaunay; HXT hangs on this geometry). The root is cut at s = 10.
- Holding the head only at that cut (floating) is unrealistic. Seated: the tail pulls the pawl axially inward and the strap body pulls the head radially outward, so the rim's side face carries the front of the head (s ≥ −3.25). The pawl tips are held at the 0.45 mm prop.
- The floor ring's peak at 300 N fell with each change:
  - 188 MPa with a 2.4 mm floor and a sharp pillar root;
  - 116–140 MPa with the gusset;
  - 64–83 MPa with a 3.6 mm floor, a 5 mm bed band and an 18.5 → 19.7 mm head (same pawl free length, so the same click strain);
  - 43–49 MPa with the gusset lengthened and 1.2 mm slot corners.

**Rating:** about 300 N of strap tension for PA12, FDM or SLS. SLS is more consistent but not much stronger in-plane. Above that the teeth yield. Dry PA6/PA66 is a little stronger but loses that with moisture, so a molded part is the way to go higher. The limit is the teeth, not the head.

### 8.6 Printability review (on edge, y up)

- **No supports.** All features are vertical walls in print, except:
  - the grip-dot domes (40° overhang);
  - the dish walls (≤ 5°);
  - the entry chamfer (45°);
  - the tip end's bottom round (r 3.5; small and harmless).
- **Bridges.**
  - The +y side wall bridges the chamber: 8.6 mm span, 1.0 mm above the pawl top.
  - The slot top bridges 4.1 mm.
- **Gaps.**
  - Pawl back to back wall: 1.3–1.8 mm.
  - Pawl tips to pillar: raised from 0.8 to 1.0 mm, because elephant's foot could fuse them on the first layers.
  - Between coil turns: 2.0 mm.
- **Fit.** The coil just fits a 180 mm bed without a brim (178.5 mm at most) and is 25.5 mm tall. With a 5 mm brim it needs about 200 mm.
- **Material.** Unfilled PA12 or PA6, dried. Not carbon- or glass-filled: the pawl strain is about 2.7 %. Not PLA, PETG or TPU.

### 8.7 Not verified (tell the user)

- **Which side the Hunter 350's chain and rear caliper are on.** A web search found the brake sizes (300 mm front disc, 270 mm rear disc on the Metro, dual-channel ABS) but not the side. The fitting rule is "side away from the chain (rear) or the disc (front)", and the user must check it.
- **The section model's dimensions:**
  - rim widths (the 140/70 rear is assumed on about MT3.50);
  - rim depth (w = 33 / 25 mm);
  - the dip under the rim.
- **Clearances.** The head stands 19.7 mm out from the rim face, and the lugs are 10.5 / 9 mm. Clearance to the fork, swingarm, mudguard, caliper and ABS ring is not checked.
- **No physical tests.** No load, fatigue, cold-impact or ice-impact test has been done. The test-piece pull test in FITTING.md §2 is the first real check.

### 8.8 Rebuild

```powershell
& "D:\Software\FreeCAD\bin\freecadcmd.exe" cad\snow_strap_fc.py           # out/: STEP, STL, coils, FCStd, info.json
& "D:\Software\FreeCAD\bin\python.exe" cad\render_previews.py out docs\images   # previews, diagrams, installed poses
```

To refresh the project page:
- copy `out/hunter350_metro_rear_installed_pose.stl` to `docs/models/hunter350_rear_loop.stl`, and the Metro straight STLs over the rear and front straight models;
- serve `docs/` and capture `index.html?render&m=loop` with `setAngle()` in headless Chrome (144 frames, 1048 × 720);
- encode with `ffmpeg -framerate 24 … -c:v libx264 -pix_fmt yuv420p`.
