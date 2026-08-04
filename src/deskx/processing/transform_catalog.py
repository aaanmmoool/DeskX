"""Self-explanatory transformation metadata catalog.

Provides rich educational context for every transformation in DeskX:
* Friendly title
* One-sentence plain-English explanation
* Detailed explanation of what it does
* Example input & output values
* Multi-line ASCII visual example
* When to use it
* Potential warnings or caveats
"""

from __future__ import annotations

from dataclasses import dataclass
from deskx.processing.pipeline import TransformType


@dataclass(frozen=True)
class TransformMetadata:
    """Rich human-readable metadata for a single transformation."""

    transform_type: TransformType
    friendly_name: str
    category: str
    one_liner: str
    what_it_does: str
    example_in: str
    example_out: str
    example_visual: str
    when_to_use: str
    warning: str


TRANSFORM_CATALOG: dict[TransformType, TransformMetadata] = {
    TransformType.TRIM_WHITESPACE: TransformMetadata(
        transform_type=TransformType.TRIM_WHITESPACE,
        friendly_name="Trim Whitespace",
        category="Cleaning",
        one_liner="Removes spaces before and after text.",
        what_it_does="Scans all text cells and column headers, stripping out accidental spaces at the start or end of words.",
        example_in='"  John Doe  "',
        example_out='"John Doe"',
        example_visual=(
            "Before         ->  After\n"
            '---------------------------\n'
            '"  John Doe  " ->  "John Doe"\n'
            '"New York   "  ->  "New York"'
        ),
        when_to_use="Use whenever text data was imported from Excel or manually entered, as extra spaces cause duplicate entries and sorting bugs.",
        warning="Internal double spaces between words (e.g. 'John  Doe') are preserved.",
    ),
    TransformType.REMOVE_EMPTY_ROWS: TransformMetadata(
        transform_type=TransformType.REMOVE_EMPTY_ROWS,
        friendly_name="Remove Empty Rows",
        category="Cleaning",
        one_liner="Deletes rows that contain no data.",
        what_it_does="Removes any row where all cells are empty, blank, or missing (NaN).",
        example_in="Row 3: [blank, blank, blank]",
        example_out="Row 3 is deleted completely.",
        example_visual=(
            "Before                 ->  After\n"
            "-----------------------------------------\n"
            "1 | Alice | Sales      ->  1 | Alice | Sales\n"
            "2 |       |            ->  2 | Bob   | IT\n"
            "3 | Bob   | IT"
        ),
        when_to_use="Use when spreadsheets have trailing blank rows or formatting artifacts at the bottom.",
        warning="Only rows that are completely blank across all columns are deleted.",
    ),
    TransformType.REMOVE_EMPTY_COLUMNS: TransformMetadata(
        transform_type=TransformType.REMOVE_EMPTY_COLUMNS,
        friendly_name="Remove Empty Columns",
        category="Cleaning",
        one_liner="Deletes columns that contain no data.",
        what_it_does="Removes any column where every single cell is empty or missing.",
        example_in="Column 'Fax': [empty, empty, empty]",
        example_out="Column 'Fax' is deleted.",
        example_visual=(
            "Before                               ->  After\n"
            "----------------------------------------------------------\n"
            "Name  | Fax     | Email              ->  Name  | Email\n"
            "Alice | [empty] | alice@example.com  ->  Alice | alice@example.com\n"
            "Bob   | [empty] | bob@example.com    ->  Bob   | bob@example.com"
        ),
        when_to_use="Use to clean up exported database reports that include unused or obsolete columns.",
        warning="If a column has even one cell with data, it will not be deleted.",
    ),
    TransformType.REMOVE_DUPLICATES: TransformMetadata(
        transform_type=TransformType.REMOVE_DUPLICATES,
        friendly_name="Remove Duplicate Rows",
        category="Cleaning",
        one_liner="Deletes identical duplicate records.",
        what_it_does="Scans selected columns (or all columns) for identical duplicate rows and keeps only one copy.",
        example_in="John, John, Alice",
        example_out="John, Alice",
        example_visual=(
            "Before                  ->  After\n"
            "---------------------------------------------\n"
            "John  | john@company.com ->  John  | john@company.com\n"
            "John  | john@company.com ->  Alice | alice@company.com\n"
            "Alice | alice@company.com"
        ),
        when_to_use="Use to remove duplicate customer records or redundant transactions.",
        warning="Ensure you select which columns define a duplicate (e.g. Email or Customer ID).",
    ),
    TransformType.REMOVE_COLUMNS: TransformMetadata(
        transform_type=TransformType.REMOVE_COLUMNS,
        friendly_name="Remove Specified Columns",
        category="Columns",
        one_liner="Deletes columns you do not want in the output.",
        what_it_does="Permanently removes the chosen columns from the exported dataset.",
        example_in="Columns: [Name, SSN, Salary]",
        example_out="Columns: [Name] (SSN & Salary removed)",
        example_visual=(
            "Before                        ->  After\n"
            "---------------------------------------------\n"
            "Name  | Internal_ID | Email    ->  Name  | Email\n"
            "Alice | ID-9982     | alice... ->  Alice | alice..."
        ),
        when_to_use="Use to strip internal metadata, notes, or confidential columns before sharing files externally.",
        warning="Removed columns cannot be recovered in the output file.",
    ),
    TransformType.RENAME_COLUMNS: TransformMetadata(
        transform_type=TransformType.RENAME_COLUMNS,
        friendly_name="Rename Columns",
        category="Columns",
        one_liner="Changes the titles of your columns.",
        what_it_does="Renames column headers to clear, standardized names based on your mapping.",
        example_in="Column 'cust_nm'",
        example_out="Column 'Customer Name'",
        example_visual=(
            "Before                 ->  After\n"
            "---------------------------------------------\n"
            "cust_nm | eml_addr     ->  Customer Name | Email Address\n"
            "Alice   | a@test.com   ->  Alice         | a@test.com"
        ),
        when_to_use="Use when raw database exports have cryptic abbreviations or underscores in column headers.",
        warning="Renaming a column that does not exist will be ignored safely.",
    ),
    TransformType.REORDER_COLUMNS: TransformMetadata(
        transform_type=TransformType.REORDER_COLUMNS,
        friendly_name="Reorder Columns",
        category="Columns",
        one_liner="Arranges columns in a logical left-to-right order.",
        what_it_does="Moves your most important columns to the front of the spreadsheet.",
        example_in="[Email, Name, Customer ID]",
        example_out="[Customer ID, Name, Email]",
        example_visual=(
            "Before                     ->  After\n"
            "----------------------------------------------------\n"
            "Email    | Name  | ID      ->  ID  | Name  | Email\n"
            "a@co.com | Alice | C-101   ->  C-101 | Alice | a@co.com"
        ),
        when_to_use="Use to organize spreadsheets so primary identifiers and names appear first.",
        warning="Any unlisted columns will be placed automatically at the end.",
    ),
    TransformType.FILL_MISSING: TransformMetadata(
        transform_type=TransformType.FILL_MISSING,
        friendly_name="Fill Missing Values",
        category="Missing Values",
        one_liner="Replaces blank cells with a fallback value or average.",
        what_it_does="Fills empty cells in selected columns using a fixed value, average (mean/median), or drops rows with missing data.",
        example_in="Salary: [50000, blank, 60000]",
        example_out="Salary: [50000, 55000, 60000] (using average)",
        example_visual=(
            "Before                  ->  After (Fill with 'Unknown')\n"
            "-------------------------------------------------------\n"
            "Alice | Sales           ->  Alice | Sales\n"
            "Bob   | [blank]         ->  Bob   | Unknown"
        ),
        when_to_use="Use to prevent formulas from breaking on blank cells or to substitute default labels.",
        warning="Using the 'drop' strategy will permanently delete rows containing blank cells.",
    ),
    TransformType.NORMALIZE_DATES: TransformMetadata(
        transform_type=TransformType.NORMALIZE_DATES,
        friendly_name="Normalize Date Formats",
        category="Type Normalization",
        one_liner="Converts mixed dates into standard YYYY-MM-DD format.",
        what_it_does="Parses dates written as MM/DD/YYYY, DD-Mon-YYYY, or text, and converts them into a uniform ISO date format.",
        example_in="03/25/2026 or 25-Mar-2026",
        example_out="2026-03-25",
        example_visual=(
            "Before            ->  After\n"
            "---------------------------------\n"
            "03/25/2026        ->  2026-03-25\n"
            "25-Mar-2026       ->  2026-03-25\n"
            "2026.03.25        ->  2026-03-25"
        ),
        when_to_use="Use whenever datasets come from different regional systems or Excel users with mixed date formats.",
        warning="Unparseable text dates will be left blank (NaN).",
    ),
    TransformType.NORMALIZE_NUMBERS: TransformMetadata(
        transform_type=TransformType.NORMALIZE_NUMBERS,
        friendly_name="Normalize Number Formats",
        category="Type Normalization",
        one_liner="Strips currency symbols and commas so numbers can be calculated.",
        what_it_does="Removes $, €, commas, and converts accounting parentheses (100) into negative numbers -100.",
        example_in='"$1,250.00" or "(500)"',
        example_out="1250.0 or -500.0",
        example_visual=(
            "Before         ->  After\n"
            "---------------------------\n"
            '"$1,250.00"    ->  1250.0\n'
            '"(500.00)"     ->  -500.0\n'
            '"€ 89,50"      ->  89.5'
        ),
        when_to_use="Use on financial imports before performing sum or average calculations.",
        warning="Converts text numbers into standard floating-point numbers.",
    ),
    TransformType.NORMALIZE_BOOLEANS: TransformMetadata(
        transform_type=TransformType.NORMALIZE_BOOLEANS,
        friendly_name="Normalize Yes/No Values",
        category="Type Normalization",
        one_liner="Converts yes/no, active/inactive, or 1/0 into True/False.",
        what_it_does="Standardizes different words representing yes/no into consistent True/False boolean values.",
        example_in='"Yes", "Y", "1", "Active"',
        example_out="True",
        example_visual=(
            "Before         ->  After\n"
            "---------------------------\n"
            '"Yes" / "Y"    ->  True\n'
            '"No"  / "0"    ->  False\n'
            '"Active"       ->  True'
        ),
        when_to_use="Use to clean up survey responses or status flags.",
        warning="Unrecognized words will be converted to False.",
    ),
    TransformType.FILTER_ROWS: TransformMetadata(
        transform_type=TransformType.FILTER_ROWS,
        friendly_name="Filter Rows by Condition",
        category="Filtering",
        one_liner="Keeps only rows that match your filter rules.",
        what_it_does="Filters the spreadsheet to keep or exclude rows based on comparisons (e.g. Status equals Active, or Salary greater than 50000).",
        example_in="Status: [Active, Inactive, Active]",
        example_out="Keeps only 'Active' rows.",
        example_visual=(
            "Before                         ->  After (Filter: Department == 'Sales')\n"
            "------------------------------------------------------------------------\n"
            "Alice | Sales      | $60,000   ->  Alice | Sales | $60,000\n"
            "Bob   | Engineering| $80,000   ->  Carol | Sales | $55,000\n"
            "Carol | Sales      | $55,000"
        ),
        when_to_use="Use to extract specific subsets of data (e.g. only US customers or only transactions from this year).",
        warning="Rows that do not match the condition will be excluded from the exported file.",
    ),
    TransformType.REPLACE_VALUES: TransformMetadata(
        transform_type=TransformType.REPLACE_VALUES,
        friendly_name="Find and Replace Text",
        category="Filtering",
        one_liner="Replaces specific words or codes in a column.",
        what_it_does="Finds matching words or text patterns in a column and substitutes them with your new text.",
        example_in='"NY" or "N.Y."',
        example_out='"New York"',
        example_visual=(
            "Before         ->  After (Replace 'NY' with 'New York')\n"
            "-------------------------------------------------------\n"
            "Alice | NY     ->  Alice | New York\n"
            "Bob   | CA     ->  Bob   | CA"
        ),
        when_to_use="Use to correct typos or standardize state abbreviations and department names.",
        warning="Exact matching is case-sensitive by default.",
    ),
    TransformType.MASK_COLUMN: TransformMetadata(
        transform_type=TransformType.MASK_COLUMN,
        friendly_name="Mask Email & Text",
        category="Privacy",
        one_liner="Hides part of an email or ID while keeping it recognizable.",
        what_it_does="Replaces characters with asterisks (*) while keeping the first letter and domain visible for verification.",
        example_in="john.doe@company.com",
        example_out="j***@company.com",
        example_visual=(
            "Before                 ->  After\n"
            "---------------------------------------------\n"
            "john.doe@company.com   ->  j***@company.com\n"
            "4532-8819-2201-9981    ->  ***********9981\n"
            "555-019-2831           ->  *******2831"
        ),
        when_to_use="Use when sharing customer lists where teams need to verify email domains or last-4 digits without seeing the full PII.",
        warning="Masked values cannot be unmasked; save to a separate output file.",
    ),
    TransformType.REDACT_COLUMN: TransformMetadata(
        transform_type=TransformType.REDACT_COLUMN,
        friendly_name="Redact Confidential Data",
        category="Privacy",
        one_liner="Replaces sensitive cells completely with [REDACTED].",
        what_it_does="Overwrites the entire contents of selected columns with a uniform replacement tag such as [REDACTED] or CONFIDENTIAL.",
        example_in="SSN: 123-45-6789",
        example_out="[REDACTED]",
        example_visual=(
            "Before               ->  After\n"
            "----------------------------------------\n"
            "SSN: 123-45-6789     ->  [REDACTED]\n"
            "Notes: Heart patient ->  [REDACTED]"
        ),
        when_to_use="Use to completely sanitize social security numbers, medical notes, or passwords before distribution.",
        warning="100% irreversible. The original data in this column will be completely gone in the export.",
    ),
    TransformType.HASH_COLUMN: TransformMetadata(
        transform_type=TransformType.HASH_COLUMN,
        friendly_name="Hash Identifiers",
        category="Privacy",
        one_liner="Replaces IDs with irreversible encrypted SHA-256 codes.",
        what_it_does="Converts names or IDs into a unique 64-character cryptographic hash. Identical inputs always produce the same hash, allowing data matching across files without revealing the identity.",
        example_in="CUST-1023",
        example_out="4af83d9ab7...",
        example_visual=(
            "Before      ->  After (SHA-256 Hash)\n"
            "--------------------------------------------------\n"
            "CUST-1023   ->  4af83d9ab7c12...8e90a\n"
            "CUST-1023   ->  4af83d9ab7c12...8e90a (identical)"
        ),
        when_to_use="Use for analytics or database joins where you need to track unique users without knowing who they are.",
        warning="Hashing cannot be reversed. Anyone with the same hashing algorithm and input could compare known values.",
    ),
    TransformType.PSEUDONYMIZE_COLUMN: TransformMetadata(
        transform_type=TransformType.PSEUDONYMIZE_COLUMN,
        friendly_name="Pseudonymize (Fake IDs)",
        category="Privacy",
        one_liner="Replaces names or IDs with consistent fake labels like 'Person_1'.",
        what_it_does="Maps each unique name or ID to a clean, readable placeholder (e.g. Person_1, Person_2). The same input always gets the same fake name in the file.",
        example_in="Alice Smith, Bob Jones, Alice Smith",
        example_out="Person_1, Person_2, Person_1",
        example_visual=(
            "Before        ->  After (Prefix: 'Customer_')\n"
            "---------------------------------------------\n"
            "Alice Smith   ->  Customer_1\n"
            "Bob Jones     ->  Customer_2\n"
            "Alice Smith   ->  Customer_1"
        ),
        when_to_use="Use when preparing demo data, training reports, or sharing charts where executives need readable labels instead of long hex hashes.",
        warning="The mapping table between real names and fake IDs is not saved after processing completes.",
    ),
    TransformType.GENERALIZE_COLUMN: TransformMetadata(
        transform_type=TransformType.GENERALIZE_COLUMN,
        friendly_name="Generalize Numbers & Dates",
        category="Statistical Privacy",
        one_liner="Rounds exact numbers or dates into broader ranges.",
        what_it_does="Rounds ages to the nearest decade (34 -> 30) or dates to the year/month (2026-03-25 -> 2026-03) to protect individual identity.",
        example_in="Age: 34",
        example_out="Age: 30 (rounded to decade)",
        example_visual=(
            "Before            ->  After (Round to 10)\n"
            "------------------------------------------\n"
            "Age: 34           ->  30\n"
            "Age: 38           ->  40\n"
            "Age: 42           ->  40"
        ),
        when_to_use="Use when publishing demographic or survey data where exact age or birth date could identify someone.",
        warning="Precision is reduced; individual statistical accuracy will be grouped.",
    ),
    TransformType.REVENUE_BANDS: TransformMetadata(
        transform_type=TransformType.REVENUE_BANDS,
        friendly_name="Convert to Income/Revenue Bands",
        category="Statistical Privacy",
        one_liner="Replaces exact dollar amounts with salary/revenue brackets.",
        what_it_does="Converts exact numerical values into friendly descriptive brackets such as '< $50K', '$50K - $100K', or '> $500K'.",
        example_in="$62,500",
        example_out="50K-100K",
        example_visual=(
            "Before            ->  After\n"
            "-----------------------------------\n"
            "$42,000           ->  < 50K\n"
            "$62,500           ->  50K-100K\n"
            "$185,000          ->  100K-500K"
        ),
        when_to_use="Use for HR compensation reports, customer revenue charts, or public datasets.",
        warning="Exact dollar amounts will be replaced by text bracket labels.",
    ),
    TransformType.SUPPRESS_LOW_COUNTS: TransformMetadata(
        transform_type=TransformType.SUPPRESS_LOW_COUNTS,
        friendly_name="Suppress Rare Categories",
        category="Statistical Privacy",
        one_liner="Hides rare groups that have fewer than N people.",
        what_it_does="Scans a column for categories that occur very rarely (e.g. fewer than 5 times) and groups them together into 'Other' or '[SUPPRESSED]'.",
        example_in="Department: 'Nuclear Physics' (1 person)",
        example_out="Department: 'Other'",
        example_visual=(
            "Before                           ->  After (Threshold: 3)\n"
            "----------------------------------------------------------\n"
            "Sales (45 people)                ->  Sales\n"
            "Engineering (30 people)          ->  Engineering\n"
            "Executive Aviation (1 person)    ->  Other"
        ),
        when_to_use="Use to prevent re-identification of individuals in small departments or rare medical conditions.",
        warning="Rare categories will be merged into a single 'Other' bucket.",
    ),
}


def get_transform_metadata(tt: TransformType) -> TransformMetadata:
    """Retrieve metadata for a transform type, returning a fallback if unknown."""
    if tt in TRANSFORM_CATALOG:
        return TRANSFORM_CATALOG[tt]
    return TransformMetadata(
        transform_type=tt,
        friendly_name=tt.name.replace("_", " ").title(),
        category="Other",
        one_liner="Applies data transformation.",
        what_it_does="Performs transformation on selected columns.",
        example_in="Sample input",
        example_out="Sample output",
        example_visual="Before -> After",
        when_to_use="Use when this transformation is required.",
        warning="Check settings before processing.",
    )
