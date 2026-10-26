# Printing, fitting and riding guide

How to print the Hunter 350 snow straps, fit them through the wheel, and ride on them.
Read [Strength and limits](#5-strength-and-limits) before you trust them.

![Where the strap goes around each tyre and rim](docs/images/fit_diagram.png)

## 1. Pick the right file

The tyre size is printed on the sidewall. Each preset is sized for one tyre and rim.

| Your Hunter 350 | Wheel | Tyre | Print this file | Strap | Lugs |
|---|---|---|---|---|---|
| Metro (Dapper, Rebel), cast wheels | front | 110/70-17 | `out/hunter350_metro_front_PRINT_on_edge_coil.stl` | 525 mm | 4, low |
| Metro (Dapper, Rebel), cast wheels | rear | 140/70-17 | `out/hunter350_metro_rear_PRINT_on_edge_coil.stl` | 615 mm | 5 |
| Retro / Factory (spoke wheels), Base Premium | front | 100/80-17 | `out/hunter350_retro_front_PRINT_on_edge_coil.stl` | 490 mm | 4, low |
| Retro / Factory (spoke wheels), Base Premium | rear | 120/80-17 | `out/hunter350_retro_rear_PRINT_on_edge_coil.stl` | 550 mm | 5 |
| Test piece (print this first) | none | none | `out/hunter350_coupon_PRINT_on_edge.stl` | 230 mm | 2 |

Front straps have lower lugs (9 mm above the tyre instead of 10.5 mm) because the front mudguard sits closer to the tyre.

**Check the length on your bike.** The strap loops around the tyre and the rim. Wrap a string the way the strap goes (diagram above): from the inner edge of the rim on one side, over the tread, down to the inner edge of the rim on the other side, then back under the rim through a gap between spokes. Compare the string with the estimated loop below. The lock still lands on the teeth if your loop is within ±10 %.

| Preset | Estimated loop | Lock works for loops of | Spare tail after locking |
|---|---|---|---|
| METRO_FRONT | 359 mm | about 325–395 mm | about 140 mm |
| METRO_REAR | 438 mm | about 395–480 mm | about 150 mm |
| RETRO_FRONT | 325 mm | about 290–360 mm | about 140 mm |
| RETRO_REAR | 381 mm | about 345–420 mm | about 140 mm |

If your tyre or loop is different, open `cad/snow_strap_fc.py` in FreeCAD, add your tyre to `TYRES` and run it again. The lug band, the start of the teeth and the strap length are worked out from the tyre size.

## 2. Print

**Material.** Use unfilled PA12 nylon. It stays tough below −10 °C, takes up little moisture, and keeps its shape in summer heat.
- PA6/66 copolymer is a second choice, and PA6 a third: both soften and weaken when damp.
- Do not use carbon- or glass-filled nylon. It is too brittle for the pawl, which bends about 2.7 % every time it clicks.
- Do not use PLA, PETG, ABS or PC. They crack in the cold, and PLA softens when warm.
- Do not use TPU. It is too soft to hold the lock.
- Pick a PA12 whose datasheet gives an elongation at break of 20 % or more.
- For the most consistent straps (no layer lines, no warping), upload the same STL files to an SLS/MJF PA12 print service.
- The reasons, and the full ranking, are in the [README](README.md#which-filament).

**Before printing.** Dry the filament (for example 70–80 °C for 8–12 h) and print it straight from a dry box.

**Orientation.** The files are already laid out on edge, as an upright coil. Do not rotate them. Printed this way, the teeth, the pawl and the strap tension all lie in the layer plane, which is the strongest direction for FDM.

**Bed.** The coils are about 178 × 166 mm and 25.5 mm tall, so they just fit a 180 × 180 mm bed with no brim. With a brim you need a bed of at least 200 mm. The test piece is 230 mm long and goes diagonally on a 180 mm bed.

**Settings.** These are a starting point for a 0.4 mm nozzle:
- 0.15–0.2 mm layers;
- 100 % infill (or at least 5 perimeters);
- a 5 mm brim, and glue stick or the adhesive your nylon needs;
- an enclosure or at least no drafts;
- elephant's-foot compensation of 0.15–0.2 mm. The pawl's tips are 1.0 mm from the frame on the first layers.

**After printing:**
- Leave the parts in room air for a day or two. Nylon that has taken up a little moisture is much tougher.
- Check that the pawl moves: press it back with a fingernail through the open side of the head.
- Clear any strings from the slot.

**Test the lock first.** Print two test pieces and push one's tail into the other's head from the underside, teeth toward the pawl.
1. It should click tooth by tooth and must not pull back out.
2. Hang a load from the pair, or pull with a luggage scale. Aim for 30 kg (about 300 N) without slipping.
3. Repeat after 2 h in a freezer.

If the tail is very hard to push in, or slips, check the first layers and the slot for blobs before changing any parameters.

## 3. Fit

You need 5–6 straps per wheel, spread evenly around it. Fit the rear (drive) wheel first.

1. **Warm the straps** inside your jacket. Cold nylon is stiffer to thread.
2. **Pick a gap between spokes.** Keep away from the valve: on the spoked Retro wheels, never put a strap over the valve stem.
3. **Place the head.**
   - It sits flat against the side of the rim, with its slot just past the rim's inner edge.
   - Seat it properly: the rim's side face carries the front of the head, and the strength numbers in §5 assume it does.
   - On the rear wheel, use the side away from the chain. On the front wheel, use the side away from the brake disc.
   - Check this on your own bike. The side with more room between the rim and the swingarm or fork is the right one.
4. **Lay the lug band over the tread** with the lugs facing out, centred on the crown.
5. **Take the tail down the far side of the rim, under the rim through the wheel, and back** to the head.
6. **Thread the tail into the slot from the rim side**, teeth toward the pawl (toward the hub), and pull it through until it is hand-tight. Snug is enough: do not crank it with pliers. The tyre squeezes the strap every time it rolls through the contact patch.
7. **Fit all straps, roll the bike a metre, and tighten each one again.**
8. **Cut the tail** about 5 mm above the head and round off the cut corner.
9. **Check clearance before riding.** Put the bike on its stand and turn the wheel slowly by hand. Watch every strap pass:
   - the fork legs or the swingarm;
   - the brake caliper and disc, and the ABS sensor and its toothed ring;
   - the chain, sprocket and chain guard;
   - the mudguard and the tyre hugger.

   You need at least 5 mm everywhere. The head stands 19.7 mm out from the rim's side face. If anything touches, cut that strap off and move it, or don't ride.

## 4. Ride

- **Snow and ice only.** On bare tarmac the lugs wear away fast and the bike skips. Take the straps off as soon as the road is clear.
- **25 km/h at most.** Accelerate, brake and steer gently.
- **Stop after the first kilometre** and tighten every strap again. Check them every 5–10 km after that.
- **Straps are single-use.** Cut them to remove them. Don't refit a strap you have ridden on.
- **Inspect them after each ride.** Throw a strap away if it is cracked at the head, the pawl, the root or a lug, or if its teeth are worn.
- These are emergency traction aids. They do not replace winter tyres or proper chains. Check what your local rules allow.

## 5. Strength and limits

The numbers below are from a 2D and 3D finite-element check (CalculiX). They are not from a load test, so do the test-piece pull test.

| Check | Result | What it means |
|---|---|---|
| Pawl bending as each tooth clicks past (0.9 mm) | 2.7 % peak strain at the pawl's root fillet | Fine for unfilled nylon over the few dozen clicks a strap sees. Brittle filled grades would crack. |
| Force to pull the tail through | about 50 N warm, about 80 N at −20 °C | Can be pulled by hand. Use gloves or pliers in the cold. |
| Lock, 300 N shared by both pawl teeth | pawl ≤ 30 MPa; tooth-root fillet peak 39 MPa (38.5 MPa cold) | Below PA12's strength (about 45–50 MPa). |
| Lock, 300 N on one tooth (worst-case fit) | top tooth 44 MPa; lower tooth up to 87 MPa at its fillet | That small spot yields and the load moves to the other tooth. OK as an occasional overload, not as the working load. |
| Lock, 500 N shared | pawl about 51 MPa; teeth 66 MPa | Beyond PA12. |
| Without the strap core behind the pawl | the pawl would bend about 4 mm at 300 N | The strap core propping the pawl is what makes the lock work. Don't thin the strap or open the slot. |
| Head frame around the slot, 300 N, head seated on the rim (3D model) | local peaks of 43–49 MPa at the slot corners and the pawl root; everything else ≤ 36 MPa; stress across the print layers ≤ 30 MPa | About as strong as the teeth. An earlier head with a 2.4 mm floor reached 188 MPa, so the floor was thickened to 3.6 mm, the frame next to the slot widened, and a gusset added. A head hanging off the rim carries the whole pull itself. |

**Rating:** about 300 N of strap tension per strap in PA12, FDM or SLS. SLS is more consistent but not much stronger in this direction. Above that, the teeth start to yield. Dry PA6/PA66 is a little stronger, but loses that once it takes up moisture.

The weakest point is the teeth, not the pawl or the head. The FEM drove the switch to 2.5 mm teeth with 0.4 mm root fillets: they cut the peak stress by about 30 % compared with 2.0 mm teeth.

**Not checked:**
- fatigue over many wheel turns;
- impact on ice;
- UV ageing;
- the real clearance on your bike (see step 9).

## 6. Loads by model

The [README](README.md#pressure-and-torque-by-royal-enfield-model) gives the pressure on each tooth and the wheel torque for the Hunter, Classic, Meteor, Himalayan 450 and the 650 twins. In short:
- at 300 N the lock puts 150 N and 13.8 MPa of bearing pressure on each pawl tooth;
- on snow every model needs about 145–190 Nm of wheel torque, whatever its engine, because the tyre slips first;
- one strap carrying the whole pull is at 88–95 % of the rating on a 350 or Himalayan 450, and at or over it on the heavy 650s;
- with 5–6 straps per wheel, two straps share the pull and every model is at or below about 55 % of the rating.
