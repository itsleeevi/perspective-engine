"""Cost-table arithmetic for provider pricing helpers."""

from __future__ import annotations

from adapters.pricing import openai_chat_cost


class TestOpenAIChatCost:
    def test_plain_tokens_use_full_input_rate(self):
        # Terra: $2 / $12 per MTok. 1_000 in + 500 out = 0.002 + 0.006.
        assert openai_chat_cost("gpt-5.6-terra", 1_000, 500) == 0.008

    def test_cached_reads_bill_at_one_tenth(self):
        # 2_000 cached reads at 0.1 × $2/MTok = 0.0004; no output.
        cost = openai_chat_cost(
            "gpt-5.6-terra",
            input_tokens=2_000,
            output_tokens=0,
            cached_tokens=2_000,
        )
        assert cost == 2_000 * (2.00 / 1_000_000) * 0.10

    def test_cache_writes_bill_at_one_and_a_quarter(self):
        cost = openai_chat_cost(
            "gpt-5.6-terra",
            input_tokens=2_000,
            output_tokens=0,
            cache_write_tokens=2_000,
        )
        assert cost == 2_000 * (2.00 / 1_000_000) * 1.25

    def test_mixed_cached_written_and_plain(self):
        # Matches the official example shape: 2000 cached + 400 written + 200
        # plain, plus some output.
        cost = openai_chat_cost(
            "gpt-5.6-terra",
            input_tokens=2_600,
            output_tokens=100,
            cached_tokens=2_000,
            cache_write_tokens=400,
        )
        rate = 2.00 / 1_000_000
        expected = (
            200 * rate
            + 2_000 * rate * 0.10
            + 400 * rate * 1.25
            + 100 * (12.00 / 1_000_000)
        )
        assert cost == expected
