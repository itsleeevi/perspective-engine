# Custom narrative videos

Operational playbook for the one-off YouTube cuts (Putin-Americans, Hitler-Americans, and whatever title comes next). Read this **before** generating a new video. After a cut lands, update `docs/videos/` so the next agent does not invent a second copy of the last story.

## Hard rules

1. **New title, new story.** Do not clone the previous video’s beat sheet, metaphors, or “folder / coupon / two Americas / machine” spine. Recurring format (third-person narrator, still slideshow, fill-frame, Kokoro) is allowed. Recurring plot is not.
2. **Narrator is third person.** Talk *about* the hero. Never “I” as the hero. Everyday American English. Short sentences. Count things. Promise, then pay off.
3. **Voice is Kokoro `am_liam`, not ElevenLabs, not Edge.** Local, $0. Models live in `assets/models/kokoro/` (gitignored). Set `NARRATION_WPM=205` **before** importing `graph.script_fixture` so chunk size matches long-form Kokoro (~205 wpm at speed 1.0). ElevenLabs Liam stays 166 wpm; do not change that default.
4. **Picture follows speech.** Cuts land on sentence/clause pauses. Kokoro synthesises in ~80-word packs with phoneme-word timings (interpolated if the count is off by a few). Do not fall back to Edge. Do not synth one tiny caption at a time (slideshow cadence).
5. **Scenes must follow each other.** Lock 3–5 sets and 1–2 props (office, book, everyman, soldier). Match-cut the prop. Callback the opening image at the end. Hero is not in every frame. Same face, same suit, same book — say “SAME” in every still prompt. GenerateImage gets no memory unless you pass a reference still.
6. **Fill the frame.** Grok often emits 1536×1024 (3:2). Cover-crop to 16:9 on ingest (`cover_crop_16x9`, keep the **top** on thumbnails so type survives). Assemble uses `force_original_aspect_ratio=increase` then crop. YouTube thumbs must be **1280×720 JPEG**, never the 3:2 PNG — a 3:2 file in a 16:9 slot is black side bars.
7. **Hollywood, not a lecture.** Cold open, open loops (“Stay. I will count the fakes.”), numbered list the viewer can hold, smash cuts, match cuts, one object as the spine, button that restates the mechanism in one line.
8. **No Nazi flags, swastikas, armbands, camps, gore.** No photoreal celebrity politician faces. Historical leads are stylized graphic-novel, not photographs. Mustache on Hitler stills is often blocked; charcoal suit + hard side-part + clean-shaven is the stills workaround. Thumbnails can push likeness harder.
9. **When the video is done, update markdown.** Add or rewrite `docs/videos/<slug>.md` (title, spine, what not to copy, voice, stills prefix, output path, WPM, thumb files). Touch this playbook if a rule changed. Touch `AGENTS.md` if the contract changed.

## Pipeline (this repo, this phase)

JSON fixture → `fixture_to_beats` / `split_beat_into_chunks` → one Grok still per chunk → `scripts/run_*_americans.py` (prebuilt stills adapter, auto-approve HITL, Kokoro, 4K assemble).

Do not run two assemble scripts at once. 4K encode is CPU-bound (`_ENCODE_CONCURRENCY = 3`).

## Voice / sync checklist

- `adapters/voice/kokoro.py` — default voice `am_liam`, speed `1.0`, packs of 80 words.
- Chunking WPM must equal the voice you will actually use (`NARRATION_WPM` env).
- If picture changes mid-word, timings failed: check pack size and `_resize_offsets`. If picture flashes every 2s, WPM is too low for that voice (too many words per estimated 4s, then audio shrinks the hold).
- Probe a new voice on a punchy sentence before a full render (`assets/models/kokoro/probe/`).

## Thumbnails / YouTube

- Generate 16:9, then **top-crop** 3:2 masters to 1280×720 JPEG.
- Upload file: `assets/youtube/thumbnail_upload_1280x720.jpg` (or the titled `*_1280x720.jpg`).
- Description: search phrase in the first 200 characters; chapters starting at `0:00`; synthetic-content disclosure on.
- Copy-paste kit lives under `assets/youtube/` (gitignored). Log the paths in `docs/videos/`.
