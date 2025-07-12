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
    def download_to_file(self, file_id: str, output_path: str | Path) -> None: ...
    
    @abc.abstractmethod
    def list_files(self, query: str) -> Iterable[DriveFile]: ...