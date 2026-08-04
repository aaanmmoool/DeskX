# DeskX — Desktop Data Transformation Tool

A production-quality, offline-only Windows desktop application that helps
non-technical users safely sanitize datasets before sharing them.

## Features (Stage 1 + 2)

- **Upload** — Drag-and-drop or browse to select CSV, XLSX, JSON, or TXT files
- **Preview** — View data in a table with column types, select columns
- **Results** — Summary card with safe-copy processing pipeline
- **Dark / Light theme** — Toggle instantly from the navigation bar
- **Recent files** — Quickly re-open previously used files
- **Safe processing** — SHA-256 hashing, temp-file writes, path validation

## Quick Start

### Prerequisites

- Python 3.12+
- pip

### Install

```bash
# Clone the repository
cd DeskX

# Create a virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS/Linux

# Install in development mode
pip install -e ".[dev]"
```

### Run

```bash
python -m deskx.main
```

### Test

```bash
# Full test suite
pytest

# With coverage
pytest --cov=src/deskx --cov-report=term-missing

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/
```

## Architecture

```
Layer 1 — Core          config, exceptions, utils
Layer 2 — Processing    job, hash, validation, temp-file, report (NO PySide6)
Layer 3 — Services      background worker, progress events (QThread bridge)
Layer 4 — Adapters/GUI  file adapters, PySide6 widgets/pages/theme
```

Dependencies always point inward. The Processing Engine has zero GUI imports.

## Project Structure

```
src/deskx/
├── core/           # Shared constants, exceptions, helpers
├── processing/     # Domain logic — orchestrates safe-copy pipeline
├── adapters/       # CSV, JSON, XLSX, TXT file adapters
├── services/       # Background worker + progress events
├── gui/            # PySide6 presentation layer
│   ├── widgets/    # Drag-drop area, data table, nav bar
│   ├── pages/      # Upload, Preview, Results
│   └── theme/      # Colors, fonts, QSS generation
└── history/        # Recent-files JSON store
```

## Safety Guarantees

1. **Never overwrites** the original file
2. **SHA-256 hash** computed before and after processing
3. **Same-path rejection** — source and output paths must differ
4. **Temp-file writes** — data is written to a temp file first, then promoted
5. **Automatic cleanup** — temp files are deleted on success or failure

## License

MIT
