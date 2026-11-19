## Appendix A: Reference code (Python, numpy + Pillow; tested against the Duo files)

`dpad_box`, `rounded` and `composite_check` are condensed from the October 2026 decimal scripts and haven't been re-run in exactly this form.

```python
import numpy as np
from PIL import Image

def load(path):
    return np.asarray(Image.open(path).convert('RGBA')).astype(float)

def luma(a):
    return 0.299*a[..., 0] + 0.587*a[..., 1] + 0.114*a[..., 2]

def ray(Y, x, y, dx, dy, maxlen):
    v = []
    while 0 <= x < Y.shape[1] and 0 <= y < Y.shape[0] and len(v) < maxlen:
        v.append(Y[y, x]); x += dx; y += dy
    return np.array(v)

def find_well(v):
    """Index of the darkest pixel of the first strong dip (the well line), or None."""
    for i in range(3, len(v) - 2):
        ref = v[max(0, i-6):i].max()
        if v[i] <= v[i-1] and v[i] <= v[i+1] and ref - v[i] > 45 and v[i] < 0.7*ref:
            j = i
            while j + 1 < len(v) and v[j+1] <= v[j]:
                j += 1
            return j
    return None

# ---------- Part 1: cap frames (inside the well) ----------
def cap_ray(Y, x, y, dx, dy, maxlen):
    """Returns (k, cov): k = steps from the center to the first line pixel,
    cov = how much of that pixel the well line covers."""
    v = ray(Y, x, y, dx, dy, maxlen)
    j = find_well(v)
    if j is None:
        return None
    line = v[j]                                            # darkest pixel = line color
    for k in range(max(2, j-2), j+1):
        c = v[k-1] + np.clip(v[k-1] - v[k-2], -15, 5)      # bevel-aware cap color
        cov = (c - v[k]) / (c - line) if c > line else 1.0
        if cov > 0.08:
            return k, min(cov, 1.0)
    return None

def cap_box(Y, xc, yc, radius, span=2):
    """Round caps, fractional edges. Call twice: the second time centered on the first result."""
    cx, cy = int(xc), int(yc); ml = int(radius*1.25) + 6
    sides = {'L': [], 'R': [], 'T': [], 'B': []}
    for o in range(-span, span+1):
        for s, (x, y, dx, dy) in {'L': (cx, cy+o, -1, 0), 'R': (cx, cy+o, 1, 0),
                                  'T': (cx+o, cy, 0, -1), 'B': (cx+o, cy, 0, 1)}.items():
            r = cap_ray(Y, x, y, dx, dy, ml)
            if r is None:
                continue
            k, cov = r
            sides[s].append({'L': x-k+cov, 'R': x+k+1-cov, 'T': y-k+cov, 'B': y+k+1-cov}[s])   # keep the fraction
    L, T, R, B = (float(np.median(sides[s])) for s in 'LTRB')
    return L, T, R - L, B - T

def dip_inner_edge(v, line=25.0):
    """Straight edges (D-pad caps): inner edge of the dark line in sample coordinates."""
    j = find_well(v)
    if j is None:
        return None
    a = j
    while a - 1 >= 0 and v[a-1] <= v[j] + 2:                       # step over a flat core
        a -= 1
    while a - 1 >= 0 and v[a-1] - v[a] > max(4, 0.15*(v[a-1] - v[j])):
        a -= 1
    b = j
    while b + 1 < len(v) and v[b+1] <= v[j] + 2:
        b += 1
    while b + 1 < len(v) and v[b+1] - v[b] > max(4, 0.15*(v[b+1] - v[j])):
        b += 1
    ia, ib = max(a-1, 0), min(b+1, len(v)-1)
    idx = np.arange(a, b+1)
    base = v[ia] + (v[ib] - v[ia]) * (idx - ia) / max(ib - ia, 1)
    d = np.clip((base - v[a:b+1]) / (base - line), 0, 1)
    w = d.sum()
    if w <= 0:
        return None
    return (idx*d).sum()/w + 0.5 - w/2

def dpad_box(Y, x0, y0, x1, y1):
    """D-pad, fractional edges. (x0, y0, x1, y1) is a rough outer box. Scans the rows (or columns) within
    ±11% of the width around the center, starting 7% inside each edge and moving outward."""
    W = x1 - x0; cx = (x0 + x1) / 2; cy = (y0 + y1) / 2; n = int(0.2*W)
    rows = range(int(cy - 0.11*W), int(cy + 0.11*W) + 1)
    cols = range(int(cx - 0.11*W), int(cx + 0.11*W) + 1)
    out = {}
    for s in 'LRTB':
        vals = []
        for r in (rows if s in 'LR' else cols):
            if s == 'L':
                st = int(x0 + 0.07*W); t = dip_inner_edge(Y[r, st::-1][:n]); e = None if t is None else st + 1 - t
            elif s == 'R':
                st = int(x1 - 0.07*W); t = dip_inner_edge(Y[r, st:][:n]); e = None if t is None else st + t
            elif s == 'T':
                st = int(y0 + 0.07*W); t = dip_inner_edge(Y[st::-1, r][:n]); e = None if t is None else st + 1 - t
            else:
                st = int(y1 - 0.07*W); t = dip_inner_edge(Y[st:, r][:n]); e = None if t is None else st + t
            if e is not None:
                vals.append(e)
        assert vals, 'no reading on side ' + s   # happened on the bottom arm of the Duo PDF render
        out[s] = float(np.median(vals))
    return out['L'], out['T'], out['R'] - out['L'], out['B'] - out['T']

# ---------- rounding for info.json ----------
def tidy(v, places=1):
    """Round to places; whole numbers come back as int (1815, not 1815.0)."""
    v = round(v, places)
    return int(v) if v == int(v) else v

def rounded(f, places=1):
    """[x, y, w, h] with the edges rounded, then w and h taken from the rounded edges,
    so every edge is within half a step of the measurement."""
    x0, y0 = round(f[0], places), round(f[1], places)
    x1, y1 = round(f[0] + f[2], places), round(f[1] + f[3], places)
    return [tidy(x0, places), tidy(y0, places), tidy(x1 - x0, places), tidy(y1 - y0, places)]

# ---------- verification ----------
def asset_fit(bg, art, asset, x0, y0, r=5):
    """Composite a cap asset over the background near (x0, y0); returns (error, x, y)
    for the placement that best reproduces the full art."""
    al = asset[..., 3:4] / 255; h, w = asset.shape[:2]
    best = None
    for dy in range(-r, r+1):
        for dx in range(-r, r+1):
            x, y = x0 + dx, y0 + dy
            comp = asset[..., :3]*al + bg[y:y+h, x:x+w, :3]*(1 - al)
            e = np.abs(comp - art[y:y+h, x:x+w, :3]).mean()
            if best is None or e < best[0]:
                best = (e, x, y)
    return best

def area_weights(edges, lo, n, k):
    """W[i, s]: share of device pixel lo+i covered by source cell s, which spans edges[s]..edges[s+1] in mapping px."""
    d0 = (lo + np.arange(n))[:, None] / k
    return np.clip(np.minimum(d0 + 1/k, edges[None, 1:]) - np.maximum(d0, edges[None, :-1]), 0, None) * k

def to_device(img, xe, ye, box, k):
    """Area-average a premultiplied image, whose pixel edges are xe and ye in mapping px, onto the device pixels in box."""
    X0, Y0, X1, Y1 = box
    t = np.tensordot(area_weights(ye, Y0, Y1 - Y0, k), img, axes=(1, 0))
    return np.tensordot(t, area_weights(xe, X0, X1 - X0, k), axes=(1, 1)).transpose(0, 2, 1)

def composite_check(art, bg, asset, frame, k, pad=6):
    """Delta at phone resolution. The background and the cap asset (stretched into its decimal frame) are each
    resampled to the device's pixels and composited, then compared with the full art resampled the same way.
    art, bg, asset: RGBA floats 0-1 (load(...) / 255). k = device px per mapping px
    (2007 px art on a 402 pt, 3x phone: 1206/2007). Returns the error per device pixel in 8-bit levels;
    report its max and 99th percentile."""
    pm = lambda a: np.concatenate([a[..., :3]*a[..., 3:], a[..., 3:]], -1)
    x, y, w, h = frame; M, N = asset.shape[:2]
    x0, y0, x1, y1 = int(x) - pad, int(y) - pad, int(x + w) + pad + 1, int(y + h) + pad + 1
    box = (int(np.ceil(x0*k)) + 1, int(np.ceil(y0*k)) + 1, int(x1*k) - 1, int(y1*k) - 1)
    gx, gy = np.arange(x0, x1 + 1.0), np.arange(y0, y1 + 1.0)
    B = to_device(pm(bg[y0:y1, x0:x1]), gx, gy, box, k)
    A = to_device(pm(art[y0:y1, x0:x1]), gx, gy, box, k)
    C = to_device(pm(asset), x + np.arange(N + 1)*w/N, y + np.arange(M + 1)*h/M, box, k)
    return np.abs(C + B*(1 - C[..., 3:]) - A)[..., :3].max(-1) * 255
```

**Patching numbers only (keeps the file's formatting).** Tokenize numbers outside string literals, walk the parsed original and the updated object in the same order, assert both have the same structure, and replace only the tokens whose value changed. Then `json.loads(result) == updated` must hold. Format each new value with `json.dumps(tidy(v))`, so tenths come out as `1810.6` and whole numbers as `1815`.

**Padding: "fit to new layout" (Genesis, November 2026).** Use only when the user picks it (padding is their call). Hit
areas that overlap fire both buttons (`ButtonsInputView.items(at:)`), so this splits each overlapping neighbour gap.

```python
import math
EDGES = ['top', 'bottom', 'left', 'right']

def solve_padding(caps, existing, base):
    """caps: {name: [x, y, w, h]}; existing: {name: item extendedEdges dict}; base: representation extendedEdges.
    Every edge starts at max(representation default, existing override); new items start at the default. Each
    overlapping pair of hit areas is split at the middle of the gap between the two CAPS, along the axis where the
    caps don't overlap, rounded down to 0.1 so the areas meet but never overlap."""
    pads = {n: {e: max(base[e], existing.get(n, {}).get(e, base[e])) for e in EDGES} for n in caps}
    def rect(n):
        x, y, w, h = caps[n]; p = pads[n]
        return (x - p['left'], y - p['top'], x + w + p['right'], y + h + p['bottom'])
    floor1 = lambda v: math.floor(v * 10 + 1e-9) / 10
    names = list(caps)
    for _ in range(50):
        changed = False
        for i, m in enumerate(names):
            for n in names[i + 1:]:
                A, B = rect(m), rect(n)
                # 1e-6 tolerance: float noise (219.20000000000002 vs 219.2) otherwise never converges
                if min(A[2], B[2]) - max(A[0], B[0]) <= 1e-6 or min(A[3], B[3]) - max(A[1], B[1]) <= 1e-6:
                    continue
                (ax, ay, aw, ah), (bx, by, bw, bh) = caps[m], caps[n]
                gx = max(bx - (ax + aw), ax - (bx + bw)); gy = max(by - (ay + ah), ay - (by + bh))
                assert gx > 0 or gy > 0, ('caps overlap', m, n)
                if gx >= gy:
                    l, r = (m, n) if ax < bx else (n, m); half = floor1(gx / 2)
                    pads[l]['right'] = min(pads[l]['right'], half); pads[r]['left'] = min(pads[r]['left'], half)
                else:
                    t, b = (m, n) if ay < by else (n, m); half = floor1(gy / 2)
                    pads[t]['bottom'] = min(pads[t]['bottom'], half); pads[b]['top'] = min(pads[b]['top'], half)
                changed = True
        if not changed:
            return pads
    raise AssertionError('padding did not converge')
# write only the edges that differ from the representation default: {e: tidy(v) for e, v in pads[n].items() if tidy(v) != base[e]}
```
