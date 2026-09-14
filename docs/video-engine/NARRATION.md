# Narration

Provider on **new jobs** is Gemini 3.1 Flash TTS (`python -m channel tts`, model `gemini-3.1-flash-tts-preview`, voice Charon) when `GEMINI_API_KEY` is set. The engine writes `tts_chunks.txt` and `audio/chunks/*.wav`, concatenates them, then runs ingest-audio. `--resume` does the same automatically. Audio tags stay off unless `--audio-tags`.

If the key is missing, **imported audio** still works: copy `script.txt` into ElevenLabs (or any TTS). The engine never calls ElevenLabs, Edge, or Kokoro on this path. Missing audio is a wait state (`WAIT_AUDIO`), not a fallback to another TTS.

Shipped recuts whose spec still says `voice: kokoro` keep Kokoro (`KOKORO_LOCK` in `channel/engine.py`). Default speaker `am_liam`.

Pinned word budgets in `channel/config.py`:

| | WTRT | How They Really Make Money | How They Took Over | Quiet Wealth |
|---|---|---|---|---|
| Words | 800–2500 | 800–2500 | 800–2500 | 5,600–5,800 |
| Runtime | ~5–15 min | ~5–15 min | ~5–15 min | ~32–36 min |
| Spoken pacing | 1.0–1.15 | 1.0–1.15 | 1.0–1.15 | 1.0–1.15 |
| Default | 1.15 | 1.15 | 1.15 | 1.15 |
| Voice | third person | third person | third person | second person |

Shipped recuts may be slower. Costco is locked at **0.92** Kokoro. Do not recut a locked slug unless the user asks.

Spoken English. Documentary channels are third person. Quiet Wealth is second person. Write as if a sharp five-year-old is watching with an adult: tiny words, cause then effect, funny when the evidence is funny. Calendar years as digits (`1995`). No “today is DATE”. `the_thought` / `title_payoff` must be said in the VO.

Scene cuts come from pauses in the finished voice-over (`python -m channel ingest-audio`), not from word-count chunks. Drop-folder cuts (`python -m channel drop`) cut on the start clock in the still filename (`[00-13]_….jpg`) instead, and assemble without burned captions.

WTRT is **not** a Short. Older shipped cuts may be shorter or longer; new titles follow the word budgets above.
