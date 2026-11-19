## Appendix C: PDF assets with an offset page box

**Symptom.** A PDF cap draws shifted up and right inside its frame with its far edges cut off, or doesn't appear at all, while the background looks fine. In the GBC iPad skin the D-pad was shifted and clipped, and A, B, Start, Select and Menu were missing.

**Cause.** Illustrator can export a cap PDF whose page box keeps the cap's position on the full artboard: `[1180.5 154 1311.5 286]` instead of `[0 0 131 132]`. DeltaCore's `UIImage.image(withPDFData:targetSize:)` (`DeltaCore/Extensions/UIImage+PDF.swift`) reads the crop box but calls `drawPDFPage` without translating by its origin. The content therefore lands (x0, y0) away from where it should: small origins shift the cap, large ones push it off its image entirely. Backgrounds exported at the artboard origin are unaffected. DeltaCore can't be changed, so fix the files.

**Check.** Run `python rebase_pdf_origin.py --check *.pdf` on every PDF the skin references (Step 1, item 6). Anything not at (0, 0) needs rebasing. Record the boxes before rebasing: in top-down coordinates the cap was cut at x = x0, y = artboard height − y1.

**What doesn't work.** Wrapping the page in a translation, either a leading `q 1 0 0 1 -x0 -y0 cm … Q` or the whole page as a Form XObject with that `/Matrix`. MuPDF renders both exactly like the originals, but CoreGraphics evaluates the caps' soft masks (the luminosity masks behind highlights and shading overlays) in the page's base space. The Start/Select pill lost its top highlight, and A and B shaded differently.

**Fix.** `rebase_pdf_origin.py` rewrites coordinates instead of adding a transform:
- Everything the page draws while the CTM is still the page's base space is shifted by (−x0, −y0): path coordinates and the translation of each `cm`.
- Forms and soft-mask groups painted in that space have their BBox and contents shifted the same way, recursively.
- Anything drawn under a `cm` is left alone, because the shifted `cm` already moves it.

Numbers are shifted with exact decimal arithmetic, file names stay the same, and info.json needs no change. It stops with an assertion on anything it doesn't handle rather than guessing: text, inline images, a shading or image painted in base space, an inline soft-mask dictionary, or a CropBox that differs from the MediaBox.

```bash
python rebase_pdf_origin.py --check originals/*.pdf
python rebase_pdf_origin.py originals rebased ipad_large_a.pdf ipad_large_b.pdf ipad_large_dpad.pdf ipad_large_start_select.pdf
```

**Verify through CoreGraphics, not another renderer.** MuPDF and similar renderers honor the page origin, so they can't show the bug or the wrapper failure. `deltapdf.swift` (below) runs DeltaCore's drawing code on macOS. Build it with `swiftc -O deltapdf.swift -o deltapdf`, then check each cap:
1. Render the original with a sixth argument, so the origin is handled: `deltapdf orig.pdf W H 4 want.png correct`.
2. Render the rebased file normally: `deltapdf rebased.pdf W H 4 got.png`.
3. Compare: `got.png` must equal `want.png` exactly (max difference 0).

W and H are the asset's size in points. Rendering an original without the sixth argument reproduces the simulator bug.

**GBC iPad landscape (October 2026).** Each rebased file matched its original exactly through this harness, and the full scene matched the full art. The rewrite touched 2–156 forms and mask groups per file.

| Asset | Page box before | After |
|---|---|---|
| `ipad_large_a.pdf` | `[1180.5 154 1311.5 286]` | `[0 0 131 132]` |
| `ipad_large_b.pdf` | `[1048.5 49.5 1179.5 180.5]` | `[0 0 131 131]` |
| `ipad_large_dpad.pdf` | `[32 34 298 299.5]` | `[0 0 266 265.5]` |
| `ipad_large_start_select.pdf` | `[715.5 164 780.5 192]` | `[0 0 65 28]` |

`rebase_pdf_origin.py` (Python, PyMuPDF):

```python
"""Move a single-page PDF's page box to origin (0, 0) so Delta draws it where it belongs.

Usage:
  python rebase_pdf_origin.py --check a.pdf b.pdf ...      # report page-box origins
  python rebase_pdf_origin.py SRC_DIR DST_DIR a.pdf ...    # write rebased copies to DST_DIR

Coordinates are rewritten, not wrapped: everything the page draws while the CTM is still the
page's base space is shifted by (-x0, -y0) (path coordinates, the translation of `cm`, and,
recursively, the BBox and contents of forms and soft-mask groups painted in that space).
No transform is added, so CoreGraphics evaluates every soft mask exactly as in the original.
Requires PyMuPDF (pip install pymupdf).
"""
import re
import sys
from decimal import Decimal

import fitz

WS = b' \t\r\n\x0c\x00'
DELIM = b'()<>[]{}/%'
PATH_XY = {b'm': 2, b'l': 2, b'c': 6, b'v': 4, b'y': 4}
UNHANDLED = (b'sh', b'BI', b'BT', b'Tm', b'Td', b'TD', b'T*', b"'", b'"', b'd0', b'd1')


def tokenize(data):
    """(kind, bytes, start, end) tokens of a content stream."""
    i, n, out = 0, len(data), []
    while i < n:
        c = data[i:i + 1]
        if c in WS:
            i += 1
            continue
        if c == b'%':
            while i < n and data[i:i + 1] not in (b'\r', b'\n'):
                i += 1
            continue
        s = i
        if c == b'(':
            depth = 0
            while i < n:
                ch = data[i:i + 1]
                if ch == b'\\':
                    i += 2
                    continue
                if ch == b'(':
                    depth += 1
                elif ch == b')':
                    depth -= 1
                    if depth == 0:
                        i += 1
                        break
                i += 1
            out.append(('str', data[s:i], s, i))
        elif data[i:i + 2] in (b'<<', b'>>'):
            out.append(('dict<' if data[i:i + 2] == b'<<' else 'dict>', data[i:i + 2], s, i + 2))
            i += 2
        elif c == b'<':
            j = data.index(b'>', i)
            out.append(('hex', data[s:j + 1], s, j + 1))
            i = j + 1
        elif c in (b'[', b']'):
            out.append((c.decode(), c, s, i + 1))
            i += 1
        elif c == b'/':
            i += 1
            while i < n and data[i:i + 1] not in WS and data[i:i + 1] not in DELIM:
                i += 1
            out.append(('name', data[s:i], s, i))
        else:
            while i < n and data[i:i + 1] not in WS and data[i:i + 1] not in DELIM:
                i += 1
            tok = data[s:i]
            if re.fullmatch(rb'[+-]?(\d+\.?\d*|\.\d+)', tok):
                out.append(('num', tok, s, i))
            else:
                out.append(('op', tok, s, i))
                if tok == b'ID':  # inline image data runs to EI
                    j = data.index(b'EI', i + 1)
                    while not (data[j - 1:j] in WS and (j + 2 >= n or data[j + 2:j + 3] in WS)):
                        j = data.index(b'EI', j + 2)
                    out.append(('imgdata', data[i:j], i, j))
                    i = j
    return out


def operations(data):
    """[(operand tokens, operator token)]"""
    ops, operands, depth = [], [], 0
    for t in tokenize(data):
        if t[0] in ('[', 'dict<'):
            depth += 1
        if t[0] in (']', 'dict>'):
            depth -= 1
        if t[0] == 'op' and depth == 0:
            ops.append((operands, t))
            operands = []
        else:
            operands.append(t)
    return ops


def fmt(v):
    s = format(v.normalize(), 'f')
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def numbers(array_str):
    return [Decimal(t) for t in array_str.strip('[]').split()]


class Rebaser:
    def __init__(self, doc, tx, ty):
        self.d, self.tx, self.ty = doc, tx, ty
        self.done = set()

    @staticmethod
    def ref(s):
        m = re.fullmatch(r'(\d+) 0 R', s.strip())
        return int(m.group(1)) if m else None

    def resources(self, owner, inherited):
        k, v = self.d.xref_get_key(owner, 'Resources')
        if k == 'null':
            return inherited
        return (owner, 'Resources') if k == 'dict' else (self.ref(v), None)

    def lookup(self, res, category, name):
        owner, prefix = res
        key = (prefix + '/' if prefix else '') + category + '/' + name.lstrip('/')
        k, v = self.d.xref_get_key(owner, key)
        return self.ref(v) if k == 'xref' else None

    def form_in_base(self, xref, inherited):
        """A form (or soft-mask group) whose content is evaluated in base space."""
        if xref in self.done:
            return
        self.done.add(xref)
        k, v = self.d.xref_get_key(xref, 'Matrix')
        if k != 'null' and numbers(v) != [1, 0, 0, 1, 0, 0]:
            a, b, c, d, e, f = numbers(v)  # its own Matrix places it: shift that like a cm
            self.d.xref_set_key(xref, 'Matrix', '[%s]' % ' '.join(fmt(t) for t in (a, b, c, d, e - self.tx, f - self.ty)))
            return
        x0, y0, x1, y1 = numbers(self.d.xref_get_key(xref, 'BBox')[1])
        self.d.xref_set_key(xref, 'BBox', '[%s]' % ' '.join(fmt(t) for t in (x0 - self.tx, y0 - self.ty, x1 - self.tx, y1 - self.ty)))
        self.d.update_stream(xref, self.rewrite(self.d.xref_stream(xref), self.resources(xref, inherited)))

    def rewrite(self, data, res):
        out, pos, base = bytearray(), 0, [True]

        def replace(start, end, text):
            nonlocal pos
            out.extend(data[pos:start])
            out.extend(text.encode())
            pos = end

        def shifted(tok, t):
            return fmt(Decimal(tok[1].decode()) - t)

        for operands, op in operations(data):
            o = op[1]
            if o == b'q':
                base.append(base[-1])
            elif o == b'Q':
                base.pop()
            elif not base[-1]:
                continue  # already positioned by a shifted cm
            elif o in PATH_XY or o == b're':
                assert len(operands) == (4 if o == b're' else PATH_XY[o]), (o, operands)
                count = 2 if o == b're' else len(operands)
                vals = [shifted(t, self.tx if i % 2 == 0 else self.ty) if i < count else t[1].decode()
                        for i, t in enumerate(operands)]
                replace(operands[0][2], operands[-1][3], ' '.join(vals))
            elif o == b'cm':
                assert len(operands) == 6
                replace(operands[4][2], operands[5][3], shifted(operands[4], self.tx) + ' ' + shifted(operands[5], self.ty))
                base[-1] = False
            elif o == b'gs':
                gs = self.lookup(res, 'ExtGState', operands[0][1].decode())
                k, v = self.d.xref_get_key(gs, 'SMask')
                assert k != 'dict', 'inline SMask dictionary not handled'
                if k == 'xref':
                    gk, gv = self.d.xref_get_key(self.ref(v), 'G')
                    if gk == 'xref':
                        self.form_in_base(self.ref(gv), res)
            elif o == b'Do':
                x = self.lookup(res, 'XObject', operands[0][1].decode())
                assert self.d.xref_get_key(x, 'Subtype')[1] == '/Form', 'image drawn in base space'
                self.form_in_base(x, res)
            elif o in UNHANDLED:
                raise AssertionError('unhandled operator in base space: %r' % o)
        out.extend(data[pos:])
        return bytes(out)


def page_box(doc):
    page = doc[0]
    assert len(doc) == 1, 'expected a single page'
    assert doc.xref_get_key(page.xref, 'CropBox')[0] == 'null', 'CropBox differs from MediaBox: handle it too'
    return page, numbers(doc.xref_get_key(page.xref, 'MediaBox')[1])


def rebase(src, dst):
    doc = fitz.open(src)
    page, (x0, y0, x1, y1) = page_box(doc)
    if (x0, y0) == (0, 0):
        doc.save(dst)
        return (x0, y0)
    r = Rebaser(doc, x0, y0)
    res = r.resources(page.xref, None)
    for cx in page.get_contents():
        doc.update_stream(cx, r.rewrite(doc.xref_stream(cx), res))
    doc.xref_set_key(page.xref, 'MediaBox', '[0 0 %s %s]' % (fmt(x1 - x0), fmt(y1 - y0)))
    doc.save(dst, garbage=0, deflate=True)
    return (x0, y0)


if __name__ == '__main__':
    if sys.argv[1] == '--check':
        for f in sys.argv[2:]:
            _, (x0, y0, x1, y1) = page_box(fitz.open(f))
            print('%-40s origin (%s, %s)  %s' % (f, fmt(x0), fmt(y0), 'OK' if (x0, y0) == (0, 0) else 'OFFSET: rebase before use'))
    else:
        src_dir, dst_dir = sys.argv[1], sys.argv[2]
        for f in sys.argv[3:]:
            x0, y0 = rebase(src_dir + '/' + f, dst_dir + '/' + f)
            print('%s: origin (%s, %s) -> (0, 0)' % (f, fmt(x0), fmt(y0)))
```

`deltapdf.swift` (macOS):

```swift
// deltapdf.swift: DeltaCore's UIImage.image(withPDFData:targetSize:) run on macOS.
// Usage: deltapdf file.pdf widthPt heightPt scale out.png [correct]
// A sixth argument also translates by the page origin, which shows how the PDF should look.
import Foundation
import CoreGraphics
import AVFoundation
import ImageIO
import UniformTypeIdentifiers

let args = CommandLine.arguments
let data = try! Data(contentsOf: URL(fileURLWithPath: args[1]))
let targetSize = CGSize(width: Double(args[2])!, height: Double(args[3])!)
let screenScale = CGFloat(Double(args[4])!)
guard let provider = CGDataProvider(data: data as CFData),
      let document = CGPDFDocument(provider),
      let page = document.page(at: 1) else { fatalError("bad pdf") }

let pageFrame = page.getBoxRect(.cropBox)
var destinationFrame = AVMakeRect(aspectRatio: pageFrame.size, insideRect: CGRect(origin: .zero, size: targetSize))
destinationFrame.origin = .zero

// Stand-in for UIGraphicsImageRenderer: screen scale, top-left origin
let width = Int((destinationFrame.width * screenScale).rounded(.up))
let height = Int((destinationFrame.height * screenScale).rounded(.up))
let context = CGContext(data: nil, width: width, height: height, bitsPerComponent: 8, bytesPerRow: 0,
                        space: CGColorSpace(name: CGColorSpace.sRGB)!,
                        bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
context.scaleBy(x: screenScale, y: screenScale)
context.translateBy(x: 0, y: destinationFrame.height)
context.scaleBy(x: 1, y: -1)

// DeltaCore's drawing code, unchanged apart from the marked line
context.saveGState()
let transform = CGAffineTransform.identity.scaledBy(x: 1.0, y: -1.0).translatedBy(x: 0.0, y: -targetSize.height)
context.concatenate(transform)
destinationFrame = destinationFrame.applying(transform)
let aspectScale = min(destinationFrame.width / pageFrame.width, destinationFrame.height / pageFrame.height)
context.translateBy(x: destinationFrame.minX, y: destinationFrame.minY)
context.scaleBy(x: aspectScale, y: aspectScale)
if args.count > 6 { context.translateBy(x: -pageFrame.minX, y: -pageFrame.minY) }  // not in DeltaCore
context.drawPDFPage(page)
context.restoreGState()

let destination = CGImageDestinationCreateWithURL(URL(fileURLWithPath: args[5]) as CFURL,
                                                  UTType.png.identifier as CFString, 1, nil)!
CGImageDestinationAddImage(destination, context.makeImage()!, nil)
CGImageDestinationFinalize(destination)
```
