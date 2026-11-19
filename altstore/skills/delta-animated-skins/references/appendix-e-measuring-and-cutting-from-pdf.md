## Appendix E: Measuring and cutting from a PDF (Parts 1 and 2)

The functions are the ones used on the Duo inner portrait (October 2026); the usage lines at the end are a sketch of how they fit together. Requires pikepdf and PyMuPDF.

```python
"""Cap frames, a caps-removed background and cap assets from a single-page PDF.
Assumes the page box starts at (0, 0) (Appendix C) and the page isn't rotated."""
import io
import numpy as np, pikepdf, fitz

def top_level_blocks(src):
    """The open PDF, its page's content ops, and (start, end) for each top-level q ... Q block."""
    pdf = pikepdf.open(src)
    ops = list(pikepdf.parse_content_stream(pdf.pages[0]))
    blocks, depth, start = [], 0, None
    for i, o in enumerate(ops):
        op = str(o.operator)
        if op == 'q':
            if depth == 0:
                start = i
            depth += 1
        elif op == 'Q':
            depth -= 1
            if depth == 0:
                blocks.append((start, i + 1))
        else:
            assert depth > 0, 'op %d draws outside any q ... Q block' % i
    return pdf, ops, blocks

def pdf_from_ops(src, sel):
    """Bytes of a copy of src whose page draws only the ops in sel."""
    out = pikepdf.open(src)
    out.pages[0].Contents = out.make_stream(pikepdf.unparse_content_stream(sel))
    buf = io.BytesIO(); out.save(buf)
    return buf.getvalue()

def render(data, scale):
    """RGBA render of PDF bytes at scale px per pt (3 for iPhone art, which gives exactly mappingSize)."""
    pix = fitz.open(stream=data, filetype='pdf')[0].get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=True)
    return np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 4).copy()

def cut_cap(data, frame, s=3.0):
    """Render PDF bytes so that frame ([x, y, w, h] in px at scale s, top-down) fills exactly round(w) x round(h) px."""
    x, y, w, h = [v / s for v in frame]
    N, M = int(round(frame[2])), int(round(frame[3]))
    sx, sy = N / w, M / h
    pix = fitz.open(stream=data, filetype='pdf')[0].get_pixmap(
        matrix=fitz.Matrix(sx, 0, 0, sy, -x*sx, -y*sy), alpha=True, clip=fitz.Rect(x, y, x + w, y + h))
    assert (pix.x, pix.y, pix.width, pix.height) == (0, 0, N, M), (pix.irect, N, M)
    return np.frombuffer(pix.samples, np.uint8).reshape(M, N, 4).copy()

def bez_extrema(p0, p1, p2, p3):
    """The end points of a cubic Bézier plus the points where it turns in x or y."""
    ts = [0.0, 1.0]
    for i in range(2):
        a = -p0[i] + 3*p1[i] - 3*p2[i] + p3[i]; b = 2*(p0[i] - 2*p1[i] + p2[i]); c = p1[i] - p0[i]
        if abs(a) < 1e-12:
            if abs(b) > 1e-12:
                ts.append(-c/b)
        else:
            disc = b*b - 4*a*c
            if disc >= 0:
                r = np.sqrt(disc); ts += [(-b + r)/(2*a), (-b - r)/(2*a)]
    pts = []
    for t in ts:
        if 0 <= t <= 1:
            mt = 1 - t
            pts.append(tuple(mt**3*p0[i] + 3*mt*mt*t*p1[i] + 3*mt*t*t*p2[i] + t**3*p3[i] for i in range(2)))
    return pts

def path_boxes(ops):
    """(kind, (x0, y0, x1, y1), op index) for every path in ops, in page space (y up), through the cm stack.
    kind is the painting operator ('f', 'S', ...), 'clip' for a clip, or 'clip+f' for both."""
    ctm, pts, cur, clip, out = [np.eye(3)], [], None, False, []
    def T(x, y):
        v = np.array([x, y, 1.0]) @ ctm[-1]
        return v[0], v[1]
    for i, o in enumerate(ops):
        op = str(o.operator)
        a = [float(v) for v in o.operands] if op in ('m', 'l', 'c', 'v', 'y', 're', 'cm') else None
        if op == 'q':
            ctm.append(ctm[-1].copy())
        elif op == 'Q':
            ctm.pop()
        elif op == 'cm':
            ctm[-1] = np.array([[a[0], a[1], 0], [a[2], a[3], 0], [a[4], a[5], 1]]) @ ctm[-1]
        elif op in ('m', 'l'):
            cur = T(a[0], a[1]); pts.append(cur)
        elif op in ('c', 'v', 'y'):
            if op == 'c':
                p1, p2, p3 = T(a[0], a[1]), T(a[2], a[3]), T(a[4], a[5])
            elif op == 'v':
                p1, p2, p3 = cur, T(a[0], a[1]), T(a[2], a[3])
            else:
                p1, p2, p3 = T(a[0], a[1]), T(a[2], a[3]), T(a[2], a[3])
            pts += bez_extrema(cur, p1, p2, p3); cur = p3
        elif op == 're':
            for x, y in ((a[0], a[1]), (a[0] + a[2], a[1]), (a[0], a[1] + a[3]), (a[0] + a[2], a[1] + a[3])):
                pts.append(T(x, y))
        elif op in ('W', 'W*'):
            clip = True
        elif op in ('n', 'f', 'F', 'f*', 'S', 's', 'B', 'B*', 'b', 'b*'):
            if pts:
                xs, ys = [p[0] for p in pts], [p[1] for p in pts]
                kind = ('clip' if clip else '') + ('' if op == 'n' else ('+' if clip else '') + op)
                out.append((kind, (min(xs), min(ys), max(xs), max(ys)), i))
            pts, clip = [], False
    return out

def to_px(bb, page_h, s=3.0):
    """Page-space (y up) box -> top-down [x, y, w, h] in px at scale s."""
    x0, y0, x1, y1 = bb
    return [x0*s, (page_h - y1)*s, (x1 - x0)*s, (y1 - y0)*s]

# ---------- usage sketch (Duo inner portrait) ----------
# from PIL import Image
# SRC = 'Duo - Open - Portrait.pdf'                         # 669 x 951 pt
# pdf, ops, blocks = top_level_blocks(SRC)
# for k, (a, b) in enumerate(blocks):                       # see what each block draws
#     Image.fromarray(render(pdf_from_ops(SRC, ops[a:b]), 1)).save('block_%03d.png' % k)
# CAPS = {'a': range(76, 85), 'b': range(61, 69)}           # ...every cap's blocks, read off those renders
# for k in CAPS['a']:                                       # the face circle's box is A's frame
#     for kind, bb, i in path_boxes(ops[blocks[k][0]:blocks[k][1]]):
#         print(k, i, kind, [round(v, 3) for v in to_px(bb, 951)])
# caps = {k for r in CAPS.values() for k in r}
# art = render(open(SRC, 'rb').read(), 3)
# bg = render(pdf_from_ops(SRC, [o for k, (a, b) in enumerate(blocks) if k not in caps for o in ops[a:b]]), 3)
# cap_a = cut_cap(pdf_from_ops(SRC, [o for k in CAPS['a'] for o in ops[blocks[k][0]:blocks[k][1]]]), [1810.6, 1927.6, 140.8, 140.8])
```

### Splitting shared blocks and cutting vector cap PDFs (Genesis, November 2026)

Used on all seven Genesis poses. `split_block` handles blocks that draw one cap's art plus other things: a letter
drawn with the next button's well, or the D-pad cross shadow sharing a block with the ring's static arrows.
`cut_cap_pdf` writes a SNES-style vector cap: page box = the rounded frame, rebased to (0, 0) by rewriting
coordinates (Appendix C's `Rebaser`), never by a wrapper `cm`. Both run on the mesh-cleaned PDF.

```python
import io, numpy as np, pikepdf, fitz
from decimal import Decimal
import rebase_pdf_origin as rb          # Appendix C

def groups(ops, a, b):
    """[(start, end)] of the depth-1 q ... Q groups of top-level block (a, b)."""
    out, d, st = [], 0, None
    for i in range(a, b):
        op = str(ops[i].operator)
        if op == 'q':
            d += 1
            if d == 2: st = i
        elif op == 'Q':
            if d == 2: out.append((st, i + 1))
            d -= 1
    return out

def inside(pt, f, round_cap):
    """Is point pt (pt units, top-down) inside the cap outline of frame f? Circle test for round caps --
    a bounding-box test would claim the D-pad ring's dots, which sit inside the disc's box."""
    x, y, w, h = f
    if round_cap:
        return ((pt[0] - (x + w / 2)) / (w / 2)) ** 2 + ((pt[1] - (y + h / 2)) / (h / 2)) ** 2 <= 1
    return x <= pt[0] <= x + w and y <= pt[1] <= y + h

def split_block(src, ops, a, b, f, round_cap):
    """(cap op indices, background op indices, report) for block (a, b), split against ONE cap (the one the block is
    listed under -- the next button's well is centred on the next button, so never test against all caps).
    Both halves keep the block's ungrouped ops (q, clip, colour/gs state, Q); each depth-1 group goes to the cap if
    its rendered centre lies inside the cap outline. A group that renders nothing follows the group before it."""
    gs = groups(ops, a, b)
    ing = {i: g for g in gs for i in range(*g)}
    shared = [i for i in range(a, b) if i not in ing]
    cap_groups, rep, prev = set(), [], False
    for g in gs:
        img = render(pdf_from_ops(src, [ops[i] for i in sorted(shared + list(range(*g)))]), 4)
        ys, xs = np.nonzero(img[..., 3] > 4)
        if len(xs):
            c = ((xs.min() + xs.max() + 1) / 8, (ys.min() + ys.max() + 1) / 8)
            prev = inside(c, f, round_cap)
            rep.append('%d-%d %s (%.1f, %.1f)' % (g[0], g[1], 'cap' if prev else 'bg', *c))
        else:
            rep.append('%d-%d %s (renders nothing)' % (g[0], g[1], 'cap' if prev else 'bg'))
        if prev:
            cap_groups.add(g)
    cap = sorted(shared + [i for g in cap_groups for i in range(*g)])
    bg = sorted(shared + [i for g in gs if g not in cap_groups for i in range(*g)])
    return cap, bg, rep                          # print rep and read it

def save_pdf(src, sel_ops, dst, box=None):
    """A copy of src drawing only sel_ops, lean: Illustrator page extras and unused resources removed.
    box = (x0, y0, x1, y1) in page space (y up) becomes the only page box."""
    pdf = pikepdf.open(io.BytesIO(pdf_from_ops(src, sel_ops)))
    page = pdf.pages[0]
    for k in ('/ArtBox', '/BleedBox', '/CropBox', '/TrimBox', '/PieceInfo', '/LastModified'):
        if k in page.obj: del page.obj[k]
    if box is not None:
        page.obj.MediaBox = pikepdf.Array([Decimal(repr(round(v, 4))) for v in box])
    if '/Metadata' in pdf.Root: del pdf.Root['/Metadata']
    page.remove_unreferenced_resources()
    pdf.save(dst, compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)

def cut_cap_pdf(src, sel_ops, frame, page_h, dst, tmp):
    """Vector cap PDF whose page is exactly `frame` ([x, y, w, h] in pt, top-down, already rounded to 0.1)."""
    x, y, w, h = frame
    save_pdf(src, sel_ops, tmp, (x, page_h - (y + h), x + w, page_h - y))
    doc = fitz.open(tmp)
    _, (x0, y0, x1, y1) = rb.page_box(doc)
    r = rb.Rebaser(doc, x0, y0)
    res = r.resources(doc[0].xref, None)
    for cx in doc[0].get_contents():
        doc.update_stream(cx, r.rewrite(doc.xref_stream(cx), res))
    doc.xref_set_key(doc[0].xref, 'MediaBox', '[0 0 %s %s]' % (rb.fmt(x1 - x0), rb.fmt(y1 - y0)))
    doc.save(dst, garbage=3, deflate=True)

# background = every op no cap took, plus the background half of each split block, at the full page box:
# save_pdf(src, [ops[i] for i in bg_indices], '<pose>_background.pdf')
```

**Per-pose spec.** Keep the block assignment in a module that every step imports, e.g. per cap:
`dict(frame=[62, 63], well=61, blocks=[62, 63, 64, 65, 66], split=[66])`.
- `frame`: the blocks whose first non-page path boxes union to the outline (face + rim).
- `well`: the block whose *largest* path is the well.
- `blocks`: every block that belongs to the cap.
- `split`: the blocks shared with the background.

Poses of one design usually differ by a constant block offset, so write the spec as a function of that offset.
