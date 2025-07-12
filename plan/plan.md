Dưới góc độ Python dev “nặng” OOP, cách dễ bảo trì nhất là **kết hợp Clean-Architecture (Ports & Adapters) + một vài GoF patterns (Facade, Strategy, Repository)**. Ý tưởng: domain (nghiệp vụ) độc lập hoàn toàn khỏi hạ tầng (Google Drive, Gemini, PDFMiner…), nên khi Google đổi API hay bạn muốn chuyển sang OpenAI chỉ cần thêm adapter chứ không “đụng” business-logic.

---

## 1 . Tổng thể các lớp & pattern chính

| Tầng                         | Vai trò                                                                           | Pattern gợi ý                                                                                                      |
| ---------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| **Domain**                   | Mô hình nghiệp vụ thuần: `Transaction`, `Statement`, `Category`…                  | *Entity / Value-Object*                                                                                            |
| **Application / Services**   | Use-case orchestration: `StatementPipeline`, `MetricsService`, `ReportService`…   | *Facade* (để gom nhiều bước thành 1 API), *Strategy* (chọn LLM, PDF engine), *Factory* (tạo pipeline tuỳ cấu hình) |
| **Infrastructure**           | Kết nối thế giới ngoài: Google Drive, Gemini, bộ giải PDF, lưu file hệ thống, DB… | *Adapter / Gateway*, *Repository*                                                                                  |
| **Interface / Presentation** | CLI, REST (FastAPI) hoặc Web (Streamlit)                                          | –                                                                                                                  |

---

### 1.1 Các lớp cốt lõi (một ví dụ)

```python
# domain/models.py
@dataclass
class Transaction:
    date: datetime
    description: str
    amount: Decimal
    sub_category: str | None = None

# services/pipeline.py
class StatementPipeline:
    """Facade gom toàn bộ 1→4."""
    def __init__(
        self,
        drive: DriveGateway,
        pdf_extractor: PDFExtractor,
        llm: LLMExtractor,
        validator: JSONValidator,
        repo: StatementRepository,
    ): ...

    def run(self, file_id: str) -> list[Transaction]:
        pdf_bytes   = self.drive.download(file_id)
        text        = self.pdf_extractor.extract(pdf_bytes)
        raw_json    = self.llm.extract(text)
        txs         = self.validator.parse_transactions(raw_json)
        self.repo.save_json(txs)
        return txs
```

* `DriveGateway`, `PDFExtractor`, `LLMExtractor` đều là **interfaces** (ABC); cài đặt thật nằm trong *infrastructure* (ví dụ `GeminiLLM`, `OpenAIExtractor`, `PdfMinerExtractor`…), chọn runtime bằng **Strategy Pattern**.
* `StatementRepository` ẩn chi tiết lưu JSON / Parquet / DB; tuỳ cấu hình có thể swap.

---

## 2 . Cấu trúc thư mục đề xuất

```
bank_statement_ai/
│
├── pyproject.toml          # poetry / hatch / pip-tools tuỳ bạn
├── .env.example            # GOOGLE_API_KEY, GEMINI_API_KEY...
├── README.md
│
├── bank_statement_ai/
│   ├── __init__.py
│   ├── config.py           # đọc biến môi trường → Settings (pydantic-v2 BaseSettings)
│   │
│   ├── domain/
│   │   ├── __init__.py
│   │   └── models.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pipeline.py     # StatementPipeline (Facade)
│   │   ├── metrics.py      # MetricsService
│   │   └── report.py       # ReportService
│   │
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── drive_client.py     # GoogleDriveGateway
│   │   ├── pdf_extractor.py    # PDFMinerExtractor, PyMuPDFExtractor...
│   │   ├── llm_client.py       # GeminiLLM, GPT4oLLM...
│   │   └── storage.py          # LocalFileRepository / S3Repository
│   │
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── cli.py          # Typer entrypoint
│   │   └── web.py          # FastAPI / Streamlit UI
│   │
│   └── utils/
│       ├── __init__.py
│       └── logging.py
│
└── tests/
    ├── __init__.py
    ├── test_pipeline.py
    ├── test_metrics.py
    └── fixtures/
```

*Ở ngoài* có thể thêm `scripts/` (bash, invoke, makefile), `notebooks/` nếu cần R\&D.

---

## 3 . Dòng chảy dữ liệu chi tiết

```mermaid
flowchart TD
    A[Google Drive<br>PDF] -->|download| B(PDFExtractor)
    B -->|raw text| C(LLMExtractor<br>(Gemini))
    C -->|json str| D(JSONValidator)
    D -->|list[Transaction]| E[Repository<br>(save *.json, *.parquet)]
    E --> F[MetricsService] --> G[ReportService]
```

* `JSONValidator` có thể dùng `pydantic.validate_json()` để chắc cú schema.
* Sau bước `Repository`, bạn gọi hàm `load_data()` (đưa vào `services.data_loader`) để tạo `DataFrame` đã sạch, rồi:

  * `MetricsService` sinh KPIs → cache parquet.
  * `ReportService` plot / xuất PDF, hoặc trả về dict/DF cho Streamlit.

---

## 4 . Một vài chiêu GoF hữu dụng

| Pattern            | Ứng dụng                          | Ghi chú                       |
| ------------------ | --------------------------------- | ----------------------------- |
| **Strategy**       | Đổi LLM, đổi PDF engine           | cấu hình qua YAML hoặc `.env` |
| **Factory Method** | Tạo `StatementPipeline` theo env  | `PipelineFactory(settings)`   |
| **Repository**     | Ẩn cách lưu (file, DB, S3)        | giúp test dễ (FakeRepository) |
| **Facade**         | `StatementPipeline.run()`         | code gọi chỉ 1 hàm duy nhất   |
| **Adapter**        | Quấn Google Drive SDK, Gemini SDK | convert về interface chung    |
| **Singleton**      | `Settings`/`Logger`               | dùng module-level instance    |

---

## 5 . Gợi ý triển khai từng bước

| Bước             | Gói / Lớp                                                       | Lib khuyên dùng                                       |
| ---------------- | --------------------------------------------------------------- | ----------------------------------------------------- |
| 1. Google Drive  | `infrastructure.drive_client.GoogleDriveGateway`                | `google-auth`, `google-api-python-client`, `gdrivefs` |
| 2. PDF → text    | `infrastructure.pdf_extractor.PyMuPDFExtractor` (hoặc PDFMiner) | `PyMuPDF` nhanh + giữ vị trí                          |
| 3. Gemini LLM    | `infrastructure.llm_client.GeminiLLM`                           | `google-generativeai` (Gemini 1.5)                    |
| 4. Validate JSON | `services.validator.JSONValidator`                              | `pydantic` schema, `jsonschema`                       |
| 5. DataFrame     | `services.data_loader.load_data`                                | `pandas` 2.x, `polars` nếu to                         |
| 6. Metrics       | `services.metrics.MetricsService`                               | `pandas`, `sqlglot` (nếu SQL-like)                    |
| 7. Reports       | `services.report.ReportService`                                 | `plotly` / `matplotlib`, `WeasyPrint` (HTML→PDF)      |

---

## 6 . Ví dụ test nhanh với Pytest

```python
@pytest.fixture
def fake_pipeline(tmp_path):
    drive      = FakeDrive()
    extractor  = DummyExtractor()
    llm        = DummyLLM()
    validator  = JSONValidator(TransactionSchema)
    repo       = FileRepository(tmp_path)
    return StatementPipeline(drive, extractor, llm, validator, repo)

def test_pipeline(fake_pipeline):
    txs = fake_pipeline.run("fake_id")
    assert len(txs) == 10
    assert all(t.amount for t in txs)
```

Vì đã dùng **interface + DI**, bạn mock rất gọn.

---

## 7 . DevOps & runtime

* **pyproject.toml** với `[tool.poetry.scripts] bank-cli = "bank_statement_ai.adapters.cli:app"`.
* **pre-commit**: black, isort, ruff, mypy.
* **CI**: GitHub Actions chạy test + lint.
* **Docker**: multi-stage build (poetry install → run).
* **Config**: `.env` → `pydantic.BaseSettings` (inject vào Factory).

---

## 8 . Lưu ý performance & bảo mật

1. **Token Google**: lưu `token.json` vào Secret Manager hoặc Vault, không commit.
2. **Gemini key**: đọc từ env, hạn chế log.
3. **Batch lớn**: chạy `StatementPipeline.run_many(ids, parallel=True)` bằng `asyncio` hoặc `ray`.
4. **Data versioning**: cân nhắc DVC / lakeFS nếu muốn rollback.

---

## 9 . Lộ trình mở rộng

| Tính năng          | Cách cắm thêm                                    |
| ------------------ | ------------------------------------------------ |
| Hỗ trợ Dropbox     | `DropboxGateway(Adapter)` + cấu hình Strategy    |
| Thêm LLM OpenAI    | Sub-class `LLMExtractor` → `OpenAILLM`           |
| Dashboard realtime | Module `adapters.web` chạy FastAPI + Plotly Dash |
| Ngôn ngữ khác      | `prompts/` tách riêng, `prompt_factory(lang)`    |

---

### TL;DR

*Dùng Clean-Architecture + Strategy + Repository. Chia `domain`, `services`, `infrastructure`, `adapters`. Tạo `StatementPipeline` làm Facade, inject các gateway. Viết test giả lập dễ, swap provider nhanh, bảo trì khoẻ.*

Chúc bạn code vui – cần sample class chi tiết hay file `pyproject.toml` mẫu, cứ hỏi thêm!
