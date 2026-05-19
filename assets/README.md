# Visual assets

| File | Size | Where it's used |
| ---- | ---- | --------------- |
| `cover.png` | 800 × 400 | README hero image (top of [README.md](../README.md)) |
| `cover@2x.png` | 1600 × 800 | Retina version of cover (browser auto-selects) |
| `cover.svg` | vector | Source for `cover.png` — edit this, not the PNG |
| `logo.png` | 128 × 128 | PyPI project icon, favicon, Twitter avatar |
| `logo@2x.png` | 256 × 256 | Retina version of logo |
| `logo.svg` | vector | Source for `logo.png` |
| `social-preview.png` | 1280 × 640 | GitHub repo social preview (Settings → General → Social preview) |

## Design notes

**Logo** — A document with one highlighted line + a red pin. The whole
brand promise compressed into a single icon: *we point at the exact place
in the PDF where every number came from*.

Colors:
- Teal background (`#0D9488`) — finance + trust
- Cream document (`#FEFCE8`) — paper
- Amber highlight (`#F59E0B`) — the extracted fact
- Red pin (`#DC2626`) — the source-page marker

**Cover** — Three-panel narrative: PDF on the left (with the same
highlighted line as the logo), arrow + validators in the middle, JSON
on the right (with `source_page: 87` matching the PDF's "p. 87" — the
match is intentional, it visually proves traceability).

## Regenerating PNGs from SVGs

PNGs are committed so users don't need a renderer, but if you edit a
SVG, run:

```bash
# Install librsvg once (macOS):
brew install librsvg

# From this directory:
rsvg-convert -w 128  -h 128 logo.svg  -o logo.png
rsvg-convert -w 256  -h 256 logo.svg  -o logo@2x.png
rsvg-convert -w 800  -h 400 cover.svg -o cover.png
rsvg-convert -w 1600 -h 800 cover.svg -o cover@2x.png
rsvg-convert -w 1280 -h 640 cover.svg -o social-preview.png
```

On Linux: `apt install librsvg2-bin` for the same `rsvg-convert` binary.
