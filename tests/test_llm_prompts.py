"""Prompt helpers stay split without dropping required instructions."""

from __future__ import annotations

from adapters.llm import openai_llm
from adapters.llm import _prompts


class TestWriteScriptPrompt:
    def test_system_prompt_contains_format_and_json_schema(self):
        system = _prompts.write_script_system_prompt()
        assert "FORMAT" in system
        assert '"hook"' in system
        assert "levels" in system

    def test_user_prompt_carries_topic_and_word_budget(self):
        user = _prompts.write_script_user_prompt("CIA ranks", "", 9.0)
        assert "CIA ranks" in user
        assert "HARD CEILING" in user

    def test_combined_prompt_includes_both_halves(self):
        combined = _prompts.write_script_prompt("CIA ranks", "", 9.0)
        assert _prompts.write_script_system_prompt() in combined
        assert "CIA ranks" in combined


class TestVisualizePrompt:
    def test_system_prompt_is_stable_across_batches(self):
        a = _prompts.visualize_system_prompt()
        b = _prompts.visualize_system_prompt()
        assert a == b
        assert "shot_type" in a
        assert "extreme close-up" in a

    def test_user_prompt_lists_every_fragment(self):
        user = _prompts.visualize_user_prompt(
            ["You sit down.", "They ask why."], topic="Secret Service"
        )
        assert "[0] You sit down." in user
        assert "[1] They ask why." in user
        assert "Secret Service" in user
        assert "0 to 1" in user

    def test_combined_prompt_includes_rules_and_fragments(self):
        combined = _prompts.visualize_chunk_prompt(["You sit down."])
        assert _prompts.visualize_system_prompt() in combined
        assert "[0] You sit down." in combined

    def test_system_prompt_is_long_enough_to_cache(self):
        # GPT-5.6 requires >= 1024 tokens through the breakpoint. A rough
        # 4-chars-per-token floor means the rule block must be well over
        # 4k characters or the explicit cache write is silently skipped.
        assert len(_prompts.visualize_system_prompt()) > 4_000


class TestOpenAIReasoningSettings:
    def test_storyboard_reasoning_is_disabled(self):
        import inspect
        from adapters.llm import openai_llm

        src = inspect.getsource(openai_llm)
        assert '_STORYBOARD_REASONING = "none"' in src
        assert "reasoning_effort=_STORYBOARD_REASONING" in src
        assert "prompt_cache_options" in src

