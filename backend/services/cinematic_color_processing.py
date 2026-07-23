from __future__ import annotations

_DOCUMENTARY_PROFILE = "documentary"

# Gentle contrast lift + slight desaturation — a modern-documentary look. F25 ships exactly
# one preset; ColorProcessing.for_profile already dispatches by name so more presets can be
# added later purely by extending _PROFILES, with no change to callers.
_PROFILES: dict[str, str] = {
    _DOCUMENTARY_PROFILE: "eq=contrast=1.05:saturation=0.92:brightness=0.01",
}


class ColorProcessing:
    def __init__(self, filter_fragment: str) -> None:
        self._filter_fragment = filter_fragment

    def build_filter(self) -> str:
        return self._filter_fragment

    @classmethod
    def for_profile(cls, name: str | None) -> "ColorProcessing":
        """Resolves `Shot.color_profile` to a ColorProcessing instance. None or an
        unrecognized name both fall back to the default documentary grade — the field is a
        real seam (not a dead one), it just has a single preset implemented today."""
        return cls(_PROFILES.get(name or _DOCUMENTARY_PROFILE, _PROFILES[_DOCUMENTARY_PROFILE]))
