---
name: delta-animated-skins
description: Measure Delta controller-skin artwork and write the results into a skin's info.json. Cap frames to 0.1 px or pt (inside the dark well line, never the well), from PDF vectors or raw art; each is both the press-animation frame and the button frame, with touch padding via extendedEdges. Also cuts a caps-removed background and cap assets matching those frames, writes frames, padding, screens and assets into info.json, shares caps across poses and devices, installs the skin into a core (rebuilds Standard.deltaskin), and publishes it to Download Skins with Duo reps and previews. An optional first step removes Illustrator gridlines. Use whenever someone hands over skin PNGs/PDFs to map, measure, or pull x/y/width/height, find buttons, caps or wells, set touch areas or padding, animate buttons, cut cap assets or backgrounds, fix mappings for any pose (iPhone, Duo, iPad), fix cap PDFs Delta draws shifted or not at all, remove gridlines or seams, or update an info.json - even if they don't say "skin" or "mapping".
---

# Delta skin mapping

Three jobs, done in this order. A PDF of the art is the best source; without one, everything works from the raw PNGs. No highlight boxes or inspector screenshots are needed.

First, if Delta will draw an Illustrator PDF and it shows gridlines in Preview or Delta, clean it up (Step 0).

1. **Cap frames (Part 1):** everything inside the thin dark well line but not the line itself, to a tenth of a pixel. This one frame does double duty: it's what animates on press, and it's the button's `frame` in info.json.
2. **Background and cap assets (Part 2):** from a PDF, the art with the caps removed, and each cap cut to exactly its frame. Skip this when the user supplies them.
3. **info.json (Part 3):** write the frames, padding, screens, background and cap assets into the skin's JSON with a minimal, verifiable diff.

Then, if asked: **share caps** across poses and devices (Part 4), **install** the result into the core for device testing (Part 5), and **publish** it as a downloadable skin (Part 6).

**Look at the repo before choosing units or formats.** Find the most recent animated skin in the other cores (`grep -l '"asset"' Cores/*/…/Controller Skin/info.json`, including uncommitted work) and copy its conventions. As of November 2026 that's SNES: point-based mapping, frames to 0.1 pt, a vector background PDF plus one vector PDF per cap.

**A touch area is the cap frame plus padding.** There's no separate input frame to measure. The hit area is the cap frame grown by `extendedEdges`, and the padding is the user's choice, usually a standard amount per button kind. Don't measure the well or the recess to size touch areas.

## Anatomy of a button

Moving outward from the center, every button has these layers:

| Layer | What it looks like | In the cap frame |
|---|---|---|
| Cap | Light face, darker bevel toward the bottom | ✓ |
| Well line | Thin, near-black ring (about 2.6 px on big buttons, about 1 px on small ones at 3×) | ✗ |
| Recess | A darker-pink inset ring around the well, smooth (flat or a gentle gradient) | ✗ |
| Body or drop shadow | Device surface; the shadow under a button is darker than the recess | ✗ |

L and R bumpers have no well line or recess. They're segments of the hinge bar, separated from its middle section by a seam.

## Ground rules (apply to every job)

- **Measure the original files on disk, never a chat preview.** Chat clients downscale images over 2000 px and re-encode them, so open the file from disk and check its real size and format. Lossless PNG or a PDF is required, and a PDF is best: its vector paths give every edge exactly (Part 1).
- **Confirm the scale.** iPhone art is 3×: each image dimension should be exactly 3 × the point frame (951 × 669 pt → 2853 × 2007 px). PDFs exported from the design tool are often 10× (pdfimages gives the page raster). **Always measure the highest-resolution source.** A 1× raster put three N64 buttons 1 px off.
- **Pixel convention.** Pixel *k* covers [k, k+1). Frames are positions on that continuous axis: x and y are the left and top edges (x = 1810.6 starts 0.6 of the way into pixel 1810), and w = right edge − left edge.
- **Frames are decimal, to 0.1 px.** See Precision, below.
- **Check every number twice.** Draw the box back onto a 6–10× zoomed crop, and print the pixel values across each edge. Buttons of the same kind in a pose should measure the same size: within 0.1 px from vectors, within about 0.5 px from pixels.
- **Never hand-edit a value without re-running the check.** If a check finds an error, fix the method or the input and recompute.
- **Report judgment calls explicitly,** including L/R, screens, rounding, background/art mismatches, duplicates and placeholders.
- **Report odd values, but don't change them.** Pairs that are 1 px off (L 126 vs R 127, Select 81 vs Start 80, caps 55 × 56) are usually real design nudges. Flag them and leave the numbers alone. Edge rounding can also leave a square cap 0.1 px off square (Duo D-pad 389.7 × 389.6); leave that too.

## Precision: frames to a tenth of a pixel

**Delta uses decimal frames as written.** DeltaCore reads every frame as `[String: CGFloat]` (`ControllerSkin.swift`), divides it by `mappingSize` and scales it to the view, with no rounding or `.integral` anywhere in layout or hit-testing. A cap asset is a `UIImageView` with the default `scaleToFill`, stretched to exactly its frame (`ControllerView.swift`); PNG and PDF assets both work. On press the cap shrinks 2 pt on each side.

**Rules:**

- **Write frames to 0.1 px.** Hundredths measured no better than tenths. Whole pixels leave edges up to 0.5 px off the art.
- **Round the edges, not x, y, w and h separately.** Round x, y, x + w and y + h to 0.1, then take w and h from the rounded edges (`rounded()`, Appendix A). Every edge then lands within 0.05 px of the measurement; rounding w on its own can leave the right edge 0.1 px off.
- **Measure from vectors when there's a PDF** (Part 1). The pixel method is only good to about ±0.3 px. Write tenths from it anyway, since coarser rounding only adds error, but don't read meaning into 0.1 px differences.
- **Cut each cap asset to exactly its frame** (Part 2). Delta stretches the asset to fill the frame, so an asset cut to a whole-pixel box, or 0–2 px larger than the cap, throws the decimals away.

**Evidence (Duo inner portrait, October 2026).** For each precision, each cap was cut to that frame, composited over the background at phone resolution and compared with the full art. Worst pixel, in 8-bit levels (0–255):

| Cap | Phone | Whole px | Tenths | Hundredths |
|---|---|---|---|---|
| A | 440 pt, 3× | 85 | 51 | 54 |
| A | 402 pt, 3× | 73 | 48 | 50 |
| Start | 440 pt, 3× | 78 | 59 | 59 |
| Start | 402 pt, 3× | 85 | 44 | 42 |
| D-pad | 440 pt, 3× | 37 | 34 | 37 |
| D-pad | 402 pt, 3× | 36 | 30 | 32 |

- **The worst pixel is on the cap outline,** where a sliver of the well line or the hole shows if cap and line don't meet. Tenths cut it by 25–50% on the round caps, and by less on the D-pad.
- **Inside the cap, whole pixels are slightly cleaner** (99th percentile 18 vs 22 levels on A, 4 vs 9 on the D-pad, at 440 pt), because a whole-pixel asset's pixels line up with the background's. Tenths trade a few levels of softness inside for a correct edge.
- **Hundredths change nothing measurable.**
- **Simulate at phone resolution, not 1:1** (`composite_check`, Appendix A). A phone never shows the art 1:1 (2007 px of art across 1206–1320 screen pixels), and at 1:1 a whole-pixel asset isn't resampled at all, which makes whole pixels look cleaner inside the cap than they will on a phone.
- **Cut a fresh asset for each precision you compare.** Reusing one asset in every frame adds stretching error to the coarser frames; it made whole pixels look about twice as bad as they are (worst pixel 150–200).

**Not yet confirmed on device.** As of October 2026, decimal frames are confirmed in DeltaCore's source and in simulation only. Check them with Skin Debugging (Part 3) and update this line.

**PDF skins map in points, not pixels.** When the skin's assets are PDFs (`resizable`), `mappingSize` is the PDF page size in points and frames are in points to 0.1 pt (SNES, Genesis). The pixel rules above carry over with s = 1 in Part 1 step 4. 0.1 pt is 0.3 px at 3×, but because each vector cap PDF is cut to exactly its rounded frame, its art still lands where it was; rounding only moves the cap's outline by ≤0.05 pt against the well line. If the PDF's page size differs from the old `mappingSize` (Genesis portrait: 320×250 vs. 320×254), use the page size and say so.

## Step 0: Remove gridlines from Illustrator PDFs (rasterize only the gradient meshes)

Do this first, before exporting or measuring anything, whenever a PDF shows thin seams ("gridlines") across highlights or shading in Preview or in Delta. It isn't needed when the PDF is only rendered to PNGs with MuPDF (Part 2), because MuPDF blends the patches seamlessly.

**Cause.** Illustrator saves each gradient mesh as a grid of small patches (PDF shading types 4–7; Illustrator uses type 7). Apple's renderer, which Preview and Delta both use, draws each patch separately and leaves a hairline seam where neighbors meet. MuPDF and poppler blend the patches seamlessly, so they never show the problem. Check in Preview, or through the CoreGraphics harness in Appendix C.

**Fix: replace each mesh with an image of just that mesh, and change nothing else.**

1. **Find every mesh draw.** Walk the page content, every form and every soft-mask group (an ExtGState's `/SMask /G`), recursively. Meshes hide in all three. The Duo inner portrait had 52: 12 on the page, 14 inside forms and 26 inside soft masks, where they're the opacity fades behind highlights.
2. **Render each mesh on its own, in its own coordinates.** Use the mesh's `/Decode` range as the canvas, find the area the mesh actually covers, then render that area at 6 px per point. That's twice the 3× asset scale, so zooming in stays smooth. **Supersample it:** render at 4 × 6 px/pt and area-average the premultiplied samples down to 6 px/pt (Appendix D does this). MuPDF draws a mesh's *outer boundary* without anti-aliasing. Where that boundary isn't hidden under a clip, as with Genesis's cap bevels, a plain 6 px/pt image shows it as a stair-step. MuPDF returns premultiplied color, so un-premultiply after averaging.
3. **Keep the color space.** RGB meshes keep their own ICC profile (sRGB). Gray meshes, which live in soft masks, become DeviceGray.
4. **Put the image inside a small form, and draw that form in place of the mesh.** Replace only the `sh` operator, with `q <cm> /MeshImg Do Q`, where the `cm` maps the form's unit square onto the mesh's box. The clip that shapes the mesh, the mask that fades it and the outlines around it are untouched, so every edge is still vector.
5. **Delete the mesh resources nothing draws any more,** and confirm none are left anywhere in the file.

`rasterize_meshes.py` (Appendix D) does all of this: `python rasterize_meshes.py in.pdf out.pdf`. If the PDF's page box also needs rebasing (Appendix C), rasterize the meshes first.

**What not to do.** Each of these was tried and failed:

- **Rasterizing whole layers:** the mesh together with its clip or the shape it masks, or Illustrator's effect forms. The crisp outlines get baked into pixels, and the cap's highlight edge and the black well ring went jagged when zoomed in.
- **Rasterizing Illustrator's blur, shadow and glow effects.** They're already images and never caused gridlines. Leave them alone.
- **Drawing the mesh image directly, with its transparency as the image's own soft mask.** An image's soft mask replaces whatever soft mask is already in effect. One highlight lost its opacity fade and turned solid white. Wrapping the image in a form keeps both masks working.

**Verify:**

- **No shading of type 4–7 is left** in the page, in any form or in any soft mask.
- **At 3×, the result matches the original.** On the Duo inner portrait, 99.9% of pixels were within 2 of 255 brightness levels. The few that differed were single-pixel slivers along the top edge of each button's highlight. Genesis (November 2026) reached 99.91–99.96% on iPad and 99.5–99.8% on iPhone. The leftover differences are 1 px lines along mesh boundaries: anti-aliased in the cleaned file, hard-edged in MuPDF's render of the original. Those are fine.
- **Diagnose before accepting a low score:** zoom (24×) into the worst cells of a diff map. If you see steps that get finer when you raise `--scale`, it's the aliased mesh boundary, so supersample. If the score doesn't move with `--scale` and the image is shifted, it's a placement error (Appendix D).
- **Prove the fix through CoreGraphics,** not just MuPDF. Render the original and the cleaned file with the harness (Appendix C) and look at a button cluster: the original shows seams across every cap; the cleaned one shows none.
- **At 16× on a button, the edges match.** The well ring and the highlight edge should match the original; on the Duo, 99% of pixels were within 3 levels.
- **Open it in Preview at high zoom,** or render it with the CoreGraphics harness. There should be no seams, and the edges should be as crisp as in the original.

## Step 1: Inventory and validate inputs

1. List every file with its pixel size and mode, and map each one to a pose and orientation. Check every representation in info.json too: some reuse another pose's art (iPad split-view portrait draws `ipad_portrait.pdf`), and some hold stale items copied from another core (Genesis split-view portrait had SNES's layout: `select`, an X/Y diamond, buttons where L/R go).
2. Sort files into these kinds:
   - **PDF of the full art:** the best source. Measure its vectors (Part 1) and cut the background and cap assets from it (Part 2).
   - **Full art:** caps present. This is what you measure when there's no PDF.
   - **Background:** caps removed and the cap holes filled dark. This is what actually renders.
   - **Cap assets:** for example `iphone_small_a.png`.
3. Re-uploads arrive with `_1` suffixes. Compare their pixels (not their bytes) to the originals before assuming anything has changed.
4. Check that each background lines up with its full art. Diff a 300 px corner region (with no caps in it) at offsets (0,0), (1,0), (0,1) and (1,1). Our backgrounds lined up at (0,0) but were **1 px wider and taller**, with an anti-aliased edge row and column. Decide on `mappingSize` deliberately and say what you chose (see Part 3). A background you render in Part 2 is exactly the art's size, so this check is for supplied backgrounds.
5. **Compare where the background puts each button with where the full art puts it.** In a background, the cap is gone but the well is still there, filled dark. Measure each dark hole's bounding box and compare it with the button's frame in the full art. Every button of the same kind should show the same offsets. **An outlier means the background and the art disagree, and the background wins,** because it's what users see and tap. Shift that button's cap frame by the outlier's offset and flag it. The splitView Start well was 6 px lower in the background.
6. **Compare poses' block structures** (the operator sequence of each top-level block, matched with `difflib`). Poses of one design usually line up block for block with a fixed offset, so you map one pose and transfer the block numbers. Whatever doesn't line up deserves a look. Genesis edge-to-edge landscape had a **stray duplicate D-pad** (24 extra blocks, 1 pt left of the real one) that showed as a doubled edge. Keep such art in the background as supplied, since the real well hides the duplicate cap, and flag it for removal in the source.
7. **Check every PDF asset's page origin.** Run `python rebase_pdf_origin.py --check` (Appendix C) on each PDF the skin references. Cap PDFs cut from a larger artboard can keep the artboard position as their page box, and Delta then draws the cap shifted or not at all. Record each box first, because it's exactly where the cap was cut from (a free asset-fit cross-check), then rebase the file to (0, 0).

## Part 1: Cap frames (inside the well, not the well)

**Definition.** The cap is everything inside the thin dark well line. The line and everything outside it stay static. The frame is the cap's bounding box to 0.1 px, and it's also the button's `frame` in info.json; the touch padding goes on separately (Part 3).

### From a PDF: the vector paths (preferred)

The PDF gives every edge exactly, so measure there whenever the art comes as a PDF. Appendix E has the code.

1. **Split the page into its top-level `q … Q` blocks** and render each block alone to see what it draws. Note which blocks draw each cap; Part 2 cuts the background and assets from the same list.
2. **Find the path that marks each edge:**
   - **Round caps:** the cap face circle. Its box is the inner edge of the well line. **Rule: the cap outline is the largest shape inside the well that's concentric with it.** On Genesis A/B/C a rim ring sits around the face. The ring's outer circle is concentric with the well; the face is offset 0.35 pt down inside it to fake lighting. So the frame is the rim's outer circle, which keeps the rim's top highlight on the cap. Take the union of the face and rim boxes.
   - **D-pad:** the cap's base fill, the cross inside the dark well cross. Some D-pads are a **disc** with the cross raised on it (Genesis): then the disc is the cap, measured like a round cap, and the cross, centre dimple and diagonal arrows all ride on it.
   - **Round single buttons** (iPad Genesis's purple Menu): measure like a round cap. Layers drawn *between* two faces (a blurred dark shading) belong to the cap.
   - **L / R:** the bar's clip, top to bottom, from the seam with the middle bar out to the page edge.
   - **Screens:** the transparent window, which is the inner edge of the black border.
3. **Take the path's exact bounding box** in page space: apply the `cm` transforms, and include the curves' extremes rather than their control points.
4. **Convert to top-down pixels:** x = x0 · s, y = (page height − y1) · s, w = (x1 − x0) · s, h = (y1 − y0) · s, with s = 3 for iPhone art drawn in points.
5. **Round to 0.1 px** (Precision, above), and cut assets to the rounded frame, since that's the frame Delta stretches them into.

**Watch for:**

- **A cap's drawing can spill past its edge.** The Duo round caps' bevel ran about 0.2 pt past the face circle at the bottom left. The frame is the face circle, not the box around everything the cap's blocks draw.
- **A highlight can reach over the well line.** On the DS iPad D-pad (October 2026), the rim highlights along the top edges start 1.6 pt outside the base cross and cover the inner half of the well line, so the line looks thinner there. Still measure the frame from the base fill, and report the overhang. Anything outside the frame gets dropped (Part 2). If it's big or bright, ask whether the frame should grow to take it in. Ask before the frames go into info.json, because the user may lock the mapping after testing.
- **One block can draw both well and cap.** The Duo D-pad's well block also drew the cap's pink base. The base is the cap (Part 2 splits the block).
- **One block can draw one button's cap and the next button's well.** Genesis drew each button's *letter* inside the next button's well block (A's letter with B's well, and so on). The D-pad cross's shadow shared a block with the ring's static white arrows and dots. List the block under the cap it partly belongs to, and split it by group (Part 2).
- **Find the well as the block's largest path,** not its first: a split block can start with the previous button's letter.
- **Contact sheets beat bounding boxes.** Render each top-level block alone on a loud background (magenta) in a labelled grid, one sheet per region. That's how letters, shadows and decorations get assigned correctly.

### From pixels: the coverage rule

Use this when there's no PDF. It lands within about ±0.3 px of the true edge.

**Pixel rule.** A pixel belongs to the cap if the line covers less than half of it. Along a ray from the cap's center outward:

- **Line color** is the darkest pixel of the dip. Don't use a global threshold.
- **Cap reference color, c,** is the previous pixel, extrapolated by the local slope clipped to −15…+5. This allows for the bevel.
- **Coverage** = (c − p) / (c − line). The first pixel with coverage above 0.08 is where the line starts. The cap edge lies (1 − coverage) of the way into that pixel, measured from its inner side. Keep the fraction; don't round to the pixel.

**How to apply the rule to each shape:**

| Element | How to measure |
|---|---|
| Round caps | Cast rays left, right, up and down from the center at offsets −2…+2. Take the median per side (the mean of the middle two on an even count). Recenter on the result and run again. Cap ray length at about 1.25 × the radius. |
| D-pad | The arm ends are straight. For each side, scan rows covering ±11% of the width, starting 7% inside the edge. Inner edge = dip centroid − line width ÷ 2. Take the median. |
| L / R bumpers | There's no well, so the frame is the bumper itself: its silhouette from the hinge gap above to the bar's bottom edge, out to the seam with the middle bar. **Exclude** the seam pixel and the 1 px outline at the image edge. Padding goes on through `extendedEdges` like any other button. Nothing animates unless L/R get assets. |
| Screens (output frames) | The transparent window inside the black border: a component of alpha < 128 that doesn't touch the image edge. Take each edge's fraction from its edge pixels' alpha, the same way as coverage. Alpha edges can read up to 0.5 px off, so check the result against 4:3 (the Duo windows are exactly 1104 × 828 and 960 × 720). If the L/R bar crosses a screen, the window comes out 1 px short of 4:3, so flag it. |

**Expect edges to read slightly outward.** The cap, its bevel, the line and the recess are stacked anti-aliased layers, and each adds a little coverage at the edge, so the line seems to start early and caps come out large. On the Duo inner portrait, edges read 0.2–0.3 px outside the vector edges on a 3× render of the PDF, and up to 0.45 px on the older PNG. Screen windows taken from alpha were off by up to 0.5 px.

**Pitfalls:**

- **A global luminance threshold (< 140) stops at the cap's bevel, not the well.** Bottom edges came out about 8 px short.
- **A flat two-pixel dark core broke the dip analysis,** because the baseline got taken from the core. Step back over a flat core first.
- **Small buttons have lines about 1 px thick** that straddle two pixels. Expect ±0.5 px and use medians.
- **Identical caps measure a few tenths apart from pixels.** Caps about 155.5 px across came out 155 or 156 under the old whole-pixel rule. From vectors they agree exactly. Don't force identical caps to equal sizes from pixels; report the spread.
- **Highlight boxes or inspector panels, if you get them, are only a cross-check, never the source.** Inspector panels with a 90° or 180° rotation field measure from a rotated frame, so convert before comparing.

**Verification (required):**

0. **From vectors, assert the well line on all four sides** (well box minus frame box, per side) and print it. Genesis caps came out uniform to ±0.002 pt (D-pad 1.0, A/B/C 0.62, X/Y/Z 0.98 pt on iPhone). A side that's thin, negative or uneven means you picked the wrong path or the wrong well.
1. Make zoomed crops (6–10×) with each box drawn on, and print the pixel values across every edge. The box should sit on the inner edge of the line all the way round, on the seam for L/R, and on the window edge for screens.
2. Run the background check from Step 1.
3. **Composite check.** Stretch each cap asset into its decimal frame, composite it over the background at phone resolution, and compare with the full art (`composite_check`, Appendix A). Errors should sit only on the cap outline; on the Duo the worst pixel was 30–60 levels. Error along one side means the frame or the asset is off that way.
4. **Asset fit, for supplied assets.** Composite each asset over the background at whole-pixel offsets ±5 px (`asset_fit`, Appendix A) and compare with the full art. The best offset shows where the asset was cut from. Use this to pick small vs. large assets and to report mismatches between asset and frame. An asset that doesn't cover exactly its frame throws the decimals away, so recut it in Part 2 if there's a PDF.

## Part 2: Background and cap assets (from a PDF)

Skip this part when the user supplies the background and cap assets. Check those with the composite check (Part 1) instead, and report any asset that doesn't cover exactly its frame.

**Each cap asset covers exactly its frame.** Delta stretches the asset to fill the frame, so the asset must hold exactly the art inside x … x + w and y … y + h. Its pixel size is w × h rounded (141 × 141 for a 140.8 × 140.8 frame); Delta's stretch undoes the 0.1% difference. Appendix E has the code.

1. **Background:** render every top-level block except the cap blocks (Part 1) at exactly `mappingSize` (3× for iPhone art). Render the full art the same way, with the same renderer, so the two line up pixel for pixel.
   - **No part of a cap block stays in the background,** not even what it paints outside the cap's outline. The background is static, so whatever a cap block leaves there stays put in the well when the cap shrinks on press.
   - **Don't split a spilling block at the outline.** One DS iPad build did exactly that: the cap got the inside, and the background kept the outside. The D-pad's rim highlights then left light lines in the well above three arms when it was pressed, which the user caught in the simulator.
   - **The spill goes to the cap,** cut only by the frame (step 3). Anything outside the frame is dropped.
   - **The one exception is a block that also draws unrelated art away from the cap.** Split it by operator, as in step 2, so only that art stays in the background. Don't split it by clipping the background copy to "outside the outline": CoreGraphics leaves a sliver along the outline, which shows as a ring on press (N64 B, October 2026).
2. **Split blocks that draw both well and cap.** The Duo D-pad's well block drew the dark cross and the cap's pink base together. The cap gets the block's outer `q`, its page clip (`re W n`), the color space and color, the base's fill and the closing `Q`; the background keeps the rest.
   - **General method (Genesis):** split at the block's depth-1 `q … Q` groups.
     - Both halves keep the block's ungrouped ops (outer `q`, clip, colour and gs state, `Q`).
     - Render each group alone with those ops. A group whose rendered centre falls inside the outline of *the cap the block is listed under* goes to that cap; the rest stay in the background.
     - Test only against that one cap. The next button's well is centred on the next button, so testing against every cap would hand it over.
     - Use a circle test for round caps, not the box: the D-pad ring's dots sit inside the disc's bounding box.
     - A group that renders nothing follows the group before it. Print every assignment and read it.
3. **Cap assets:** render only that cap's blocks, with the frame mapped onto exactly round(w) × round(h) pixels and the render clipped to the frame (`cut_cap`, Appendix E). It asserts the image comes out that size, starting at (0, 0).
   - **For PDF skins, cut vector cap PDFs instead (`cut_cap_pdf`, Appendix E):**
     - Take a copy of the page drawing only the cap's ops.
     - Set its MediaBox to the rounded frame in page space, and drop Crop/Bleed/Trim/ArtBox, PieceInfo and Metadata.
     - Remove unreferenced resources, then **rebase the page box to (0, 0) by rewriting coordinates** (`Rebaser`, Appendix C). Never add a wrapper `cm`: it breaks soft masks in CoreGraphics.
     - The background is the same: a vector PDF of every op the caps didn't take, at the full page box.
     - Resulting sizes: 60–110 KB per cap, about 100 KB per background.
4. **Check each asset:** everything outside the cap is fully transparent (a round cap's corners, the D-pad's notches), and none of the well line is in it.
5. **Check each hole in the background.** Render the background alone, zoom into every cap's hole, and find the brightest pixel inside it.
   - **Expected:** only the well's own dark fill and the cap's drop shadow.
   - **A light line or sliver is cap art left behind,** and it will show in the ring the press animation opens. On the DS iPad D-pads, the brightest pixel in the well was 199 levels in a well that's 30.
   - **Then composite the caps pressed** (2 units smaller per side) over the background and look again.
   - **Measure the uncovered ring with the real outlines** (circle or pill), between the frame outline and the pressed outline. Keep ≥0.6 pt clear of the pressed cap's edge: at 2× a light cap's anti-aliased edge bleeds about 1 px, and a 0.3 pt margin read 54–75 levels on iPad X/Y while the well itself was 0–3. A rectangle ring is wrong; it picks up the pressed cap's own rim.
6. **Check what lies outside each asset's outline:** count the opaque pixels beyond the outline and print their distance and maximum luma. Dark spill (a cross's drop shadow, a shading layer, anti-aliasing) is harmless on a black well. Anything light is a problem.
7. **Run the end-to-end CoreGraphics check (Appendix F):** compose the background and every cap through DeltaCore's PDF code and compare with the art drawn through the same code. Classify errors by whether they sit on an *edge of the art*: Genesis had every pixel above 16 levels on an art edge, with off-edge max 10–12. The edge errors come from Delta's own pipeline (it rasterizes at a rounded-up pixel size, then the image view stretches into the fractional frame). Off-edge errors mean lost soft masks or highlights.

**Report these choices:**

- **What the holes show.** The background shows whatever the PDF draws under the cap (on the Duo, the well's own dark fill rather than a flat color). It's visible only in the ring the press animation opens.
- **Spill outside the frame gets clipped.** On the Duo, the round caps' bevel ran about 0.2 pt past the face circle at the bottom left, so the line looks a hair thicker there.
  - **On the DS iPad D-pad,** the rim above the up arm ran 1.6 pt past the frame. Without it, the well line there reads as 3 pt of dark instead of 1.4 pt of dark plus 1.6 pt of light.
  - **Report the size of anything dropped.** If it's visible, offer to grow the frame to take it in and take the same amount off that side's `extendedEdges`, so the hit area stays the same. A pixel outside the frame can't be light at rest and dark when pressed.
- **Shared assets.** Caps whose frames are the same size can share one asset. The Duo's Start, Select and Menu used the Start render (under 0.5 levels apart on average).
- **New names.** Give new assets per-pose names (`duo_inner_portrait_a.png`), so other poses keep the shared assets they use.
- **Resolution.** Keep assets at the art's own scale (3×). Higher-resolution assets haven't been tested on device.

## Part 3: Writing into info.json

**Model structure** (Duo outer/closed portrait is the reference):

```json
"portrait": {
  "assets": { "large": "duo_outer_portrait_background.png" },
  "items": [
    {
      "asset": { "name": "iphone_small_a.png" },
      "inputs": ["a"],
      "frame": { "x": 1186, "y": 1711, "width": 142, "height": 142 },
      "extendedEdges": { "top": 12, "bottom": 12, "left": 0, "right": 72 }
    },
    { "inputs": ["l"], "frame": { "x": 1, "y": 744, "width": 293, "height": 106 } },
    { "inputs": { "x": "touchScreenX", "y": "touchScreenY" }, "frame": { "...": "= touch screen outputFrame" } }
  ],
  "screens": [
    { "inputFrame": { "x": 0, "y": 0,   "width": 256, "height": 192 }, "outputFrame": { "...": "top screen window" } },
    { "inputFrame": { "x": 0, "y": 192, "width": 256, "height": 192 }, "outputFrame": { "...": "touch screen window" } }
  ],
  "mappingSize": { "width": 1398, "height": 2034 },
  "extendedEdges": { "top": 60, "bottom": 60, "left": 60, "right": 60 }
}
```

**Where each measurement goes:**

| Item | `frame` | Padding (`extendedEdges`) |
|---|---|---|
| Buttons (D-pad, A/B/X/Y, Start/Select/Menu) | Cap frame (Part 1). When the pose has cap art, `asset` is the first key. | The user's standard padding for that button kind. |
| L / R | Bumper frame (Part 1); no asset | The user's padding. |
| Touch screen | The touch screen's `outputFrame`, exactly, so a tap maps 1:1 onto game pixels; no asset | Usually 0. |

**Padding is the user's call.** The hit area is `frame` + `extendedEdges`, so touch size is set entirely by the padding. Use the values the user gives; if they haven't given any, keep the existing `extendedEdges` and list that as an assumption. Never grow `frame` to make a bigger target, and never derive padding from the art. Cap frames with the Duo skin's original `extendedEdges` registered taps correctly on device.

**Overlapping hit areas fire both buttons.** `ButtonsInputView.items(at:)` returns every item whose `extendedFrame` contains the touch, and item padding overrides the representation's edge by edge (`ControllerSkin.swift`). So when a redesign moves buttons, **the old padding is stale.** After the Genesis 3→6-button change, keeping it overlapped A/X, B/Y, C/Z and X/Y/Z, and Menu's old `right: 30` ran into Start.
- **Compute the overlaps and ask the user** (padding is still their call). Offer: keep the existing values; fit to the new layout; or strip per-item padding.
- **"Fit to new layout" (`solve_padding`, Appendix A), the option chosen for Genesis:**
  - Every edge starts at the item's existing outward value (the larger of its override and the representation default; new items start at the default).
  - Each overlapping pair splits the gap between the two caps, on the axis where the caps don't overlap, rounded down to 0.1 so they meet without overlapping. Compare with a 1e-6 tolerance; float noise like 219.20000000000002 otherwise loops forever.
  - Diagonal neighbours end up thin (A/B 0.3 pt, C/Z 0.9 pt on iPhone) because rectangles can't split a diagonal. Say so, and render a hit-area preview (green frames, red frame + padding) for the user.

**Other rules:**

- In `screens`, `inputFrame` y = 0 is the top DS screen and y = 192 is the bottom (touch) screen. In splitView, the top screen has `"placement": "app"` and no `outputFrame`, and the controller screen has `"placement": "controller"`.
- **Choose assets by cap size, not by pose name.** Small assets fit caps about 142 px (47 pt) wide: outer portrait, outer landscape and **inner portrait**. Large assets fit caps about 155.5 px (52 pt) wide: inner landscape and splitView. Confirm with the asset fit from Part 1. Assets cut in Part 2 fit their own frames, so this applies only to supplied assets.
- **Units.** Frames are in the art's pixel units, to 0.1 px (`"x": 1810.6`), and `mappingSize` is the art's pixel size. When converting a representation from points (or 2×), multiply **every** `extendedEdges` value by the same factor: item, screen and representation level.
- **Backgrounds were 1 px larger than the art.** We kept `mappingSize` = art size, which leaves an error under 1 px; setting it to the background's size would make the mapping exactly 1:1. Say which you chose. A background rendered in Part 2 is exactly the art's size, so the question doesn't arise.

**Editing rules:**

- **Edit the text; don't re-serialize the file.** The file mixes hand formatting, so re-serializing creates a noisy diff. Patch only the numbers, strings and keys that change, working from the end of the file backward. For structural edits (inserting an `asset` key), use a span-aware parser that records each value's start and end offsets.
  - When a value is rewritten wholesale (a new `items` array), replace **the key's whole line** through the end of the value, and indent it like a sibling key (`"assets"`). Some old `"items"` key lines are mis-indented, and keeping them makes the new block look broken.
  - Match the file's own style: Genesis writes `"key": value`, while SNES writes `"key" : value`.
  - Validate that every *other* representation key (`extendedEdges`, `translucent`) and every top-level key comes out equal.
- **iPad split-view portrait mirrors standard portrait** when it draws the same art. SNES does this: same background, caps, frames and padding, with mapping 1024×429 rather than the old 800×335.
- **Write numbers cleanly:** at most one decimal place, whole numbers as integers (`1815`, not `1815.0`), and no float noise (`389.70000000000005`). `tidy()` in Appendix A does this.
- **Validate before delivering:**
  - The file parses.
  - The result equals the intended object built separately in code.
  - Every other representation and top-level key is byte-identical.
  - Every referenced file exists.
  - Every PDF asset's page box starts at (0, 0) (`rebase_pdf_origin.py --check`, Appendix C).
  - Every frame lies inside `mappingSize`, and every value has at most one decimal place.
  - Each new frame's center is within a few pixels of the old frame's center, which catches swapped buttons.
- **Leave alone** the skin's name and identifier, other devices, harmless keys (`"translucent": false` is the default), and any asset names you weren't given. Flag placeholders instead of guessing. Keep the top-level `"debug"` a Bool (`true` or `false`); anything else and the skin fails to load.

**Check on device with Skin Debugging.** In Delta, turn on Settings → Experimental Features → Skin Debugging:

- **Show Hit Targets** draws each item's hit area (frame plus padding) as a red box.
- **Ignore Padding** shrinks the boxes to the bare frames. It shrinks the real hit areas too, so turn it off when you're done.
- **What to look for.** Caps draw on top of the boxes, and screens get none. With Ignore Padding on, each box's edges should meet the inner edge of the well line on all four sides of a round cap and at all four arm ends of the D-pad. A box that overlaps the line on one side and falls short on the other is off toward the overlap. Then press each button: the ring that opens around the cap should be even all the way round.

## Part 4: Sharing caps across poses and devices

Cut once, reuse wherever the art matches: Delta stretches each PDF cap to its frame. Genesis (November 2026) went from 42 PDFs to 26: 7 backgrounds and 19 caps.

**Where sharing usually works:**
- **Edge-to-edge and standard** poses of one orientation: same art and size; only the positions differ.
- **iPad split-view landscape and iPad portrait** when they're the same art (same block structure, plus or minus a few blocks).
- **The D-pad** often matches across orientations.
- **iPhone and iPad** when the iPad art is a uniform scale of the iPhone art. Genesis was exactly 1.8×: caps, well lines and effects. Check the ratios of frames and well lines; they should all be equal.

**Where it doesn't:** different art. Genesis landscape letters are white and portrait letters dark and embossed; pills of a different shape, or carrying text; a round Menu that exists on only one device.

**How to test a share honestly:**
- Compose the *target* scene with the shared cap through CoreGraphics (Appendix F), then compare it with the target's art *and* with the target's own caps.
- Check inside the caps, away from edges: Genesis iPad caps in the iPhone scenes scored p99 1–5 levels, the same as the iPhone's own.
- **Cut from the larger art** and scale down. Rasterized meshes and effect bitmaps then carry more detail than needed. Scaling the small caps *up* makes the comparison look worse than the art really differs; I first misread the Genesis effects as tuned separately for that reason.
- Same-size pairs can also be pixel-compared directly; a hairline-only difference (≤2% of pixels at 12×, along edges) means the same art.

**Aspect must match:** DeltaCore aspect-fits a PDF into its target (`AVMakeRect`), so a shared cap whose aspect differs from a frame leaves slack at one edge. Assert below 0.3%: 0.1 pt rounding of small iPhone frames gives up to 0.25%, ≤0.04 pt.

**Naming:** device-neutral `<button>_<orientation>.pdf` (`a_portrait.pdf`, `start_landscape.pdf`) and a single `dpad.pdf`, following N64's shared `thumbstick_portrait.pdf`. Caps that exist in one pose family only keep pose names (`iphone_portrait_start.pdf`, `ipad_portrait_menu.pdf`). Backgrounds stay per pose.

**Coupling:** sharing holds only while the art stays identical (or exactly scaled). Write that down for the designer: if one device's caps change, split them again.

## Part 5: Installing into a core for device testing

- **The app bundles `Standard.deltaskin`, not the loose files.** In a core's `Package.swift` and Xcode project, only that zip is copied (`.copy("Resources/Controller Skin/Standard.deltaskin")`). Loose files alone never reach the device.
- **Do what SNES does:** put the loose `info.json` and PDFs in `Controller Skin/`, then rebuild `Standard.deltaskin` as a **flat, deflated zip**: `info.json` first, then the PDFs; no folders, no `.DS_Store`, no `__MACOSX`. Read it back and assert every entry is byte-identical to its loose file.
- **Before replacing anything, check git:** the designer's new full-art PDFs are often uncommitted edits, so deleting them loses them. Move them to the deliverables folder (`full-art-original/`), and confirm they're byte-identical to what you worked from.
- Tell the user to do a clean build, and to reinstall the app if the old skin still shows.

## Part 6: Publishing as a downloadable skin

Delta's **Download Skins** screen (Settings → Skins → a system → a display tab → More; `DownloadableSkinsView.swift`) lists skins from a catalog, `skins/remote-skins.json` on the CDN. Entries are grouped by game type, and each has `identifier`, `name`, `url` (the skin's loose `info.json`) and `downloadURL` (the `.deltaskin`). Don't confuse it with `skins/skins.json`, which silently replaces a *bundled* standard skin by identifier (`RemoteControllerSkinManager`).

**Give the skin its own name and identifier.**
- A skin built as a core's standard skin carries `"identifier": "com.delta.<system>.standard"`.
- When a skin is installed, Delta takes its identifier from the skin's own `info.json` (`ControllerSkin+Configuring.swift`), not from the catalog. If you publish the skin unchanged, installing it adds a second record with the bundled skin's identifier.
- The screen's checkmark compares against the catalog's identifier, so a skin whose two identifiers differ never shows as installed.
- Set `name` and `identifier` to match the catalog entry. Genesis 6-button shipped to the catalog still marked as standard, and was caught later.
- Anyone who downloaded the old version has to download it again.

**Older builds match representations exactly.**
- Before November 2026, the screen listed a skin only if `info.json` had exactly `representations[device][displayType][orientation]`. It ignored DeltaCore's fallbacks.
- So on iPhone Duo, which uses the `iphone/inner`, `iphone/outer` and `iphone/splitView` traits, no skin without Duo reps appeared, even though it would play fine once installed.
- The fix is to try the picker's fallback traits in order. For builds without it, add explicit Duo reps that are verbatim copies of what DeltaCore already falls back to (`ControllerSkinProtocol.supportedTraits(for:)`). No new assets are needed:

| Add | Copy of | Why |
|---|---|---|
| `iphone.inner` | `ipad.standard` | Inner falls back to outer, then iPad standard, then iPhone edgeToEdge, then standard |
| `iphone.outer` | `iphone.standard` | Outer skips edgeToEdge |
| `iphone.splitView` | `ipad.splitView` | Duo split view falls back to iPad split view |

- Rendering doesn't change: the game was already drawing those reps on a Duo. Only the item IDs change, because they're derived from the traits.
- Don't add `cover`. Delta doesn't support preferences for it yet.

**What to upload.** The screen reads the loose `info.json` to build the list. Its preview is the matched rep's `preview` if there is one, otherwise `assets["large"]` (or the first asset), fetched from the same folder as that `info.json`. Installing uses the `.deltaskin`. So the upload folder needs the loose `info.json`, the `.deltaskin`, the loose background PDFs, and any preview images. Deliver those as one folder that mirrors the server path.

**Preview images (animated skins only).**
- An animated skin's background has its caps cut out, so on its own it previews as an empty controller. Give each rep in the *loose* `info.json` a `"preview"` key that names a PNG with the caps drawn in, uploaded next to that `info.json`.
- Static skins don't need one: their background already shows the buttons. Neither does the in-app skin picker, which draws the caps itself (`ControllerSkinProtocol.previewImage`). `preview` only matters on Download Skins.
- `preview` sits next to `assets`, `items` and `mappingSize`, not inside `assets`. `assets` only takes DeltaCore's `AssetSize` keys (`small`, `medium`, `large`, `resizable`). DeltaCore ignores unknown rep keys, so `preview` is harmless anywhere.
- Add it to the loose `info.json` only, not the one in the `.deltaskin`. The two then intentionally differ by the `preview` keys. Say so in the deliverables' NOTES.md, so a later re-upload keeps them.
- Draw the caps at rest with `compose` (Appendix F), using each rep's background and every cap item's asset in its frame. Skip thumbsticks, as `previewImage` does. Render every image 1200 px wide, the widest the list ever shows one (~400 pt at 3× on iPhone; the iPad form sheet is narrower). Reps that draw the same background and caps in the same frames share one file, named `preview_<background pose>.png` (e.g. `preview_ipad_portrait.png` for iPad standard and split-view portrait plus Duo inner and split-view portrait).
- Check each preview against the full art drawn through `compose --art` at the same size, as in Appendix F.
- Appendix H has the scripts.

**Editing and checking:**
- If `json.dumps(d, indent=2)` reproduces `info.json` byte for byte (Genesis did, with no trailing newline), edit it as data. Otherwise patch it as text (Part 3).
- Diff against the previous version: only `name`, `identifier`, the added reps and (in the loose copy) the `preview` keys should change.
- Run the screen's lookup in Python for every trait, including the Duo ones (`iphone` × `inner`/`outer`/`splitView` × both orientations). The lookup is `preview`, then `assets["large"]`, then the first asset. Confirm each one finds a rep and a preview file that's in the upload folder.
- After uploading, download each new or changed file from the CDN and `cmp` it against the upload folder.
- Rebuild the `.deltaskin` (Part 5) and compare it with the live one. The PDFs should be byte-identical; only `info.json` changes.
- To test on the Duo simulator ("iPhone Duo", iOS 27.1 or later), run `xcrun simctl openurl <udid> "file:///…/Name.deltaskin"`. Delta imports it, and the skin should appear under its own name next to the standard skin on the Inside, Outside and Split View tabs.
- The simulator can't show what an older build lists, so ask the user to check Download Skins on a real Duo after uploading.

## Naming conventions

Taken from the skins in Delta's cores (`Cores/*/…/Controller Skin/`, October 29, 2026). File names are case-sensitive on device and must match info.json exactly. Everything is lowercase, with words joined by underscores.

**Pose names:**

| Representation | Pose |
|---|---|
| `iphone/standard/portrait`, `landscape` | `iphone_portrait`, `iphone_landscape` |
| `iphone/edgeToEdge/portrait`, `landscape` | `iphone_edgetoedge_portrait`, `iphone_edgetoedge_landscape` |
| `ipad/standard/portrait`, `landscape` | `ipad_portrait`, `ipad_landscape` |
| `ipad/splitView/portrait` | Reuses `ipad_portrait`'s files (DS has its own, `ipad_portrait_splitview`) |
| `ipad/splitView/landscape` | `ipad_landscape_splitview` (orientation before `splitview`) |

**Files for each pose.** All PDFs, under `assets` → `resizable`:

| Pose | Background | Caps |
|---|---|---|
| Animated (caps cut out) | `<pose>_background.pdf` | `<pose>_<button>.pdf`, one per button |
| Static (no cap assets) | `<pose>.pdf` | None |

For example: `iphone_portrait_background.pdf`, `iphone_portrait_a.pdf`, `ipad_landscape_splitview_dpad.pdf`, and the static `iphone_landscape.pdf`.

**Buttons.** `<button>` is the item's input in snake_case: `a`, `b`, `c`, `x`, `y`, `z`, `l`, `r`, `start`, `select`, `menu`, and N64's `c_up`, `c_down`, `c_left` and `c_right` (from `cUp`, …). The one item whose inputs are up, down, left and right is `dpad`. Start and Select each have their own file (`iphone_portrait_start.pdf`, `iphone_portrait_select.pdf`).

**N64's analog stick** is a `thumbstick` item, not a cap, shared across poses by orientation: `thumbstick_portrait.pdf`, `thumbstick_landscape.pdf`.

**The DS Duo poses are the exception** (`iphone/inner`, `iphone/outer`, `iphone/splitView`). Each draws a single PNG under `large`: `duo_inner_portrait_background.png`, `duo_outer_landscape_background.png`, `duo_splitview_background.png`, and so on. Only inner portrait has its own caps (`duo_inner_portrait_a.png`, with one `duo_inner_portrait_start_select.png` for Start, Select and Menu). The others share caps by size: `iphone_small_*` for the outer poses, `iphone_large_*` for inner landscape and split view. DS's `iphone_edgetoedge_landscape.png` is also a single PNG under `large`.

**Shared caps** (Part 4) use device-neutral names instead: `dpad.pdf`, `<button>_portrait.pdf`, `<button>_landscape.pdf` (Genesis, November 2026).

**Leftovers.** Some Controller Skin folders still hold files from older naming schemes that info.json no longer references (GBA's `iphone_a.pdf`, `iPad_a.png`, `ipad_dpad.png`). Don't copy their names.

## Deliverables checklist

- [ ] If a PDF was cleaned in Step 0: zero gradient meshes left, and a Preview check at high zoom.
- [ ] Per pose: a cap-frame table (with the L/R bumper frames and screens), as `[x, y, w, h]` in pixels to 0.1 px, with the frame size and the source (vectors or pixels).
- [ ] If Part 2 ran: a background at exactly `mappingSize`, one asset per cap cut to its frame, and the composite check's worst pixel per cap.
- [ ] info.json delivered as a file, with a one-line summary of what changed.
- [ ] A short list of assumptions and judgment calls: L/R, screens, rounding, padding, background/art mismatches, duplicates, placeholders, `mappingSize` choice, asset/frame mismatches, and any cap drawing clipped from an asset.
- [ ] Whether the frames have been checked on device with Skin Debugging (Part 3).
- [ ] If padding changed: the user's choice, the per-item values, and a hit-area preview.
- [ ] If caps are shared: which file each representation uses, how the share was tested, and the coupling note (Part 4).
- [ ] Deliverables in one folder in the workspace (not only the scratchpad): info.json, PDFs, a NOTES.md, previews, rasterized and original full art. If installed: what changed in the core's working tree (Part 5).
- [ ] If published as a downloadable (Part 6): `name` and `identifier` match the catalog entry and aren't the bundled `.standard` identifier; Duo reps added if the shipping build still matches exactly; an upload folder with `info.json`, the `.deltaskin` and the background PDFs; a note that earlier downloaders must download again. If the skin is animated: a `preview` PNG for every rep (in the loose `info.json` only), the art check's numbers, and a contact sheet.

**Tooling notes.**
- Run PDF tools in a venv in the scratchpad (`pip install pymupdf pikepdf numpy pillow`), with `python -I`.
- Write scripts to files and keep the measurement spec (which blocks belong to which cap, per pose) in its own module, so the measure, build, verify and write steps share it.
- In zsh, `$list` doesn't word-split (`for f in $names` sees one long name) and a line starting with `==` fails, so loop over files in Python.

## Appendices

The appendices referred to above are in `references/`:

- Appendix A: Reference code — `references/appendix-a-reference-code.md`
- Appendix B: Worked example (Duo DS skin) — `references/appendix-b-duo-worked-example.md`
- Appendix C: PDF assets with an offset page box — `references/appendix-c-pdf-assets-offset-page-box.md`
- Appendix D: Gradient-mesh rasterizer (Step 0) — `references/appendix-d-gradient-mesh-rasterizer.md`
- Appendix E: Measuring and cutting from a PDF (Parts 1 and 2) — `references/appendix-e-measuring-and-cutting-from-pdf.md`
- Appendix F: CoreGraphics end-to-end compositor — `references/appendix-f-coregraphics-compositor.md`
- Appendix G: Worked example (Genesis 6-button, iPhone + iPad, November 2026) — `references/appendix-g-genesis-worked-example.md`
- Appendix H: Download Skins preview images (Part 6) — `references/appendix-h-download-skins-previews.md`
