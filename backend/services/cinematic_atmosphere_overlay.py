from __future__ import annotations

from collections.abc import Callable

from backend.schemas.shots import AtmosphereOverlayType

# Each builder returns a pure ffmpeg -vf filter fragment (no external asset files) meant to
# be appended, comma-separated, after the camera-movement filter in the same clip render.


def _film_grain() -> str:
    return "noise=alls=20:allf=t+u"


def _vignette() -> str:
    return "vignette=PI/5"


def _light_rays() -> str:
    # Soft radial glow approximation from an upper-corner light source. Not literal
    # volumetric ray tracing — a lightweight, pure-filter approximation for v1.
    return "geq=lum='p(X,Y)+40*exp(-((X-W*0.2)*(X-W*0.2)+(Y-H*0.1)*(Y-H*0.1))/(2*pow(W*0.4\\,2)))':cb='p(X,Y)':cr='p(X,Y)'"


def _dust_particles() -> str:
    return "noise=alls=6:allf=t+u,gblur=sigma=0.5"


_BUILDERS: dict[AtmosphereOverlayType, Callable[[], str]] = {
    AtmosphereOverlayType.FILM_GRAIN: _film_grain,
    AtmosphereOverlayType.VIGNETTE: _vignette,
    AtmosphereOverlayType.LIGHT_RAYS: _light_rays,
    AtmosphereOverlayType.DUST_PARTICLES: _dust_particles,
}


def build_atmosphere_filter(overlay: AtmosphereOverlayType) -> str:
    """Returns a pure ffmpeg -vf filter fragment for `overlay`. Only called when a Shot
    explicitly sets an atmosphere ("only when instructed") — never invoked automatically.

    Fog/rain/snow are intentionally not supported here yet: they need particle/asset-based
    compositing, not a one-line filter. Add a new AtmosphereOverlayType member plus a
    builder function + _BUILDERS entry here when that's implemented — no other file needs
    to change.
    """
    return _BUILDERS[overlay]()
