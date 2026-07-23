from __future__ import annotations

from abc import ABC, abstractmethod


class DepthEstimator(ABC):
    """Abstraction for local monocular depth estimation on a scene image.

    Not called by anything yet. This is an unused seam so a real depth model (e.g. MiDaS)
    can be wired in later to support depth-based parallax and a true ORBIT camera movement,
    without redesigning the cinematic renderer."""

    @abstractmethod
    def estimate(self, image_bytes: bytes) -> bytes | None:
        """Return a grayscale depth map (near=bright) as PNG bytes, or None if unavailable."""


class NullDepthEstimator(DepthEstimator):
    """Default implementation: depth estimation is not available locally yet."""

    def estimate(self, image_bytes: bytes) -> bytes | None:
        return None
