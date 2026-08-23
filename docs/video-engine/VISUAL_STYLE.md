# Visual style

Styles are frozen in `channel/config.py`. Agents assemble prompts; they do not rewrite the lock.

```text
CHANNEL_VISUAL_STYLE
+ per-title accent (hashed slug; empty on SHIPPED_STYLE_LOCK)
+ character visual_lock (no historical names)
+ location bible
+ ACTION + composition
+ NEGATIVE_STYLE
```

Implemented in `channel/prompts.py`. Company and personal names are stripped from image prompts.

## Channel locks

- WTRT: `GLOBAL_VISUAL_STYLE` — muted historical flat 2D
- Money: `BEHIND_THE_BUSINESS_VISUAL_STYLE` — clean analytical business 2D
- Takeover: `HOW_THEY_TOOK_OVER_VISUAL_STYLE` — energetic strategic 2D (flywheels, wars, maps)

Do not mix palettes. Not photoreal, not 3D, not anime, not painterly.

## Filename rule (from production)

Never put a company, product, or person name in a GenerateImage **filename**. The model paints that word onto cards and signs. Use the job’s `generate_filename` (hashed token), then copy onto `filename` / `copy_to`. Stored in `channel/engine.py` as `IMAGE_FILENAME_RULE`.

## Render

`channel/engine.py` `RENDER_LOCK`: stills ingest 1280×720, long output **3840×2160** at 30 fps, libx264 CRF 20, Shorts **1080×1920**. YouTube thumbs 1280×720 and 1080×1920 JPEG. Fill-frame 16:9. New composition every ~4–8 seconds.
