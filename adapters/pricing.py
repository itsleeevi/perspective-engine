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
  fal.ai FLUX.1 [schnell] (fal-ai/flux/schnell)
      https://fal.ai/models/fal-ai/flux/schnell
      $0.003 per megapixel, billed rounded up to the nearest megapixel.
      This is the default stills model: at 2048x1152 (2.36MP -> 3MP billed)
      a scene still costs ~$0.009.
  Microsoft Edge TTS (edge-tts)
      No API, no key, no metered cost. Billed as $0.00.
  fal.ai Seedance 2.0 Fast (bytedance/seedance-2.0/fast/image-to-video)
      Verified 2026-07-03 at integration time (see adapters/video_gen/fal.py).
      $0.2419 / second of generated video.
  ElevenLabs eleven_multilingual_v2 (Text to Speech API)
      https://elevenlabs.io/pricing/api
      $0.10 per 1,000 characters synthesised.

Verified 2026-08-16 (later same day, for the OpenAI authoring cutover):
  OpenAI GPT-5.6 family (chat completions, script + storyboard authoring)
      https://openai.com/api/pricing (per provider listings; see
      adapters/llm/openai_llm.py's AUTHORING_MODEL for the tier chosen).
      Sol/GPT-5.5 (flagship, $5/$30 per MTok), Terra ($2/$12, Sonnet's
      analogue — the default here), Luna ($0.20/$1.20, Haiku's analogue,
      not yet probed against Terra for this format's prompts).

Verified 2026-08-16:
  Anthropic Claude Haiku 4.5 / Sonnet 5 / Sonnet 4.6 / Opus 5
      https://platform.claude.com/docs/en/about-claude/pricing
      Haiku 4.5 ($1/$5 per MTok) is the script and storyboard model: a
      head-to-head against Sonnet 5 ($2/$10) on the same patched prompt
      showed no quality gap (see adapters/llm/anthropic.py's
      AUTHORING_MODEL), so the 2x price difference bought nothing. Sonnet 5
      is kept in the rate table as an available override; note it is
      itself cheaper than Sonnet 4.6/4.5 ($3/$15), so "downgrading" to an
      older Sonnet raises cost rather than lowering it.
  OpenAI gpt-image-1-mini (Images API)
      https://developers.openai.com/api/docs/pricing
      $2.00 / MTok text input, $2.50 / MTok image input, $8.00 / MTok image
      output. Billed from the actual token usage each call reports (a "low"
      quality 1536x1024 landscape image is roughly 400-750 output tokens,
      i.e. ~$0.003-0.006), not a flat per-image number, since output tokens
      vary with actual image content.
"""

from __future__ import annotations

import math

# Anthropic Claude, USD per token by model: (input, output).
# Verified against platform.claude.com/docs/en/about-claude/pricing 2026-08-16.
_CLAUDE_RATES = {
    "claude-haiku-4-5-20251001": (1.00 / 1_000_000, 5.00 / 1_000_000),
    "claude-sonnet-5": (2.00 / 1_000_000, 10.00 / 1_000_000),
    "claude-sonnet-4-6": (3.00 / 1_000_000, 15.00 / 1_000_000),
    "claude-opus-5": (15.00 / 1_000_000, 75.00 / 1_000_000),
}
_CLAUDE_HAIKU = "claude-haiku-4-5-20251001"

# OpenAI GPT-5.6 chat models, USD per token: (input, output).
_OPENAI_CHAT_RATES = {
    "gpt-5.6-sol": (5.00 / 1_000_000, 30.00 / 1_000_000),
    "gpt-5.5": (5.00 / 1_000_000, 30.00 / 1_000_000),
    "gpt-5.6-terra": (2.00 / 1_000_000, 12.00 / 1_000_000),
    "gpt-5.6-luna": (0.20 / 1_000_000, 1.20 / 1_000_000),
}

# fal.ai FLUX.1 [dev], USD per image at <=1 megapixel.
_FLUX_PER_IMAGE = 0.025

# fal.ai FLUX.1 [schnell], USD per megapixel.
_FLUX_SCHNELL_PER_MEGAPIXEL = 0.003

# fal.ai Seedance 2.0 Fast, USD per second of generated video.
_SEEDANCE_PER_SECOND = 0.2419

# ElevenLabs eleven_multilingual_v2, USD per character synthesised.
_ELEVENLABS_PER_CHARACTER = 0.10 / 1_000

# OpenAI image models, USD per token by kind: (text in, image in, image out).
# Verified against platform.openai.com/docs/pricing on 2026-08-16.
_GPT_IMAGE_RATES = {
    "gpt-image-1-mini": (2.00 / 1_000_000, 2.50 / 1_000_000, 8.00 / 1_000_000),
    "gpt-image-1": (5.00 / 1_000_000, 10.00 / 1_000_000, 40.00 / 1_000_000),
    "gpt-image-1.5": (5.00 / 1_000_000, 8.00 / 1_000_000, 30.00 / 1_000_000),
    "gpt-image-2": (5.00 / 1_000_000, 8.00 / 1_000_000, 30.00 / 1_000_000),
}


def claude_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    USD cost of one Claude call given its model and token usage.

    An unknown model is billed at the priciest known rates rather than $0:
    an over-reported cost is the safer error.
    """
    input_rate, output_rate = _CLAUDE_RATES.get(model, _CLAUDE_RATES["claude-opus-5"])
    return input_tokens * input_rate + output_tokens * output_rate


def claude_haiku_cost(input_tokens: int, output_tokens: int) -> float:
    """USD cost of one Claude Haiku 4.5 call given its token usage."""
    return claude_cost(_CLAUDE_HAIKU, input_tokens, output_tokens)


def openai_chat_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    USD cost of one OpenAI chat-completions authoring call.

    An unknown model is billed at the priciest known rate (Sol/GPT-5.5)
    rather than $0, same rationale as ``claude_cost``: an over-reported cost
    is the safer error for a model this table hasn't been updated for yet.
    """
    input_rate, output_rate = _OPENAI_CHAT_RATES.get(
        model, _OPENAI_CHAT_RATES["gpt-5.6-sol"]
    )
    return input_tokens * input_rate + output_tokens * output_rate


def flux_image_cost(num_images: int = 1) -> float:
    """USD cost of generating ``num_images`` FLUX.1 [dev] images (<=1MP each)."""
    return num_images * _FLUX_PER_IMAGE


def flux_schnell_image_cost(width: int, height: int, num_images: int = 1) -> float:
    """
    USD cost of ``num_images`` FLUX.1 [schnell] images at the given size.

    fal bills per megapixel, rounded up to the next whole megapixel.
    """
    megapixels = math.ceil(width * height / 1_000_000)
    return num_images * megapixels * _FLUX_SCHNELL_PER_MEGAPIXEL


def seedance_video_cost(duration_seconds: float) -> float:
    """USD cost of one Seedance 2.0 Fast clip of the given duration."""
    return duration_seconds * _SEEDANCE_PER_SECOND


def elevenlabs_tts_cost(num_characters: int) -> float:
    """USD cost of synthesising ``num_characters`` of narration."""
    return num_characters * _ELEVENLABS_PER_CHARACTER


def gpt_image_cost(
    model: str,
    text_input_tokens: int,
    image_input_tokens: int,
    image_output_tokens: int,
) -> float:
    """
    USD cost of one OpenAI image call given its actual token usage.

    Unlike the flat per-image figures on OpenAI's pricing page (which assume
    a representative output-token count), this is computed from the token
    counts the API actually reports for the call, since image output tokens
    vary with both the model and the generated content — gpt-image-2 bills
    3.75x mini's rate per output token but spends a quarter as many of them
    on the same 1536x1024 image, so the published rates alone are misleading
    about the real difference.

    An unknown model falls back to the priciest known rates rather than
    reporting $0: an under-reported cost is worse than an over-reported one.
    """
    text_rate, image_in_rate, image_out_rate = _GPT_IMAGE_RATES.get(
        model, _GPT_IMAGE_RATES["gpt-image-1"]
    )
    return (
        text_input_tokens * text_rate
        + image_input_tokens * image_in_rate
        + image_output_tokens * image_out_rate
    )
