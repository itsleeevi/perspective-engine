"""
Base interface for image-generation adapters.

Responsible for two tasks:
1. Producing the character reference sheet (multiple angles / expressions).
2. Deriving a per-shot still from the locked reference sheet for each shot.

Every concrete implementation (mock, Flux, etc.) must satisfy this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ReferenceSheetResult:
    """Output of a reference-sheet generation call."""

    image_urls: list[str]
    """URLs to the generated reference images (multiple angles)."""
    style_descriptor: str
    """
    Persistent text descriptor.  Includes at least one deliberately
    distinctive identifying detail for use in all subsequent prompts.
    """


@dataclass
class DerivedStillResult:
    """Output of a per-shot still derivation."""

    still_url: str
    """URL of the derived still, anchored to the reference sheet identity."""


class ImageGenAdapter(ABC):
    """Abstract image-generation adapter."""

    @abstractmethod
    async def generate_reference_sheet(
        self, character_description: str
    ) -> ReferenceSheetResult:
        """
        Generate a character reference sheet.

        The sheet must contain the character from multiple angles,
        expressions, and lighting conditions, generated as a consistent set.
        """

    @abstractmethod
    async def derive_still(
        self,
        shot_prompt: str,
        sheet_image_urls: list[str],
        style_descriptor: str,
    ) -> DerivedStillResult:
        """
        Derive a per-shot still from the reference sheet.

        The still must be anchored to the locked identity in the sheet.
        This is the required bridge between the reference sheet and any
        subsequent video-generation call for a motion shot.
        """
