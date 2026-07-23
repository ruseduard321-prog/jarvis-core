from __future__ import annotations

from backend.schemas.shots import AtmosphereOverlayType
from backend.services.cinematic_atmosphere_overlay import build_atmosphere_filter


def test_film_grain_uses_noise_filter():
    assert "noise=" in build_atmosphere_filter(AtmosphereOverlayType.FILM_GRAIN)


def test_vignette_uses_vignette_filter():
    assert "vignette" in build_atmosphere_filter(AtmosphereOverlayType.VIGNETTE)


def test_light_rays_uses_geq_filter():
    assert "geq=" in build_atmosphere_filter(AtmosphereOverlayType.LIGHT_RAYS)


def test_dust_particles_uses_noise_and_blur():
    filter_fragment = build_atmosphere_filter(AtmosphereOverlayType.DUST_PARTICLES)
    assert "noise=" in filter_fragment
    assert "gblur=" in filter_fragment


def test_every_overlay_type_is_supported():
    for overlay in AtmosphereOverlayType:
        assert build_atmosphere_filter(overlay)
