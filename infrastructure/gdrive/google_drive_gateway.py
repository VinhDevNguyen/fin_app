from __future__ import annotations

import io
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from ..auth import oauth, service_account
from .drive_gateway import DriveFile, DriveGateway


class GoogleDriveGateway(DriveGateway):
    def __init__(self, credentials, cache_discovery=False):
        self.service = build(
            "drive", "v3", credentials=credentials, cache_discovery=cache_discovery
        )

    @classmethod
    def from_oauth(cls, creds_path="credentials.json", token_path="token.json"):
        creds = oauth.get_oauth_creds(Path(creds_path), Path(token_path))
        return cls(creds)

    @classmethod
    def from_service_account(cls, key_path="sa.json", scopes=None):
        scopes = scopes or ["https://www.googleapis.com/auth/drive.readonly"]
        creds = service_account.get_service_account_creds(key_path, scopes)
        return cls(creds)

    def download(self, file_id: str, *, chunk_size: int = 256 * 1024) -> bytes:
        """Download blob file content (PDF) via files.get & alt=media."""
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request, chunksize=chunk_size)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.seek(0)
        return fh.read()

    def download_to_file(
        self, file_id: str, output_path: str | Path, *, chunk_size: int = 256 * 1024
    ) -> None:
        """Download file directly to specified path."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        request = self.service.files().get_media(fileId=file_id)
        with open(output_path, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request, chunksize=chunk_size)
            done = False
            while not done:
                _, done = downloader.next_chunk()

    def list_files(self, query: str) -> list[DriveFile]:
        """Simple wrapper cho files().list()."""
        results = (
            self.service.files()
            .list(q=query, fields="files(id, name, mimeType, size)")
            .execute()
        )
        return [
            DriveFile(f["id"], f["name"], f["mimeType"], int(f.get("size", 0)))
            for f in results.get("files", [])
        ]
