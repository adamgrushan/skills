## Appendix H: Download Skins preview images (Genesis 6-button, November 2026)

Two scripts used with `compose` (Appendix F) to make the `preview` images for Part 6. Genesis 6-button's 14
representations came out as 7 shared 1200 px PNGs (115–487 KB). Compared with the full art drawn through the same
code at the same size, 98.0–99.2% of pixels were within 2 levels, and every larger difference was on a cap outline or
letter edge.

```bash
swiftc -O compose.swift -o compose                      # Appendix F
python3 -I make_previews.py compose <unzipped .deltaskin dir> out
python3 -I make_upload.py <original hosted info.json> out upload/skins/<system>/<identifier>
```

Run `make_upload.py` on the hosted `info.json` *before* any `preview` keys were added. It asserts that no
representation already has one.

**`make_previews.py`**

```python
# Renders a rest-state preview (background + every cap in its frame) for each distinct layout in a skin's info.json.
# Layouts that draw the same background and caps in the same frames share one file, named after the background.
# Every preview is WIDTH px wide: the widest the Download Skins list shows a preview (~400 pt at 3x on iPhone).
# Usage: python3 -I make_previews.py <compose binary> <unzipped skin dir> <output dir>
import json, subprocess, sys
from pathlib import Path

WIDTH = 1200

compose, skin, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
info = json.loads((skin / 'info.json').read_text())

previews = {}  # (background, caps) -> filename
layouts = {}   # "device.displayType.orientation" -> filename

for device, displayTypes in info['representations'].items():
    for displayType, orientations in displayTypes.items():
        for orientation, rep in orientations.items():
            W, H = rep['mappingSize']['width'], rep['mappingSize']['height']
            background = rep['assets'].get('large') or next(iter(rep['assets'].values()))

            caps = []
            for item in rep.get('items', []):
                asset = item.get('asset') or item.get('thumbstick')
                if not asset or 'thumbstick' in item:
                    continue  # previewImage skips thumbsticks and touch screens.
                assert 'width' not in asset, 'explicit asset sizes not handled'
                f = item['frame']
                caps += [str(skin / asset['name']), str(f['x']), str(f['y']), str(f['width']), str(f['height'])]

            key = (background, W, H, tuple(caps))
            if key not in previews:
                name = 'preview_' + background.removesuffix('.pdf').removesuffix('_background') + '.png'
                assert name not in previews.values(), f'{name} would be shared by layouts that draw differently'

                scale = WIDTH / W
                subprocess.run([str(compose), str(scale), str(out / name), str(W), str(H), str(skin / background), *caps], check=True)
                previews[key] = name
                print(f'{name}: {W}x{H} @{scale:.3f}x, {len(caps) // 5} caps')

            layouts[f'{device}.{displayType}.{orientation}'] = previews[key]

(out / 'layouts.json').write_text(json.dumps(layouts, indent=2) + '\n')
```

**`make_upload.py`**

```python
# Builds the upload folder: the hosted info.json with a "preview" key added to each representation, plus the preview PNGs.
# Download Skins shows representation["preview"] if present, falling back to the background in "assets".
# DeltaCore ignores unknown representation keys, so the key is harmless anywhere a skin's info.json is read.
# Only Download Skins reads the hosted info.json. Installing uses the .deltaskin, which is unchanged.
# Usage: python3 -I make_upload.py <hosted info.json> <previews dir with layouts.json> <upload dir>
import json, shutil, sys
from pathlib import Path

hosted, previews, upload = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
raw = hosted.read_text()
info = json.loads(raw)
assert json.dumps(info, indent=2) == raw, 'info.json does not round-trip; patch it as text instead'

layouts = json.loads((previews / 'layouts.json').read_text())
upload.mkdir(parents=True, exist_ok=True)

for device, displayTypes in info['representations'].items():
    for displayType, orientations in displayTypes.items():
        for orientation, rep in orientations.items():
            assert 'preview' not in rep, f'{device}.{displayType}.{orientation} already has a preview'
            orientations[orientation] = {'preview': layouts[f'{device}.{displayType}.{orientation}'], **rep}

(upload / 'info.json').write_text(json.dumps(info, indent=2))

for name in sorted(set(layouts.values())):
    shutil.copy2(previews / name, upload / name)
```
