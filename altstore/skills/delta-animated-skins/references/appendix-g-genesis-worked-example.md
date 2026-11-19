## Appendix G: Worked example — Genesis 6-button, iPhone + iPad (November 2026)

GPGXDeltaCore, seven Illustrator PDFs: four iPhone (portrait 320×250, e2e portrait 320×274, landscape 569×320,
e2e landscape 693×320) and three iPad (portrait 1024×429, split-view landscape 1366×429, landscape 1366×1024). Nine
caps per pose: D-pad, A, B, C, X, Y, Z, Start, Menu. No Mode button in the design, so no `mode` item. Delivered
`info.json` plus 26 PDFs; installed into the core with a rebuilt `Standard.deltaskin`.

**Step 0.**
- 30–32 type-7 meshes per file.
- The plain rasterizer left stair-steps on cap bevels: MuPDF draws a mesh's outer boundary without anti-aliasing.
  Supersampling 4× fixed it (Appendix D).
- Final match at 3×: iPhone 99.5–99.8%, iPad 99.91–99.96% of pixels within 2 levels.
- Under CoreGraphics the originals had seams across every cap; the cleaned files have none.

**Structure.**
- Poses of one orientation line up block for block. iPad portrait = iPhone portrait with buttons −15 blocks; iPad
  landscape = iPhone landscape with D-pad −10 and buttons −2; split-view landscape = iPad portrait with 10 blocks
  reordered.
- Per round button: well block (black disc + drop shadows), face, rim ring, shading, letter highlight.
- **Each letter lives in the next button's well block**, so those blocks are split by group.
- The D-pad is a **disc** (99 pt iPhone): the cross, dimple and diagonal arrows ride on it. The ring's white arrows and
  dots share a block with the cross shadow, also split by group.
- Landscape Menu/Start pills carry their text (it moves); portrait MENU/START labels and the iPad DELTA logo stay static.
- iPad portrait's round purple Menu: face, a blurred dark shading layer drawn between two faces, inner face,
  highlights. All of it belongs to the cap.

**Frames.** All 63 caps are concentric with their wells, with uniform well lines asserted per side (iPhone: D-pad
1.0 pt, A/B/C 0.62, X/Y/Z 0.98, pills 0.88 / 1.26; iPad exactly 1.8× those). For A/B/C the outline is the
**rim's** outer circle (38.6 pt), not the face (37.8 pt, offset 0.35 pt down). Edge rounding left Y at 28.9 × 29 and
landscape Menu/Start at 56.1 vs 56.2; both left as-is.

**Surprises.**
- **e2e landscape had a stray duplicate D-pad**, 1 pt left of the real one; kept in the background and flagged.
- **iPad split-view portrait had SNES's layout** (`select`, X/Y diamond); made it mirror standard portrait (1024×429).
- **Old padding was stale:** A/X, B/Y, C/Z and X/Y/Z overlapped, and Menu's `right: 30` reached Start. The user
  chose "fit to new layout" (`solve_padding`).
- **Dropped spill:** the D-pad cross shadow ran ~1 pt past the well onto the recess, at most 14 levels; reported.

**Checks.**
- Holes and pressed wells: 0–9 levels.
- MuPDF rest scene: 99.5–99.9% of pixels within 2 levels.
- CoreGraphics end to end: every pixel more than 16 levels off sits on an art edge; off-edge max 10–12.
- A first pressed-ring metric used rectangles and read 170+ levels by catching the pressed cap's rim. With true
  outlines and a 0.3 pt margin it read 54–75 on iPad's light X/Y caps (edge bleed at 2×). With 0.6 pt: 0–3.

**Sharing (Part 4).**
- Edge-to-edge reuses standard; split-view landscape reuses iPad portrait.
- The iPad art is exactly 1.8× the iPhone art (effects included), so the iPhone uses the iPad caps too: one
  `dpad.pdf`, `<button>_portrait/landscape.pdf`, and pose-named Start/Menu where the shapes differ.
- Test: iPad caps composited into the iPhone scenes matched the iPhone art as well as the iPhone's own caps did
  (p99 1–5 off-edge).
- The first attempt compared the other way, iPhone caps scaled *up*, which made the difference look like separately
  tuned effects. Always cut from the larger art and test in the target scene.
- Worst aspect mismatch: 0.25%.

**Install (Part 5).** The core bundles only `Standard.deltaskin`, which was deleted in the working tree. Rebuilt it
flat and deflated from the loose files (27 entries, byte-identical). The designer's seven original PDFs were
uncommitted, so they were moved to `full-art-original/` rather than deleted.

**Downloadable (Part 6).**
- The package was published to `remote-skins.json` as `com.delta.genesis.6.button`, but its `info.json` still said
  `Standard Genesis` / `com.delta.genesis.standard`. Renamed to match the catalog entry.
- On an iPhone Duo the skin didn't appear in Download Skins, while it did on an iPhone 15. The shipping build's screen
  matched representations exactly, and the skin had no `inner`/`outer` reps.
- The shipping build didn't have the code fix, so Duo reps were added as copies: `iphone.inner` = `ipad.standard`,
  `iphone.outer` = `iphone.standard`, `iphone.splitView` = `ipad.splitView`. That's 1,113 added lines and no new assets.
- The rebuilt `.deltaskin` kept byte-identical PDFs. On the Duo simulator it imported as its own skin, and Inside ›
  Portrait drew the iPad art with all its caps.

**Not yet confirmed on device** (as of November 12, 2026).
