from __future__ import annotations

import logging
from pathlib import Path

from backend.core.config import Settings
from backend.core.workflow_engine_models import WorkflowArtifact

logger = logging.getLogger(__name__)

_TOP_LEVEL_FILENAMES = {"voice.mp3", "subtitles.srt", "thumbnail.png", "script.md", "visual_context.json"}
_SCENE_IMAGE_PREFIX = "scene_"
# F31: canonical character reference portraits (see CharacterReferenceImageService)
# live alongside the scene images — they are production evidence of what each
# recurring figure's locked appearance actually looks like, not scene footage, but
# sorting them into the same images/ folder keeps storage/runs/<id>/ simple.
_CHARACTER_IMAGE_PREFIX = "character_"


class RunArtifactStorageService:
    """Persists a production run's generated artifacts (voice, subtitles, thumbnail,
    scene images, script) to `storage/runs/<run_id>/`, alongside the final video that
    VideoAssemblyService writes to the same folder. Only artifacts actually present
    in the run are written."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def persist(self, run_id: str, artifacts: list[WorkflowArtifact]) -> Path:
        run_dir = Path(self._settings.run_storage_root) / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        for artifact in artifacts:
            if artifact.filename in _TOP_LEVEL_FILENAMES:
                self._write(run_dir / artifact.filename, artifact)
            elif artifact.filename.endswith(".png") and (
                artifact.filename.startswith(_SCENE_IMAGE_PREFIX) or artifact.filename.startswith(_CHARACTER_IMAGE_PREFIX)
            ):
                images_dir = run_dir / "images"
                images_dir.mkdir(exist_ok=True)
                self._write(images_dir / artifact.filename, artifact)

        return run_dir

    def _write(self, path: Path, artifact: WorkflowArtifact) -> None:
        data = artifact.content_bytes if artifact.content_bytes is not None else artifact.content.encode("utf-8")
        path.write_bytes(data)
