## Appendix F: CoreGraphics end-to-end compositor (Genesis, November 2026)

`deltapdf.swift` (Appendix C) renders one PDF the way DeltaCore does. `compose.swift` renders a **whole skin**:
- Each PDF goes through DeltaCore's `UIImage.image(withPDFData:targetSize:)` logic: aspect-fit into the target, then a
  bitmap of `ceil(size × scale)` pixels.
- The result is drawn into its frame the way a `UIImageView` does (`scaleToFill`). The background fills the mapping size.

This is the check that catches what MuPDF can't: soft masks or highlights lost through rebasing, aspect-fit slack on
shared caps, and Apple's mesh seams.

```bash
swiftc -O compose.swift -o compose
./compose 3 rest.png 320 250 iphone_portrait_background.pdf  a_portrait.pdf 180.3 122 38.6 38.6  dpad.pdf 25 63.5 99 99 ...
./compose 3 art.png  320 250 --art iphone_portrait_clean.pdf      # the full art through the same code
# pressed: pass each frame inset by 2 (x+2, y+2, w-4, h-4)
```

Use scale 3 for iPhone and 2 for iPad. Build the argument list from the finished `info.json` and the files in the
deliverables folder, so you test exactly what ships.

```swift
// compose.swift: Delta's skin drawing on macOS, end to end.
// Usage: compose scale out.png W H background.pdf [cap.pdf x y w h]...
//        compose scale out.png W H --art art.pdf
import Foundation
import CoreGraphics
import AVFoundation
import ImageIO
import UniformTypeIdentifiers

func rasterize(_ path: String, _ targetSize: CGSize, _ screenScale: CGFloat) -> CGImage {
    let data = try! Data(contentsOf: URL(fileURLWithPath: path))
    let document = CGPDFDocument(CGDataProvider(data: data as CFData)!)!
    let page = document.page(at: 1)!
    let pageFrame = page.getBoxRect(.cropBox)
    var destinationFrame = AVMakeRect(aspectRatio: pageFrame.size, insideRect: CGRect(origin: .zero, size: targetSize))
    destinationFrame.origin = .zero
    let width = Int((destinationFrame.width * screenScale).rounded(.up))
    let height = Int((destinationFrame.height * screenScale).rounded(.up))
    let context = CGContext(data: nil, width: width, height: height, bitsPerComponent: 8, bytesPerRow: 0,
                            space: CGColorSpace(name: CGColorSpace.sRGB)!, bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
    context.scaleBy(x: screenScale, y: screenScale)
    context.translateBy(x: 0, y: destinationFrame.height)
    context.scaleBy(x: 1, y: -1)
    // DeltaCore's drawing code, unchanged
    context.saveGState()
    let transform = CGAffineTransform.identity.scaledBy(x: 1.0, y: -1.0).translatedBy(x: 0.0, y: -targetSize.height)
    context.concatenate(transform)
    destinationFrame = destinationFrame.applying(transform)
    let aspectScale = min(destinationFrame.width / pageFrame.width, destinationFrame.height / pageFrame.height)
    context.translateBy(x: destinationFrame.minX, y: destinationFrame.minY)
    context.scaleBy(x: aspectScale, y: aspectScale)
    context.drawPDFPage(page)
    context.restoreGState()
    return context.makeImage()!
}

let a = CommandLine.arguments
let scale = CGFloat(Double(a[1])!)
let W = CGFloat(Double(a[3])!), H = CGFloat(Double(a[4])!)
let canvas = CGContext(data: nil, width: Int(W * scale), height: Int(H * scale), bitsPerComponent: 8, bytesPerRow: 0,
                       space: CGColorSpace(name: CGColorSpace.sRGB)!, bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
canvas.interpolationQuality = .high
canvas.scaleBy(x: scale, y: scale)
canvas.translateBy(x: 0, y: H)
canvas.scaleBy(x: 1, y: -1)          // top-left origin, like UIKit
func draw(_ img: CGImage, _ r: CGRect) {
    canvas.saveGState()
    canvas.translateBy(x: r.minX, y: r.maxY)
    canvas.scaleBy(x: 1, y: -1)
    canvas.draw(img, in: CGRect(x: 0, y: 0, width: r.width, height: r.height))
    canvas.restoreGState()
}
if a[5] == "--art" {
    draw(rasterize(a[6], CGSize(width: W, height: H), scale), CGRect(x: 0, y: 0, width: W, height: H))
} else {
    draw(rasterize(a[5], CGSize(width: W, height: H), scale), CGRect(x: 0, y: 0, width: W, height: H))
    var i = 6
    while i + 4 < a.count {
        let r = CGRect(x: Double(a[i + 1])!, y: Double(a[i + 2])!, width: Double(a[i + 3])!, height: Double(a[i + 4])!)
        draw(rasterize(a[i], r.size, scale), r)
        i += 5
    }
}
let dest = CGImageDestinationCreateWithURL(URL(fileURLWithPath: a[2]) as CFURL, UTType.png.identifier as CFString, 1, nil)!
CGImageDestinationAddImage(dest, canvas.makeImage()!, nil)
CGImageDestinationFinalize(dest)
```

**Reading the result: split the errors by whether they sit on an edge of the art.** Delta's own pipeline (rounded-up
bitmap, then a stretch into a fractional frame) softens every edge slightly, so a raw max is meaningless (127–180
levels on Genesis, all on outlines and letter edges). What matters is the error away from edges.

```python
import numpy as np
from PIL import Image
pm = lambda X: X[..., :3] * X[..., 3:] / 255
A = np.asarray(Image.open('art.png').convert('RGBA'), float)
R = np.asarray(Image.open('rest.png').convert('RGBA'), float)
d = np.abs(pm(A) - pm(R)).max(-1)
L = pm(A).mean(-1)
g = np.maximum(np.abs(np.diff(L, axis=0, append=L[-1:])), np.abs(np.diff(L, axis=1, append=L[:, -1:])))
edge = g > 12
for _ in range(2):                                    # grow the edge map by 2 px
    e = edge.copy(); e[1:] |= edge[:-1]; e[:-1] |= edge[1:]; e[:, 1:] |= edge[:, :-1]; e[:, :-1] |= edge[:, 1:]; edge = e
print('within 2: %.3f%%  >16 all on edges: %s  off-edge max %.0f  alpha diff %.0f'
      % ((d <= 2).mean() * 100, edge[d > 16].all(), d[~edge].max(), np.abs(A[..., 3] - R[..., 3]).max()))
```

**Genesis reference (all eight representations, from the final package):** 97.9–99.7% of pixels within 2 levels;
every pixel more than 16 levels off on an art edge; off-edge max 10–12; alpha identical. Pressed wells: 0–3 levels,
measured ≥0.6 pt clear of the pressed cap's edge (SKILL.md, Part 2).
