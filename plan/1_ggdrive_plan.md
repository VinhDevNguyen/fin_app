# BƯỚC 1 – GOOGLE DRIVE

(ta sẽ đi rất “hands-on”, kèm code skeleton, test và lý do pattern)

---

## 1. Design trước khi gõ code

| Thành phần           | Kiểu                 | Nhiệm vụ                                                  | Pattern                 |
| -------------------- | -------------------- | --------------------------------------------------------- | ----------------------- |
| `DriveGateway`       | **ABC** (interface)  | Khai báo các hành vi chung: `download`, `list`, `search`… | *Port* trong Clean-Arch |
| `GoogleDriveGateway` | implementation       | Thực thi Port bằng Google Drive API                       | *Adapter*               |
| `DriveAuthStrategy`  | Enum / lớp nhỏ       | Lựa chọn **OAuth client** hay **Service Account**         | *Strategy*              |
| `DriveFile`          | dataclass            | DTO trả ra khi gọi `list_files()`                         | –                       |
| `Settings`           | Singleton (pydantic) | Đọc `.env` (scopes, path key, v.v.)                       | *Singleton*             |

> Nhờ **Port (interface) + Adapter**, nếu mai này bạn muốn xài Dropbox chỉ việc thêm `DropboxGateway` mà không sửa service khác.

---

## 2. Cấu trúc thư mục (chỉ riêng tầng Drive)

```
bank_statement_ai/
│

├── infrastructure/
│   ├── __init__.py
│   ├── drive_gateway.py          # interface
│   ├── google_drive_gateway.py   # Adapter chính
│   └── auth/
│       ├── __init__.py
│       ├── oauth.py              # Installed-App / browser flow
│       └── service_account.py    # Server-to-server flow
│
└── tests/
    └── infrastructure/
        └── test_google_drive_gateway.py
```

---

## 3. Chi tiết code

### 3.1 Interface

```python
# infrastructure/drive_gateway.py
from __future__ import annotations
import abc
from pathlib import Path
from typing import Iterable, Protocol
from dataclasses import dataclass

@dataclass
class DriveFile:
    id: str
    name: str
    mime_type: str
    size: int | None = None

class DriveGateway(Protocol):
    @abc.abstractmethod
    def download(self, file_id: str) -> bytes: ...
    @abc.abstractmethod
    def list_files(self, query: str) -> Iterable[DriveFile]: ...
```

### 3.2 Auth strategies

```python
# infrastructure/auth/oauth.py
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

def get_oauth_creds(creds_path: Path, token_path: Path) -> Credentials:
    creds: Credentials | None = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())
    return creds
```

```python
# infrastructure/auth/service_account.py
from google.oauth2 import service_account

def get_service_account_creds(json_key: str, scopes: list[str]):
    return service_account.Credentials.from_service_account_file(json_key, scopes=scopes)
```

### 3.3 GoogleDriveGateway

```python
# infrastructure/google_drive_gateway.py
from __future__ import annotations
import io, functools
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from .drive_gateway import DriveGateway, DriveFile
from .auth import oauth, service_account

class GoogleDriveGateway(DriveGateway):
    def __init__(self, credentials, cache_discovery=False):
        self.service = build("drive", "v3", credentials=credentials, cache_discovery=cache_discovery)

    # ---------- factory helpers ----------
    @classmethod
    def from_oauth(cls, creds_path="credentials.json", token_path="token.json"):
        creds = oauth.get_oauth_creds(Path(creds_path), Path(token_path))
        return cls(creds)

    @classmethod
    def from_service_account(cls, key_path="sa.json", scopes=None):
        scopes = scopes or ["https://www.googleapis.com/auth/drive.readonly"]
        creds  = service_account.get_service_account_creds(key_path, scopes)
        return cls(creds)

    # ---------- port implementations ----------
    def download(self, file_id: str, *, chunk_size: int = 256 * 1024) -> bytes:
        """Download **blob** file content (PDF) via files.get & alt=media."""
        request = self.service.files().get_media(fileId=file_id)  # alt=media tự gắn khi gọi client lib
        fh      = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request, chunksize=chunk_size)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.seek(0)
        return fh.read()

    def list_files(self, query: str) -> list[DriveFile]:
        """Simple wrapper cho files().list()."""
        results = self.service.files().list(q=query,
                                            fields="files(id, name, mimeType, size)").execute()
        return [DriveFile(f["id"], f["name"], f["mimeType"], int(f.get("size", 0)))
                for f in results.get("files", [])]
```

**Tại sao dùng `files().get_media`?** Đó là cách chính thức để tải file nhị phân, `alt=media` được client lib tự thêm, phù hợp hướng dẫn của Google Drive API([Google for Developers][1]).

### 3.4 Settings (pydantic v2)

```python
# bank_statement_ai/config.py
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    gdrive_auth_mode: str = Field("oauth", validation_alias="GDRIVE_AUTH_MODE")
    gdrive_credentials: str = "credentials.json"
    gdrive_token: str = "token.json"
    gdrive_sa_key: str | None = None

settings = Settings()  # singleton
```

Trong `PipelineFactory`, bạn chọn adapter:

```python
def make_drive_gateway() -> DriveGateway:
    if settings.gdrive_auth_mode == "oauth":
        return GoogleDriveGateway.from_oauth(settings.gdrive_credentials, settings.gdrive_token)
    return GoogleDriveGateway.from_service_account(settings.gdrive_sa_key)
```

---

## 4. Test tự động với Pytest

### 4.1 Fake download (unit test – không chạm mạng)

```python
# tests/infrastructure/test_google_drive_gateway.py
import io, pytest
from unittest.mock import patch, MagicMock
from bank_statement_ai.infrastructure.gdrive.google_drive_gateway import GoogleDriveGateway

@pytest.fixture
def fake_service(mocker):
    svc = MagicMock()
    media_req = MagicMock()
    svc.files().get_media.return_value = media_req
    mocker.patch("googleapiclient.discovery.build", return_value=svc)
    mocker.patch("googleapiclient.http.MediaIoBaseDownload",
                 lambda fh, req, chunksize: FakeDownloader(fh))
    return svc

class FakeDownloader:
    def __init__(self, fh): self.fh, self.called = fh, False
    def next_chunk(self):
        if self.called: return None, True
        self.fh.write(b"PDFBYTES"); self.called = True
        return None, False

def test_download(fake_service):
    gw = GoogleDriveGateway(credentials="fake")   # credentials ko dùng vì đã mock build
    data = gw.download("dummy")
    assert data == b"PDFBYTES"
    fake_service.files().get_media.assert_called_once_with(fileId="dummy")
```

### 4.2 Integration (optional)

* Dùng **httpretty** hoặc **responses** để ghi lại response thật, sau đó chạy offline.
* Hoặc chạy trên CI private với Service-Account + folder test chỉ share cho SA.

---

## 5. Hướng dẫn tạo credentials

### 5.1 OAuth “Installed app”

1. Vào *Google Cloud Console* → **APIs & Services** → **OAuth consent screen** → “External” (nếu là Gmail cá nhân).
2. Enable **Drive API**.
3. Tạo *OAuth Client ID* (Desktop). Tải **`credentials.json`**.
4. Chạy `GoogleDriveGateway.from_oauth()` lần đầu; trình duyệt bật lên để bạn login, token lưu tại `token.json`.

### 5.2 Service-Account (server-side)

1. *IAM & Admin* → **Service accounts** → *Create Service Account* → cấp quyền tối thiểu.
2. Tải **JSON key**.
3. Share thư mục/file cần đọc cho e-mail service-account.
4. Chạy `GoogleDriveGateway.from_service_account("sa.json")`.

Google khuyến khích server-side dùng Service-Account cho tác vụ back-end ([Google for Developers][2]).

---

## 6. CLI nhỏ để “pull” PDF

```python
# adapters/cli.py
import typer, pathlib
from bank_statement_ai.services.pipeline import make_drive_gateway

app = typer.Typer()

@app.command()
def pull(file_id: str, out: pathlib.Path = pathlib.Path("downloads")):
    gw = make_drive_gateway()
    pdf_bytes = gw.download(file_id)
    out.mkdir(exist_ok=True, parents=True)
    outfile = out / f"{file_id}.pdf"
    outfile.write_bytes(pdf_bytes)
    typer.echo(f"Saved to {outfile}")

if __name__ == "__main__":
    app()
```

Rồi cấu hình **pyproject.toml**

```toml
[tool.poetry.scripts]
bank-cli = "bank_statement_ai.adapters.cli:app"
```

---

## 7. Recap pattern & lợi ích

* **Port & Adapter:** business code chỉ biết `DriveGateway`. Đổi provider = thêm adapter.
* **Strategy:** `DriveAuthStrategy` chọn OAuth vs SA theo `.env`.
* **Facade:** Ở bước sau, `StatementPipeline` sẽ *gọi* gateway này duy nhất 1 hàm `download`.
* **Repository:** file PDF/JSON sẽ được lưu bởi `StatementRepository`.
* **Testability:** Mock `build()` và `MediaIoBaseDownload` → *unit test chạy 100 ms*, CI không cần Google token thật.

---

### Tiếp theo

Khi Gateway đã ổn, bạn chuyển sang **Bước 2: PDFExtractor** theo cấu trúc tương tự (`PDFExtractor` interface + `PyMuPDFExtractor`).
Nếu cần demo snippet hoặc test sâu hơn, bảo mình!

[1]: https://developers.google.com/workspace/drive/api/guides/manage-downloads "Download and export files  |  Google Drive  |  Google for Developers"
[2]: https://developers.google.com/identity/protocols/oauth2/service-account "Using OAuth 2.0 for Server to Server Applications  |  Google for Developers"
