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

- WTRT: `GLOBAL_VISUAL_STYLE` — muted historical stick-figure doodle
- Money: `BEHIND_THE_BUSINESS_VISUAL_STYLE` — high-contrast business stick-figure doodle
- Takeover: `HOW_THEY_TOOK_OVER_VISUAL_STYLE` — energetic strategic stick-figure doodle (flywheels, wars, maps)

Do not mix palettes. Shared construction: hand-drawn 2D doodle, bold outlines, solid color blocks, no gradients/shadows/textures. Not photoreal, not 3D, not anime.

Every still also gets `STAGING_QUALITY` from `channel/quality_bar.py`: one idea, one oversized focal object, named lighting, unique staging, no filing-table wallpaper. That is cinema grammar, not a new identity. Spec: `docs/video-engine/QUALITY_BAR.md`.

Recurring public figures get a distinctive cartoon `visual_lock` (hair, jaw, eyes, clothes) so the viewer names them. That is a recognizable cartoon of the real person drawn as a stick-figure doodle, not a photograph, not a cloned voice. Reuse `channel/character_locks.json` and pass the hashed photo plus sheet in `channel/character_sheets/` as Google Flow references. About 35–42% hero on person-titled cuts, 12+ locations, unique visual verb every still. Signature prop in at most 6 scenes. Company-titled cuts may run empty cinematic sets with costume-locked extras.

## Filename rule (from production)

Never put a company, product, or person name in a still **filename**. The model paints that word onto cards and signs. HITL stills use index + timestamp (`000_00-00-04.png`). Drop-folder stills use a bracket clock (`[00-00]_….jpg`). Hashed `generate_filename` tokens stay as aliases. Stored in `channel/engine.py` as `IMAGE_FILENAME_RULE`.

## Render

`channel/engine.py` `RENDER_LOCK`: stills ingest **3840×2160** (Lanczos cover-crop), long output **3840×2160** at 30 fps, libx264 CRF 20, Shorts **1080×1920**. YouTube thumbs 1280×720 and 1080×1920 JPEG. Fill-frame 16:9. Still duration follows the imported-audio pause table, or the `[00-00]` filename clock on a drop-folder cut. Drop-folder cuts assemble without burned captions.
