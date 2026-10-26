# Assets

- **`web/`** — downscaled card fronts (760px JPEG, ~2.4 MB total). This is what
  the application serves, and it is committed.
- **`loteria-cards/`** — the original campaign artwork at print resolution:
  4x6 PNG fronts and backs in English and Spanish, social crops, and print PDFs.
  About 450 MB, so it is **gitignored**.

Nothing at runtime needs `loteria-cards/`. The deck's text was extracted from it
once by `backend/agents/genesis.py` and is committed in
`backend/data/cards.json`; the application reads that.

You need `loteria-cards/` only to re-run:

```bash
python -m agents.genesis   # re-extract card text from the printed art
python make_web_art.py     # regenerate assets/web/
```

The originals are campaign files created during the author's time at
GreenLatinos and are available on request rather than committed here.
