"""Generate the sample.xlsx fixture from the sample DataFrame."""
import pandas as pd
from pathlib import Path

df = pd.DataFrame({
    "id": [1, 2, 3, 4, 5],
    "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
    "email": [
        "alice@example.com", "bob@example.com",
        "charlie@example.com", "diana@example.com",
        "eve@example.com",
    ],
    "age": [30, 25, 35, 28, 32],
    "salary": [50000.0, 60000.0, 75000.0, 55000.0, 80000.0],
})

out = Path(__file__).parent.parent / "tests" / "fixtures" / "sample.xlsx"
df.to_excel(out, index=False, engine="openpyxl")
print(f"Created {out}")
