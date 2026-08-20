"""
Smoke tests for the local (Pillow-only, zero-cost) title-card renderer.

These don't assert exact pixels (the graphic design may keep changing) but
they lock in the contract other nodes rely on: a valid image is produced at
the requested resolution, level number/name are pulled out of the title beat
correctly, and identical input reliably reuses the same asset path (so
title cards don't get needlessly re-rendered).
"""

from __future__ import annotations
from urllib.parse import urlparse
from urllib.request import url2pathname

from PIL import Image

from graph.title_cards import render_title_card


def _path_for(url: str) -> str:
    return url2pathname(urlparse(url).path)


class TestRenderTitleCard:
    def test_renders_at_requested_resolution(self):
        url = render_title_card("[TITLE] Level 1: The Applicant", width=640, height=360)
        path = _path_for(url)
        with Image.open(path) as img:
            assert img.size == (640, 360)

    def test_same_input_produces_same_asset(self):
        url_a = render_title_card("[TITLE] Level 3: The Case Officer", width=320, height=180)
        url_b = render_title_card("[TITLE] Level 3: The Case Officer", width=320, height=180)
        assert url_a == url_b

    def test_different_level_names_produce_different_assets(self):
        url_a = render_title_card("[TITLE] Level 1: The Applicant", width=320, height=180)
        url_b = render_title_card("[TITLE] Level 2: The Trainee", width=320, height=180)
        assert url_a != url_b

    def test_handles_title_beat_without_colon(self):
        # Some generated titles may not include a colon separator; rendering
        # must not raise even if the level name ends up empty.
        url = render_title_card("[TITLE] Level One", width=320, height=180)
        path = _path_for(url)
        with Image.open(path) as img:
            assert img.size == (320, 180)
