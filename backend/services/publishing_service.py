from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.core.config import Settings
from backend.schemas.publishing import PublishedVideo
from backend.schemas.research import PublishingPackage

logger = logging.getLogger(__name__)


class PublishingService:
    """Publishes a finalized YouTube publishing package using YouTube Data API v3."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def publish_to_youtube(
        self,
        publishing_package: PublishingPackage,
        user_id: str | None,
    ) -> PublishedVideo:
        metadata = publishing_package.metadata
        video_file_path = str(metadata.get("video_file_path", "")).strip()
        thumbnail_file_path = str(metadata.get("thumbnail_file_path", "")).strip() or None
        playlist_id = str(metadata.get("playlist_id", "")).strip() or None
        requested_visibility = str(metadata.get("visibility", "private")).strip().lower() or "private"
        publish_at_raw = metadata.get("publish_at")

        logger.info(
            "youtube_upload_started",
            extra={"workflow": "youtube_publish", "user_id": user_id, "title": publishing_package.youtube_title},
        )

        publish_at = self._parse_publish_time(publish_at_raw)
        if requested_visibility == "scheduled" and publish_at is None:
            return self._failed_result(
                publishing_package,
                requested_visibility,
                "Scheduled visibility requires metadata.publish_at",
            )

        if not video_file_path:
            return self._failed_result(
                publishing_package,
                requested_visibility,
                "Missing metadata.video_file_path",
            )

        file_path = Path(video_file_path)
        if not file_path.exists() or not file_path.is_file():
            return self._failed_result(
                publishing_package,
                requested_visibility,
                f"Video file not found: {video_file_path}",
            )

        try:
            youtube = self._create_youtube_client()
            video_response = self._upload_video(youtube, publishing_package, file_path)
            video_id = str(video_response.get("id", "")).strip()
            if not video_id:
                return self._failed_result(
                    publishing_package,
                    requested_visibility,
                    "YouTube API upload did not return a video id",
                )
        except Exception as exc:
            logger.exception("youtube_upload_failed", extra={"workflow": "youtube_publish", "user_id": user_id})
            return self._failed_result(
                publishing_package,
                requested_visibility,
                str(exc),
            )

        thumbnail_uploaded = True
        upload_status = "success"
        visibility_error: str | None = None

        try:
            self._set_visibility(youtube, video_id, requested_visibility, publish_at)
        except Exception as exc:
            upload_status = "partial"
            visibility_error = str(exc)

        if thumbnail_file_path:
            try:
                self._upload_thumbnail(youtube, video_id, Path(thumbnail_file_path))
            except Exception:
                thumbnail_uploaded = False

        playlist_error: str | None = None
        if playlist_id:
            try:
                self._assign_playlist(youtube, video_id, playlist_id)
            except Exception as exc:
                upload_status = "partial"
                playlist_error = str(exc)

        published_at = self._parse_published_at(video_response)
        result = PublishedVideo(
            video_id=video_id,
            video_url=f"https://www.youtube.com/watch?v={video_id}",
            title=publishing_package.youtube_title,
            description=self._description_with_chapters(
                publishing_package.youtube_description,
                publishing_package.youtube_chapters,
            ),
            visibility=requested_visibility,
            publish_time=publish_at if requested_visibility == "scheduled" else published_at,
            upload_status=upload_status,
            thumbnail_uploaded=thumbnail_uploaded,
            metadata={
                "status": upload_status,
                "visibility_error": visibility_error,
                "playlist_error": playlist_error,
                "playlist_id": playlist_id,
            },
        )

        logger.info(
            "youtube_upload_completed",
            extra={
                "workflow": "youtube_publish",
                "user_id": user_id,
                "video_id": video_id,
                "upload_status": upload_status,
            },
        )
        return result

    def _create_youtube_client(self) -> Any:
        client_id = self._settings.youtube_oauth_client_id
        client_secret = self._settings.youtube_oauth_client_secret
        refresh_token = self._settings.youtube_oauth_refresh_token
        if not client_id or not client_secret or not refresh_token:
            raise ValueError("Missing YouTube OAuth settings")

        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
        except Exception as exc:  # pragma: no cover - runtime dependency guard
            raise RuntimeError("YouTube dependencies are not installed") from exc

        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri=self._settings.youtube_oauth_token_uri,
            client_id=client_id,
            client_secret=client_secret,
            scopes=[
                "https://www.googleapis.com/auth/youtube.upload",
                "https://www.googleapis.com/auth/youtube",
            ],
        )
        return build("youtube", "v3", credentials=credentials, cache_discovery=False)

    def _upload_video(self, youtube: Any, publishing_package: PublishingPackage, file_path: Path) -> dict[str, Any]:
        from googleapiclient.http import MediaFileUpload

        media_body = MediaFileUpload(str(file_path), chunksize=-1, resumable=True)
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": publishing_package.youtube_title,
                    "description": self._description_with_chapters(
                        publishing_package.youtube_description,
                        publishing_package.youtube_chapters,
                    ),
                    "tags": publishing_package.youtube_tags,
                    "categoryId": "22",
                },
                "status": {
                    "privacyStatus": "private",
                },
            },
            media_body=media_body,
        )

        response = None
        while response is None:
            _, response = request.next_chunk()
        if not isinstance(response, dict):
            raise RuntimeError("Invalid YouTube upload response")
        return response

    def _set_visibility(
        self,
        youtube: Any,
        video_id: str,
        visibility: str,
        publish_at: datetime | None,
    ) -> None:
        if visibility not in {"private", "unlisted", "public", "scheduled"}:
            raise ValueError(f"Unsupported visibility: {visibility}")

        if visibility == "scheduled":
            if publish_at is None:
                raise ValueError("publish_at is required for scheduled uploads")
            status_payload: dict[str, Any] = {
                "privacyStatus": "private",
                "publishAt": publish_at.astimezone(timezone.utc).replace(microsecond=0).isoformat(),
            }
        else:
            status_payload = {"privacyStatus": visibility}

        youtube.videos().update(
            part="status",
            body={"id": video_id, "status": status_payload},
        ).execute()

    def _upload_thumbnail(self, youtube: Any, video_id: str, thumbnail_path: Path) -> None:
        if not thumbnail_path.exists() or not thumbnail_path.is_file():
            raise ValueError("Thumbnail file not found")

        from googleapiclient.http import MediaFileUpload

        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(str(thumbnail_path)),
        ).execute()

    def _assign_playlist(self, youtube: Any, video_id: str, playlist_id: str) -> None:
        youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id,
                    },
                }
            },
        ).execute()

    def _description_with_chapters(self, description: str, chapters: list[str]) -> str:
        clean_description = (description or "").strip()
        clean_chapters = [chapter.strip() for chapter in chapters if chapter.strip()]
        if not clean_chapters:
            return clean_description

        has_all_chapters = all(chapter in clean_description for chapter in clean_chapters)
        if has_all_chapters:
            return clean_description

        if not clean_description:
            return "\n".join(clean_chapters)
        return f"{clean_description}\n\n" + "\n".join(clean_chapters)

    def _parse_publish_time(self, raw_value: object) -> datetime | None:
        if raw_value is None:
            return None
        text = str(raw_value).strip()
        if not text:
            return None

        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("publish_at must be an ISO datetime") from exc

    def _parse_published_at(self, response: dict[str, Any]) -> datetime | None:
        snippet = response.get("snippet") if isinstance(response, dict) else None
        if not isinstance(snippet, dict):
            return None

        raw_value = str(snippet.get("publishedAt", "")).strip()
        if not raw_value:
            return None

        try:
            return datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
        except ValueError:
            return None

    def _failed_result(
        self,
        publishing_package: PublishingPackage,
        visibility: str,
        reason: str,
    ) -> PublishedVideo:
        return PublishedVideo(
            video_id="",
            video_url="",
            title=publishing_package.youtube_title,
            description=publishing_package.youtube_description,
            visibility=visibility,
            publish_time=None,
            upload_status="failed",
            thumbnail_uploaded=False,
            metadata={"status": "failed", "reason": reason},
        )
