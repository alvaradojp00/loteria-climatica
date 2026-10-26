"""Downscale the original card fronts for the web.

The print masters are 3-6 MB each; the deck page needs twelve of them at once.
This writes 760px-wide JPEGs to assets/web/, which the API serves instead.
Run once after Genesis; re-run is harmless.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agents.genesis import CATALOG, sources_for
from config import ASSETS

OUT = ASSETS / "web"
WIDTH = 760


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    total_before = total_after = 0
    for number, (slug, *_rest) in sorted(CATALOG.items()):
        # English card 11 has no print front; the Spanish set does, and the
        # art is identical because the card name is printed in Spanish on both.
        src = (sources_for(number, "en")["front"]
               or sources_for(number, "es")["front"]
               or sources_for(number, "es")["social"])
        if not src:
            print(f"  {number:>2} no front image")
            continue
        im = Image.open(src).convert("RGB")
        im.thumbnail((WIDTH, WIDTH * 3))
        dst = OUT / f"{number:02d}-{slug}.jpg"
        im.save(dst, format="JPEG", quality=86, optimize=True, progressive=True)
        before, after = src.stat().st_size, dst.stat().st_size
        total_before += before
        total_after += after
        print(f"  {number:>2} {slug:<22} {before // 1024:>5} KB -> {after // 1024:>4} KB")
    print(f"\ntotal {total_before // 1024 // 1024} MB -> {total_after // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
