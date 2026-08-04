# ✦ DeskX Data Sanitizer — Official User Guide

Welcome to **DeskX Data Sanitizer**! This guide is written for business users, analysts, and data handlers who need to inspect, clean, and anonymize Excel and CSV files **100% locally and offline** without requiring technical expertise or coding.

---

## 📖 Table of Contents

1. [What is DeskX?](#1-what-is-deskx)
2. [Getting Started & First Run](#2-getting-started--first-run)
3. [The Two-Screen Workflow](#3-the-two-screen-workflow)
   - [Screen 1: The Upload Screen](#screen-1-the-upload-screen)
   - [Screen 2: Configure & Preview Screen](#screen-2-configure--preview-screen)
4. [Protecting Sensitive PII (Automatic Detection)](#4-protecting-sensitive-pii-automatic-detection)
5. [Transformation Catalog (All Available Rules)](#5-transformation-catalog-all-available-rules)
   - [Data Cleaning](#a-data-cleaning)
   - [Privacy & Security](#b-privacy--security)
   - [Formatting & Custom Rules](#c-formatting--custom-rules)
6. [Exporting Data & Audit Reports](#6-exporting-data--audit-reports)
7. [Keyboard Shortcuts](#7-keyboard-shortcuts)
8. [Troubleshooting & FAQ](#8-troubleshooting--faq)

---

## 1. What is DeskX?

DeskX is a desktop data sanitization application built to help you transform messy spreadsheets into clean, compliant datasets.

### Key Benefits:
- **100% Offline & Private:** Your spreadsheets are processed entirely on your computer. Nothing is ever uploaded to the cloud or shared over the internet.
- **No Formulas Required:** Apply complex cleaning rules (like regex masking, deduplication, or date normalization) with a single click.
- **Compliance Audit Trails:** Every time you export a dataset, DeskX generates a compliance audit report (`.report.json`) documenting exactly what rules were applied.

---

## 2. Getting Started & First Run

When you open DeskX for the first time, you will see the **Welcome & Onboarding Dialog**.
- **Try Sample Data:** Click the **"🎁 Try Sample Dataset"** button to load a built-in employee dataset (`sample_employees.csv`) complete with sample PII, trailing whitespace, duplicates, and missing values so you can practice using DeskX immediately.
- **Get Started:** Click **"Get Started →"** to enter your workspace.

> [!TIP]
> You can open the built-in interactive Help Modal at any time by pressing **F1** or clicking the **❓ Help** button in the top toolbar.

---

## 3. The Two-Screen Workflow

DeskX uses an intuitive **Two-Screen Workflow**:

```
┌────────────────────────────────┐       ┌────────────────────────────────┐
│   SCREEN 1: UPLOAD             │       │   SCREEN 2: CONFIGURE          │
│                                │  ───► │                                │
│   • Drag & Drop File           │       │   • Live Table Preview         │
│   • Browse Files               │       │   • Add/Edit Transformations   │
│   • Recent Files List          │       │   • PII Sensitive Toolbar      │
└────────────────────────────────┘       └────────────────────────────────┘
                                                         │
                                                         ▼
                                         ┌────────────────────────────────┐
                                         │   EXPORT & REPORT              │
                                         │                                │
                                         │   • Saves to same directory    │
                                         │   • Generates audit JSON       │
                                         └────────────────────────────────┘
```

### Screen 1: The Upload Screen
- **Drag and Drop:** Drag any Excel (`.xlsx`), CSV (`.csv`), or Text (`.txt`) file from your computer directly into the dashed drop zone.
- **Browse Files:** Click **"📁 Browse Files"** to open a standard file chooser.
- **Try Sample Data:** Click **"🎁 Try Sample Data"** to practice with a bundled sample file.
- **Recent Files:** Your recently opened files are listed automatically for one-click reloading.

### Screen 2: Configure & Preview Screen
Once a file is loaded, you are taken to the **Configure & Preview Screen**:
- **Left Panel (Live Table Preview):**
  - View your data in real-time.
  - **Header Statistics:** Column headers show data type badges (`ABC` for Text, `123` for Numeric, `📅` for Date) and missing value counts (e.g., `⚠️ 2 missing`).
  - **Search & Filter:** Use the top search bar to instantly search across all cells in the sample preview.
  - **Pagination:** Easily page through large sample previews using `< Previous` and `Next >`.
- **Right Panel (Transformations Sidebar):**
  - **Column Toggles:** Check or uncheck column names to include or drop them from your export.
  - **Transformation Cards:** Every rule you add appears as a clear card showing the rule name, target column, and parameters. Click the **Edit (`✏`)** button on any card to update it or preview its live effect.
  - **+ Add Transformation:** Click to open the **Transformation Configuration Modal**.

---

## 4. Protecting Sensitive PII (Automatic Detection)

DeskX automatically scans column names and cell contents for **Personally Identifiable Information (PII)**.

When sensitive columns are found (such as Email Addresses, Employee Names, Social Security Numbers, or Credit Card Numbers), a yellow **Sensitive Column Protection Toolbar** appears in the sidebar:
1. Select the sensitive column from the dropdown.
2. Choose a protective action:
   - **Mask:** Hides all characters except the last 4 (e.g., `*******6789`).
   - **Redact:** Replaces the entire cell with `[REDACTED]`.
   - **Hash:** Generates a secure SHA-256 fingerprint (useful for matching without revealing identity).
   - **Pseudonymize:** Consistently replaces real names or IDs with realistic fictional aliases.
3. Click **"Apply"** to protect the column instantly.

---

## 5. Transformation Catalog (All Available Rules)

DeskX provides 20+ built-in data sanitization rules organized into three categories:

### A. Data Cleaning
| Transformation | What It Does | Example Use Case |
| :--- | :--- | :--- |
| **Trim Whitespace** | Removes leading and trailing spaces from text cells and column headers. | `"  Alice Smith  "` → `"Alice Smith"` |
| **Remove Empty Rows** | Drops rows that are entirely empty or blank. | Removing accidental blank rows from Excel exports. |
| **Remove Empty Columns** | Drops columns that contain no data across any row. | Cleaning up unused spreadsheet columns. |
| **Remove Duplicates** | Identifies duplicate rows and keeps only the first or last occurrence. | Deduplicating customer lists or employee directories. |
| **Fill Missing Values** | Replaces empty cells with a custom text value, or statistical mean/median for numbers. | Filling missing department names with `"Unassigned"`. |

### B. Privacy & Security
| Transformation | What It Does | Example Use Case |
| :--- | :--- | :--- |
| **Mask Column** | Replaces characters with asterisks while preserving the last 4 characters. | Protecting Social Security Numbers or Credit Cards. |
| **Redact Column** | Completely overwrites the cell content with `[REDACTED]`. | Removing confidential notes or internal comments. |
| **Hash Column** | Converts text into a deterministic 64-character SHA-256 fingerprint. | Creating anonymous unique user identifiers. |
| **Pseudonymize Column** | Consistently maps unique names or IDs to realistic fictional aliases. | Anonymizing medical or HR records for reporting. |

### C. Formatting & Custom Rules
| Transformation | What It Does | Example Use Case |
| :--- | :--- | :--- |
| **Rename Columns** | Mappings to change existing header names to new names. | Renaming `"Emp_ID_Final"` to `"Employee ID"`. |
| **Reorder Columns** | Moves priority columns to the beginning of the dataset. | Placing `"ID"`, `"Name"`, and `"Department"` first. |
| **Normalize Dates** | Converts mixed date formats (`MM/DD/YYYY`, `YYYY-MM-DD`) into a standard ISO format. | `"05/14/2020"` → `"2020-05-14"` |
| **Normalize Numbers** | Strips currency symbols (`$`, `€`), commas, and accounting brackets. | `"$120,000.00"` → `120000.0` |
| **Revenue Bands** | Converts continuous dollar amounts into discrete categories (`Low`, `Medium`, `High`, `Enterprise`). | Categorizing customer contracts by deal size. |
| **Suppress Low Counts** | Replaces rare categories occurring fewer than *N* times with `"Other"`. | Protecting privacy in small departmental subsets. |

---

## 6. Exporting Data & Audit Reports

When your transformations are ready:
1. Click **"Process & Export"** at the bottom of the right-hand panel.
2. DeskX processes the entire dataset offline and saves the result in the **same directory** as your original file with a `_sanitized` suffix (e.g., `sales_data_sanitized.xlsx`).
3. An accompanying compliance audit report is generated automatically (e.g., `sales_data_sanitized.report.json`), listing:
   - Total rows and columns processed.
   - Execution duration.
   - A complete audit trail of every transformation applied.

---

## 7. Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| **Ctrl + O** | Open file chooser to upload a new dataset. |
| **Ctrl + E** / **Ctrl + S** | Process and export the sanitized dataset. |
| **F1** | Open the interactive User Guide & Quick Start dialog. |
| **Escape** | Close active dialog modal or return to the previous screen. |

---

## 8. Troubleshooting & FAQ

### Q: Where is my processed file saved?
**A:** Your file is saved automatically in the exact same folder as your original input file. For example, if you opened `C:\Users\Name\Documents\data.xlsx`, your output will be `C:\Users\Name\Documents\data_sanitized.xlsx`.

### Q: Does DeskX modify my original file?
**A:** No. DeskX **never** overwrites your original file. All transformations are written to a brand new file with the `_sanitized` suffix.

### Q: Can I process large Excel files with thousands of rows?
**A:** Yes! The live preview table displays up to 100 sample rows so you can configure rules quickly without lag. When you click **"Process & Export"**, DeskX applies your rules across all rows in the dataset.

### Q: What should I do if a column is marked "⚠️ Missing"?
**A:** Check the table header badge to see how many missing values were detected. You can use **"Fill Missing Values"** from the Transformation Catalog to fill empty cells with a default value or drop incomplete rows.
