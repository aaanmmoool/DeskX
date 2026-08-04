# DeskX — Testing Guide

## Automated Tests

### Setup

```bash
# Ensure dev dependencies are installed
pip install -e ".[dev]"
```

### Running Tests

```bash
# Full suite
pytest

# With coverage report
pytest --cov=src/deskx --cov-report=term-missing

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Specific test file
pytest tests/unit/test_hash_service.py -v
```

---

## Manual Testing Checklist

### Stage 1 — GUI

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 1 | App launches | Run `python -m deskx.main` | Window appears, dark theme, nav bar visible |
| 2 | Dark mode rendering | Observe all elements | Dark backgrounds, light text, no broken colours |
| 3 | Light mode toggle | Click "🌙 Dark Mode" in nav | Theme switches instantly, button text updates |
| 4 | Dark mode toggle back | Click "☀️ Light Mode" | Returns to dark theme |
| 5 | Navigate to Upload | Click "Upload" in nav | Upload page shown with drag-drop area |
| 6 | Navigate to Preview | Click "Preview" in nav | Preview page shown |
| 7 | Navigate to Results | Click "Results" in nav | Results page shown |
| 8 | Drag CSV file | Drag a .csv onto the drop zone | Border glows, icon changes, file loads in preview |
| 9 | Drag XLSX file | Drag a .xlsx | Same behaviour as CSV |
| 10 | Drag JSON file | Drag a .json | Same behaviour |
| 11 | Drag TXT file | Drag a .txt (tab-separated) | Same behaviour |
| 12 | Drag unsupported file | Drag a .pdf | Drop zone does not accept, no crash |
| 13 | Browse button | Click "Browse Files" | File dialog opens with correct filters |
| 14 | Select file via browse | Choose a CSV from the dialog | File loads, auto-navigates to Preview |
| 15 | Output folder picker | Click "Choose…" on Upload page | Folder dialog opens, path displays |
| 16 | Recent files | Open a file, check "Recent Files" section | File appears in the list |
| 17 | Recent files — reopen | Double-click a recent entry | File reloads |
| 18 | Preview table | Load a file, check Preview page | Table shows data with headers and types |
| 19 | Column checkboxes | Toggle individual column checkboxes | "Select All" updates accordingly |
| 20 | Select All | Toggle "Select All" checkbox | All columns toggle together |
| 21 | Resize window | Drag window edges | Layout adjusts, no overlap or clipping |
| 22 | Minimum size | Resize to minimum | Window enforces minimum size |

### Stage 2 — Processing

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 23 | Process button | Load file → go to Results → click "Process" | Progress bar fills, report appears |
| 24 | Output file created | Check output folder after processing | `*_sanitized.*` file exists |
| 25 | Output matches input | Compare source and output bytes | Byte-identical (safe copy) |
| 26 | Source unchanged | Check source file hash before/after | Hash matches — source untouched |
| 27 | Same-path rejection | Set output folder = source folder with same name | Error or warning shown |
| 28 | Cancel button | Click "Cancel" during processing | Progress stops, "cancelled" status shown |
| 29 | Process CSV | Process a CSV file | Output is valid CSV |
| 30 | Process JSON | Process a JSON file | Output is valid JSON |
| 31 | Process XLSX | Process an XLSX file | Output is valid XLSX |
| 32 | Process TXT | Process a TXT file | Output is valid TXT |

---

## Edge-Case Checklist

| # | Case | Expected Behaviour |
|---|------|-------------------|
| 1 | Empty CSV (headers only) | Preview shows headers, no rows. Processing succeeds. |
| 2 | CSV with 1 million rows | Preview loads first 200 rows. Processing copies full file. |
| 3 | File with Unicode characters | Preview displays correctly. Output preserves encoding. |
| 4 | File with special characters in name | Output filename sanitized correctly. |
| 5 | Read-only output directory | Validation error before processing starts. |
| 6 | File deleted after selection | Error message on Preview page. |
| 7 | Very long file path (>260 chars) | Windows long-path support or graceful error. |
| 8 | File with mixed line endings | Content preserved as-is in safe copy. |
| 9 | JSON with nested objects | Pandas flattens or shows object columns. |
| 10 | XLSX with multiple sheets | First sheet is loaded by default. |
| 11 | TXT with non-tab delimiter | Adapter uses configurable delimiter. |
| 12 | Corrupt recent-files JSON | Manager resets gracefully, no crash. |
| 13 | Rapid theme toggling | No UI glitches or crashes. |
| 14 | Multiple rapid file opens | Last file wins, no race condition. |
