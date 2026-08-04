"""Generate realistic messy test datasets for DeskX testing."""
import pandas as pd
import numpy as np
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures"


def create_messy_csv():
    """Create a messy CSV with real-world data quality issues."""
    data = {
        "Employee ID": [
            "EMP-001", "EMP-002", "EMP-003", "EMP-004", "EMP-005",
            "EMP-006", "EMP-007", "EMP-008", "EMP-003", "EMP-009",
            "", "EMP-010", "EMP-011", np.nan, "EMP-012",
        ],
        "  First Name  ": [  # whitespace in column name
            "  Alice  ", "Bob", " Charlie ", "Diana", "Eve",
            "Frank", "  Grace", "Hank ", "Charlie", "Ivy",
            "", "Jack", " Kate ", np.nan, "Leo",
        ],
        "Last Name": [
            "Johnson", "Smith", "Williams", "Brown", "Davis",
            "Wilson", "Taylor", "Anderson", "Williams", "Thomas",
            "", "White", "Harris", np.nan, "Martin",
        ],
        "Email Address": [
            "alice.j@acmecorp.com", "bob.smith@gmail.com",
            "charlie.w@outlook.com", "diana.brown@acmecorp.com",
            "eve_davis@yahoo.com", "frank@company.co.uk",
            "grace.taylor@acmecorp.com", "hank.a@acmecorp.com",
            "charlie.w@outlook.com", "ivy.t@example.com",
            "", "jack.white@acmecorp.com", "kate.h@company.com",
            np.nan, "leo.m@acmecorp.com",
        ],
        "Phone Number": [
            "(555) 123-4567", "555.234.5678", "+1-555-345-6789",
            "5554567890", "(555) 567-8901", "+44 20 7946 0958",
            "555-678-9012", "(555)789-0123", "+1-555-345-6789",
            "555 890 1234", "", "(555) 901-2345", "555.012.3456",
            np.nan, "(555) 123-4568",
        ],
        "Date of Birth": [
            "01/15/1990", "1985-03-22", "22-07-1992", "Mar 5, 1988",
            "1995.11.30", "12/01/1991", "1993-08-14", "June 3, 1987",
            "22-07-1992", "02/28/1996", "", "1989-12-25", "07-04-1994",
            np.nan, "Jan 1, 2000",
        ],
        "Salary": [
            "$75,000.00", "€62,500", "85000", "$92,150.50", "¥8,500,000",
            "£55,000", "$110,000", "(45,000)", "85000", "$72,000",
            "", "$88,000", "  $95,000  ", np.nan, "$67,500",
        ],
        "Department": [
            "Engineering", "Marketing", "Engineering", "HR",
            "Engineering", "Sales", "Marketing", "Engineering",
            "Engineering", "HR", "", "Sales", "Engineering",
            np.nan, "Marketing",
        ],
        "Active": [
            "Yes", "true", "1", "Y", "yes", "TRUE", "active",
            "No", "1", "false", "", "on", "True", np.nan, "0",
        ],
        "ZIP Code": [
            "90210", "10001", "94105-1234", "60601", "98101",
            "SW1A 1AA", "30301", "02101", "94105-1234", "75201",
            "", "33101", "20001", np.nan, "85001",
        ],
        "Purchase Order": [
            "PO-2024-001", "PO-2024-002", "PO-2024-003", "PO-2024-004",
            "PO-2024-005", "PO-2024-006", "PO-2024-007", "PO-2024-008",
            "PO-2024-003", "PO-2024-009", "", "PO-2024-010", "PO-2024-011",
            np.nan, "PO-2024-012",
        ],
        "Notes": [
            "Top performer Q4", "New hire, probation period", "",
            "Transferred from London office", "Remote worker since 2020",
            "Part-time contractor", np.nan, "On medical leave",
            "Duplicate of row 3?", "Recently promoted", "",
            "Referred by EMP-002", "  Needs review  ",
            np.nan, "Starting Jan 2025",
        ],
    }

    df = pd.DataFrame(data)
    # Add a completely empty row
    empty_row = pd.DataFrame(
        {col: [np.nan] for col in df.columns}
    )
    df = pd.concat([df.iloc[:7], empty_row, df.iloc[7:]], ignore_index=True)
    return df


def create_header_on_row3_csv():
    """Create a CSV where headers are on row 3 (rows 0-1 are metadata)."""
    lines = [
        "Company Report - ACME Corp,,,,",
        "Generated: 2024-01-15,,,,",
        "ID,Name,Email,Department,Revenue",
        "1,Alice Johnson,alice@acme.com,Engineering,$125000",
        "2,Bob Smith,bob@acme.com,Marketing,$98000",
        "3,Charlie Brown,charlie@acme.com,Sales,$145000",
        "4,Diana Prince,diana@acme.com,HR,$87000",
        "5,Eve Davis,eve@acme.com,Engineering,$132000",
    ]
    return "\n".join(lines)


def create_multi_sheet_xlsx():
    """Create an XLSX with multiple worksheets."""
    employees = pd.DataFrame({
        "emp_id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "department": ["Eng", "Mkt", "Eng", "HR", "Sales"],
        "salary": [75000, 62000, 85000, 55000, 92000],
    })

    departments = pd.DataFrame({
        "dept_code": ["Eng", "Mkt", "HR", "Sales"],
        "dept_name": ["Engineering", "Marketing", "Human Resources", "Sales"],
        "headcount": [15, 8, 5, 12],
    })

    revenue = pd.DataFrame({
        "quarter": ["Q1-2024", "Q2-2024", "Q3-2024", "Q4-2024"],
        "revenue": [1250000, 1380000, 1420000, 1560000],
        "expenses": [980000, 1020000, 1050000, 1100000],
    })

    return {"Employees": employees, "Departments": departments, "Revenue": revenue}


def create_pipe_delimited_txt():
    """Create a pipe-delimited text file."""
    lines = [
        "customer_id|first_name|last_name|email|phone|city",
        "C001|Alice|Johnson|alice@example.com|(555) 111-2222|New York",
        "C002|Bob|Smith|bob@example.com|(555) 333-4444|Chicago",
        "C003|Charlie|Williams|charlie@example.com|(555) 555-6666|Los Angeles",
        "C004|Diana|Brown|diana@example.com|(555) 777-8888|Houston",
        "C005|Eve|Davis|eve@example.com|(555) 999-0000|Phoenix",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    # Messy CSV
    messy_df = create_messy_csv()
    messy_df.to_csv(FIXTURES_DIR / "messy_data.csv", index=False)
    print(f"Created messy_data.csv ({len(messy_df)} rows)")

    # Header on row 3
    header_csv = create_header_on_row3_csv()
    (FIXTURES_DIR / "header_on_row3.csv").write_text(header_csv, encoding="utf-8")
    print("Created header_on_row3.csv")

    # Multi-sheet XLSX
    sheets = create_multi_sheet_xlsx()
    with pd.ExcelWriter(
        FIXTURES_DIR / "multi_sheet.xlsx", engine="openpyxl"
    ) as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)
    print("Created multi_sheet.xlsx")

    # Pipe-delimited TXT
    pipe_txt = create_pipe_delimited_txt()
    (FIXTURES_DIR / "pipe_delimited.txt").write_text(pipe_txt, encoding="utf-8")
    print("Created pipe_delimited.txt")

    print("\nDone! All test fixtures created.")
