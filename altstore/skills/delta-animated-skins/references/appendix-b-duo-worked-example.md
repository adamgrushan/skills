## Appendix B: Worked example (Duo DS skin, October 2026)

Use this as a regression check. The PNG frames below were measured with the earlier whole-pixel rule and match the info.json delivered then; the decimal pixel method should land within about 0.5 px of them. The PDF frames at the end are the decimal reference.

| Pose | Measured art | Background | mappingSize | Cap assets |
|---|---|---|---|---|
| outer portrait | `duo_outer_portrait.png` | `duo_outer_portrait_background.png` | 1398 × 2034 | `iphone_small_*` |
| outer landscape | `duo_outer_landscape.png` | `duo_outer_landscape_background.png` | 2034 × 1398 | `iphone_small_*` |
| inner portrait | `duo_inner_portrait.png` | `duo_inner_portrait_background.png` | 2007 × 2853 | `iphone_small_*` |
| inner landscape | `duo_inner_landscape.png` | `duo_inner_landscape_background.png` | 2853 × 2007 | `iphone_large_*` |
| splitView landscape | `duo_splitview_landscape.png` | `duo_splitview_background.png` | 2853 × 954 | `iphone_large_*` |

**Frames (Part 1)**, as `[x, y, w, h]` in pixels: cap frames for the buttons, and the bumper without its seam or outline for L and R. The touch screen equals its `outputFrame`.

```
outer portrait
  dpad: [75, 1587, 390, 390]   a: [1186, 1711, 142, 142]   b: [1054, 1843, 142, 142]   x: [1054, 1579, 142, 142]   y: [922, 1711, 142, 142]
  start: [616, 1756, 52, 52]   select: [616, 1867, 52, 52]   menu: [616, 1644, 52, 53]   l: [1, 744, 293, 106]   r: [1104, 744, 293, 106]
outer landscape
  dpad: [103, 935, 390, 391]   a: [1792, 1060, 142, 141]   b: [1660, 1192, 142, 141]   x: [1660, 928, 142, 141]   y: [1528, 1060, 142, 141]
  start: [919, 1104, 52, 52]   select: [919, 1215, 52, 53]   menu: [919, 993, 52, 52]   l: [1, 750, 293, 105]   r: [1740, 750, 293, 105]
inner portrait
  dpad: [61, 1803, 390, 390]   a: [1810, 1927, 142, 142]   b: [1678, 2059, 142, 142]   x: [1678, 1795, 142, 142]   y: [1546, 1927, 142, 142]
  start: [1556, 2352, 53, 53]   select: [1556, 2464, 53, 52]   menu: [398, 2463, 53, 53]   l: [0, 1433, 376, 135]   r: [1631, 1433, 376, 135]
inner landscape
  dpad: [239, 1201, 429, 430]   a: [2458, 1334, 156, 156]   b: [2313, 1479, 155, 156]   x: [2313, 1189, 155, 156]   y: [2168, 1334, 155, 156]
  start: [1993, 1693, 55, 55]   select: [1993, 1813, 55, 55]   menu: [805, 1813, 55, 55]   l: [0, 936, 376, 135]   r: [2477, 936, 376, 135]
splitView landscape
  dpad: [224, 304, 429, 429]   a: [2473, 441, 156, 155]   b: [2328, 586, 155, 156]   x: [2328, 296, 155, 155]   y: [2183, 441, 155, 155]
  start: [1986, 692, 55, 55]   select: [1986, 812, 55, 55]   menu: [812, 812, 55, 55]   l: [0, 0, 376, 134]   r: [2477, 0, 376, 134]
```

Findings from this example that the method should catch again:

- **splitView Start:** the background's well sits 6 px lower than in the full art, so its cap frame follows the background (y 692).
- **Inner portrait uses the small cap assets.** Its caps are 142 px, like the outer poses.
- **Cap assets are 0–2 px larger than the measured caps,** and several fit best about 1 px left of the frame. Delta scales each asset into its frame, so the worst case is about ⅓ pt.
- **L/R frames are the bumper alone,** without the seam or the 1 px outline. With the skin's existing `extendedEdges`, they registered taps fine on device.

**Duo inner portrait from `Duo - Open - Portrait.pdf` (decimal, October 2026).** The page is 669 × 951 pt, measured from the vector paths at 3× (Part 1). This art has a new, larger top screen; the rest of the layout matches the PNG above.

```
exact (pt × 3)
  dpad:  [60.921, 1803.1716, 389.658, 389.658]   a: [1810.62, 1927.62, 140.76, 140.76]   b: [1678.62, 2059.62, 140.76, 140.76]
  x:     [1678.62, 1795.62, 140.76, 140.76]       y: [1546.62, 1927.62, 140.76, 140.76]
  start: [1556.226, 2352.624, 52.083, 52.083]     select: [1556.226, 2463.894, 52.083, 52.083]   menu: [398.694, 2463.699, 52.080, 52.083]
  l:     [0, 1433.253, 376.5, 134.328]            r: [1630.5, 1433.253, 376.5, 134.328]
  top screen: [451.5, 306, 1104, 828]            bottom screen and touch item: [523.5, 1815, 960, 720]
written to info.json (edges rounded to 0.1)
  dpad:  [60.9, 1803.2, 389.7, 389.6]     a: [1810.6, 1927.6, 140.8, 140.8]   b: [1678.6, 2059.6, 140.8, 140.8]
  x:     [1678.6, 1795.6, 140.8, 140.8]   y: [1546.6, 1927.6, 140.8, 140.8]
  start: [1556.2, 2352.6, 52.1, 52.1]     select: [1556.2, 2463.9, 52.1, 52.1]   menu: [398.7, 2463.7, 52.1, 52.1]
  l:     [0, 1433.3, 376.5, 134.3]        r: [1630.5, 1433.3, 376.5, 134.3]
```

Findings from this file:

- **Where each edge comes from:** round caps, the face circle; D-pad, the pink cap base inside the dark cross; L/R, the bar's clip (y 477.751–522.527 pt) out from the seams at 125.5 and 543.5 pt; screens, the windows at (150.5, 102)–(518.5, 378) pt and (174.5, 605)–(494.5, 845) pt.
- **Cap blocks,** out of 161 top-level blocks: B 61–68, A 76–84, X 88–95, Y 99–105, D-pad 108–127 plus the pink base inside block 107, Start 131–134, Select 138–141, Menu 145–148.
- **The pixel method read 0.2–0.3 px outside these edges** on a 3× render of this PDF, and up to 0.45 px on the older PNG.
- **The whole-pixel frames above sit up to about 0.7 px off these edges,** and the shared 142 px `iphone_small_*` assets are 1.2 px wider than the 140.8 px caps.
- **Both screens are exactly 4:3;** the old frames were 959 px wide.
- **The file has 52 gradient meshes.** They didn't matter here, because everything was rendered to PNG with MuPDF.
- **Not yet checked on device** at the time of writing.
