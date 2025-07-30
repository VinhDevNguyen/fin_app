import io
from unittest.mock import MagicMock, patch

import pytest

from infrastructure.gdrive.google_drive_gateway import GoogleDriveGateway


@pytest.fixture
def fake_service(mocker):
    svc = MagicMock()
    media_req = MagicMock()
    svc.files().get_media.return_value = media_req
    mocker.patch("infrastructure.gdrive.google_drive_gateway.build", return_value=svc)
    mocker.patch(
        "infrastructure.gdrive.google_drive_gateway.MediaIoBaseDownload",
        lambda fh, req, chunksize: FakeDownloader(fh),
    )
    return svc


class FakeDownloader:
    def __init__(self, fh):
        self.fh = fh
        self.called = False

    def next_chunk(self):
        if self.called:
            return None, True
        self.fh.write(b"PDFBYTES")
        self.called = True
        return None, False


def test_download(fake_service):
    mock_credentials = MagicMock()
    gw = GoogleDriveGateway(credentials=mock_credentials)
    data = gw.download("dummy")
    assert data == b"PDFBYTES"
    fake_service.files().get_media.assert_called_once_with(fileId="dummy")


def test_list_files(fake_service):
    fake_service.files().list().execute.return_value = {
        "files": [
            {
                "id": "1",
                "name": "test.pdf",
                "mimeType": "application/pdf",
                "size": "1024",
            },
            {
                "id": "2",
                "name": "doc.xlsx",
                "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "size": "2048",
            },
        ]
    }

    mock_credentials = MagicMock()
    gw = GoogleDriveGateway(credentials=mock_credentials)
    files = gw.list_files("name contains 'test'")

    assert len(files) == 2
    assert files[0].id == "1"
    assert files[0].name == "test.pdf"
    assert files[0].size == 1024
