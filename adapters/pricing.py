"""
Central provider pricing table.

Single source of truth for the per-call cost math used by every real
adapter to populate ``cost_usd`` on its result. Every ``CostEntry`` written
into ``PipelineState.cost_log`` is derived from these numbers rather than
a hardcoded 0.0, so the cost log reflects what a run actually spends.

Prices are USD, verified against each provider's public pricing page on the
date noted below. Provider pricing changes without notice; re-verify before
trusting a real-money estimate for a new model or tier.

Verified 2026-08-11:
  Anthropic Claude Haiku 4.5 (claude-haiku-4-5-20251001)
      https://platform.claude.com/docs/en/about-claude/pricing
      $1.00 / MTok input, $5.00 / MTok output.
  fal.ai FLUX.1 [dev] (fal-ai/flux/dev, fal-ai/flux/dev/image-to-image)
      https://fal.ai/models/fal-ai/flux/dev
      $0.025 per megapixel, billed rounded up to the nearest megapixel.
      Every reference-sheet and derived-still call in this pipeline renders
      at "portrait_4_3" (<=1 megapixel), so each call bills as one image.
  fal.ai Seedance 2.0 Fast (bytedance/seedance-2.0/fast/image-to-video)
      Verified 2026-07-03 at integration time (see adapters/video_gen/fal.py).
      $0.2419 / second of generated video.
  ElevenLabs eleven_multilingual_v2 (Text to Speech API)
      https://elevenlabs.io/pricing/api
      $0.10 per 1,000 characters synthesised.
"""

from __future__ import annotations

# Anthropic Claude Haiku 4.5, USD per token.
_CLAUDE_HAIKU_INPUT_PER_TOKEN = 1.00 / 1_000_000
_CLAUDE_HAIKU_OUTPUT_PER_TOKEN = 5.00 / 1_000_000

# fal.ai FLUX.1 [dev], USD per image at <=1 megapixel.
_FLUX_PER_IMAGE = 0.025

# fal.ai Seedance 2.0 Fast, USD per second of generated video.
_SEEDANCE_PER_SECOND = 0.2419

# ElevenLabs eleven_multilingual_v2, USD per character synthesised.
_ELEVENLABS_PER_CHARACTER = 0.10 / 1_000


def claude_haiku_cost(input_tokens: int, output_tokens: int) -> float:
    """USD cost of one Claude Haiku 4.5 call given its token usage."""
    return (
        input_tokens * _CLAUDE_HAIKU_INPUT_PER_TOKEN
        + output_tokens * _CLAUDE_HAIKU_OUTPUT_PER_TOKEN
    )


def flux_image_cost(num_images: int = 1) -> float:
    """USD cost of generating ``num_images`` FLUX.1 [dev] images (<=1MP each)."""
    return num_images * _FLUX_PER_IMAGE


def seedance_video_cost(duration_seconds: float) -> float:
    """USD cost of one Seedance 2.0 Fast clip of the given duration."""
    return duration_seconds * _SEEDANCE_PER_SECOND


def elevenlabs_tts_cost(num_characters: int) -> float:
    """USD cost of synthesising ``num_characters`` of narration."""
    return num_characters * _ELEVENLABS_PER_CHARACTER
