## Appendix D: Gradient-mesh rasterizer (Step 0)

**Tested on:**
- **Duo inner portrait:** the file approved in Preview was made before the fix below. With the fix, its output moves
  closer to the original only where the old version was 1 unit off (see below).
- **DS iPad poses (October 2026):** 99.5–99.998% of pixels within 2 levels at 3 px/pt.

```bash
pip install pymupdf pikepdf
python rasterize_meshes.py "Duo - Open - Portrait 1.pdf" duo_inner_portrait.pdf
# replaced 52 mesh draws (52 distinct meshes) at 6 px/pt; 0 meshes left
```

**Place each image from the pixmap's real origin (fixed October 2026).** Each mesh is rendered on a temporary page that
is exactly its `/Decode` range, clipped to its coverage plus a 1-unit margin.

- **What goes wrong:** MuPDF trims the clip to the page. When a mesh comes within 1 unit of the left or top of its
  Decode range, the margin is trimmed and the pixmap starts later than the requested clip.
- **The old code** placed the image from the requested clip. It shifted the whole image by up to 1 unit (1 pt under
  a unit `cm`) toward that edge.
- **Symptom:** on the DS iPad rim meshes, the shading moved 1 pt and lost its inner edge, which showed as a hard step.
  Only about 99% of pixels came within 2 levels, and a higher `--scale` didn't help.
- **The fix:** `render_shading` now also returns `(pix.x, pix.y)`, and `mesh_image_form` places the image from that.
  When nothing is trimmed this equals the old value, so output for meshes that never touched their Decode edge is
  unchanged.
- **Results:**
  - **DS iPad:** at 3 px/pt, Portrait went from 98.9% to 99.5% of pixels within 2 levels, and Portrait Keyboard from
    98.6% to 99.9%.
  - **Duo inner portrait:** it had 8 such mesh draws. At 3 px/pt the fix changes about 4,000 pixels by up to 35
    levels (the hinge-bar ends and the Menu/Select wells; A/B/X/Y by at most 11). Within those pixels the mean error
    against the original drops from 5.2 to 1.3 levels.
- **Check for it:** if Step 0's 3× comparison comes in well under 99.9% and a higher `--scale` doesn't help, look for
  a placement error.

**Supersample each mesh (added November 2026, Genesis).** MuPDF draws a mesh's *outer boundary* without
anti-aliasing. Where a clip hides that boundary it doesn't matter, but on Genesis's cap bevels it was the visible edge
of a highlight. Rendered at 6 px/pt and drawn larger, it showed as a stair-step that the original didn't have: Apple
draws the vector mesh at output resolution, where the hard edge is sub-pixel.
- **Symptom:** stairs along a bevel at 12–24× zoom; the steps get finer as `--scale` goes up (6 → 12) but don't go away.
- **The fix:** `mesh_image_form` renders at `SS × K` px/pt (SS = 4) and area-averages the premultiplied samples down to
  K. It first pads so the SS×SS cells line up with the K grid, and keeps the pixmap's real origin (the fix above).
  Memory stays small: the sums are taken in uint16/uint32.
- **Results:** Genesis iPhone portrait went from 99.51% to 99.62% of pixels within 2 levels at 3×, with the stairs
  gone; the Genesis iPads reached 99.91–99.96%. What's left are 1 px lines along mesh boundaries (anti-aliased now,
  hard in MuPDF's render of the original). Those are expected; judge them by eye at 24×.

`rasterize_meshes.py`:

```python
"""Remove gridlines from an Illustrator PDF by rasterizing only its gradient meshes.

Usage:
  python rasterize_meshes.py IN.pdf OUT.pdf [--scale 6]

Each mesh is rendered at 4x and area-averaged down (MuPDF doesn't anti-alias a mesh's outer boundary).
Every gradient mesh (PDF shading types 4-7) drawn anywhere on page 1 -- in the page itself, inside
forms, or inside soft-mask groups -- is replaced, in place, by an image of just that mesh. Clips,
outlines, opacity masks and every other object stay vector, so edges stay crisp at any zoom.
Requires PyMuPDF and pikepdf (pip install pymupdf pikepdf).
"""
import io, sys, zlib, warnings
import numpy as np, pikepdf, pymupdf as fitz
from pikepdf import Operator as Op, ContentStreamInstruction as CSI, Name
warnings.filterwarnings('ignore')
SS = 4

def all_streams(pdf):
    """(label, stream, resources) for the page and every form / soft-mask group reachable from it."""
    page = pdf.pages[0]; out = [('page', page.obj, page.Resources)]; seen = set()
    def walk(res, tag):
        if res is None: return
        for n, x in res.get('/XObject', {}).items():
            if x.get('/Subtype') == '/Form' and x.objgen not in seen:
                seen.add(x.objgen); out.append((f'{tag}>{n}', x, x.get('/Resources'))); walk(x.get('/Resources'), f'{tag}>{n}')
        for n, g in res.get('/ExtGState', {}).items():
            sm = g.get('/SMask')
            if isinstance(sm, pikepdf.Dictionary) and '/G' in sm and sm.G.objgen not in seen:
                seen.add(sm.G.objgen); out.append((f'{tag}>{n}.SMask', sm.G, sm.G.get('/Resources'))); walk(sm.G.get('/Resources'), f'{tag}>{n}.SMask')
    walk(page.Resources, 'page')
    return out

def ops_of(pdf, obj):
    page = pdf.pages[0]
    return list(pikepdf.parse_content_stream(page if obj.objgen == page.obj.objgen else obj))

def mesh_draws(pdf):
    """Every 'sh' that paints a mesh shading: (label, stream, op index, shading)."""
    out = []
    for tag, obj, res in all_streams(pdf):
        if res is None: continue
        for i, o in enumerate(ops_of(pdf, obj)):
            if str(o.operator) == 'sh':
                s = res.Shading[str(o.operands[0])]
                if int(s.ShadingType) >= 4: out.append((tag, obj, i, s))
    return out

def render_shading(s, scale, clip=None):
    """Render one shading alone, in its own coordinate space.
    Returns premultiplied RGBA, the Decode box, and the pixmap's origin in pixels."""
    x0, x1, y0, y1 = [float(s.Decode[k]) for k in range(4)]
    t = pikepdf.new(); pg = t.add_blank_page(page_size=(x1 - x0, y1 - y0))
    pg.Resources = pikepdf.Dictionary(Shading=pikepdf.Dictionary(Sh=t.copy_foreign(s)))
    pg.Contents = t.make_stream(pikepdf.unparse_content_stream(
        [CSI([], Op('q')), CSI([1, 0, 0, 1, -x0, -y0], Op('cm')), CSI([Name('/Sh')], Op('sh')), CSI([], Op('Q'))]))
    buf = io.BytesIO(); t.save(buf)
    pix = fitz.open(stream=buf.getvalue(), filetype='pdf')[0].get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=True, clip=clip)
    # MuPDF trims the clip to the page (= the Decode range), so the pixmap can start later than the clip asked for
    return np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 4).copy(), (x0, x1, y0, y1), (pix.x, pix.y)

def coverage_box(s):
    for sc in (1.0, 8.0):                       # some meshes are slivers; look again at 8x
        a, (x0, x1, y0, y1), _ = render_shading(s, sc); ys, xs = np.nonzero(a[..., 3] > 0)
        if len(xs): return x0 + xs.min() / sc, y1 - (ys.max() + 1) / sc, x0 + (xs.max() + 1) / sc, y1 - ys.min() / sc
    return None

def mesh_image_form(pdf, s, K):
    """A small form holding an image of mesh s, plus the cm that places it in the mesh's own coordinates."""
    box = coverage_box(s)
    if box is None: return None
    bx0, by0, bx1, by1 = box; x0, x1, y0, y1 = [float(s.Decode[k]) for k in range(4)]
    clip = fitz.Rect(bx0 - x0 - 1, y1 - by1 - 1, bx1 - x0 + 1, y1 - by0 + 1)
    a, _, (px0, py0) = render_shading(s, K * SS, clip=clip)   # where the pixmap really starts, not floor(clip * K)
    # Supersample: MuPDF draws a mesh's outer boundary without anti-aliasing, so render at SS x and
    # area-average the premultiplied samples down to K px/pt. Pad so the SS x SS cells line up with
    # the K px/pt grid (px0, py0 multiples of SS).
    ox, oy = px0 % SS, py0 % SS
    h0, w0 = a.shape[:2]
    H, W = -(-(h0 + oy) // SS) * SS, -(-(w0 + ox) // SS) * SS
    big = np.zeros((H, W, 4), np.uint8); big[oy:oy + h0, ox:ox + w0] = a
    t = big.reshape(H // SS, SS, W, 4).sum(1, dtype=np.uint16)
    t = t.reshape(H // SS, W // SS, SS, 4).sum(2, dtype=np.uint32)
    a = ((t + SS * SS // 2) // (SS * SS)).astype(np.uint8)
    px0, py0 = (px0 - ox) // SS, (py0 - oy) // SS
    X0 = x0 + px0 / K; Ytop = y1 - py0 / K; w, h = a.shape[1], a.shape[0]
    A = a[..., 3:4].astype(float)
    rgb = np.where(A > 0, np.clip(a[..., :3] * 255.0 / np.maximum(A, 1), 0, 255), 0).astype(np.uint8)  # un-premultiply
    cs = s.ColorSpace
    n = int(cs[1].N) if isinstance(cs, pikepdf.Array) and str(cs[0]) == '/ICCBased' else (1 if str(cs) == '/DeviceGray' else 3)
    if n == 1:   # grey meshes (usually inside soft masks)
        data, space = (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2] + 0.5).astype(np.uint8), Name.DeviceGray
    else:        # keep the mesh's own (sRGB) ICC profile
        data, space = rgb, (cs if n == 3 else Name.DeviceRGB)
    alpha = pikepdf.Stream(pdf, zlib.compress(a[..., 3].tobytes(), 9), Type=Name.XObject, Subtype=Name.Image, Width=w, Height=h,
                           ColorSpace=Name.DeviceGray, BitsPerComponent=8, Filter=Name.FlateDecode, Interpolate=True)
    img = pikepdf.Stream(pdf, zlib.compress(np.ascontiguousarray(data).tobytes(), 9), Type=Name.XObject, Subtype=Name.Image,
                         Width=w, Height=h, ColorSpace=space, BitsPerComponent=8, Filter=Name.FlateDecode, Interpolate=True, SMask=alpha)
    # Wrap in a form: an image's own SMask would REPLACE any soft mask in effect (e.g. a highlight's opacity fade).
    form = pikepdf.Stream(pdf, pikepdf.unparse_content_stream([CSI([], Op('q')), CSI([Name('/Im')], Op('Do')), CSI([], Op('Q'))]),
                          Type=Name.XObject, Subtype=Name.Form, BBox=[0, 0, 1, 1], Resources=pikepdf.Dictionary(XObject=pikepdf.Dictionary(Im=img)),
                          Group=pikepdf.Dictionary(Type=Name.Group, S=Name.Transparency, I=False, K=False))
    return pdf.make_indirect(form), (w / K, 0, 0, h / K, X0, Ytop - h / K)

def rasterize_meshes(src, dst, K=6.0):
    pdf = pikepdf.open(src); draws = mesh_draws(pdf)
    forms = {}
    for _, _, _, s in draws:
        if s.objgen not in forms: forms[s.objgen] = mesh_image_form(pdf, s, K)
    by_stream = {}
    for _, obj, i, s in draws: by_stream.setdefault(obj.objgen, (obj, []))[1].append((i, s))
    page = pdf.pages[0]
    for og, (obj, items) in by_stream.items():
        is_page = og == page.obj.objgen
        ops = ops_of(pdf, obj); res = page.Resources if is_page else obj.Resources
        if '/XObject' not in res: res.XObject = pikepdf.Dictionary()
        rep = {}
        for i, s in items:
            if forms[s.objgen] is None: rep[i] = []; continue
            form, M = forms[s.objgen]; nm = Name(f'/MeshImg{s.objgen[0]}'); res.XObject[nm] = form
            rep[i] = [CSI([], Op('q')), CSI([round(v, 6) for v in M], Op('cm')), CSI([nm], Op('Do')), CSI([], Op('Q'))]
        new = []
        for j, o in enumerate(ops): new += rep.get(j, [o])
        data = pikepdf.unparse_content_stream(new)
        if is_page: page.Contents = pdf.make_stream(data)
        else: obj.write(data)
    for _, obj, res in all_streams(pdf):          # drop mesh resources nothing draws any more
        sd = res.get('/Shading') if res is not None else None
        if sd is None: continue
        used = {str(o.operands[0]) for o in ops_of(pdf, obj) if str(o.operator) == 'sh'}
        for nm in [str(k) for k in sd.keys()]:
            if int(sd[nm].ShadingType) >= 4 and nm not in used: del sd[nm]
    pdf.save(dst, compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)
    left = len(mesh_draws(pikepdf.open(dst)))
    assert left == 0, f'{left} mesh draws remain'
    return len(draws), len(forms)

if __name__ == '__main__':
    args = sys.argv[1:]; K = 6.0
    if '--scale' in args:
        k = args.index('--scale'); K = float(args[k + 1]); del args[k:k + 2]
    n, m = rasterize_meshes(args[0], args[1], K)
    print(f'replaced {n} mesh draws ({m} distinct meshes) at {K:g} px/pt; 0 meshes left')
```
