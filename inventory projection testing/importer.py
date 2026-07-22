from io import StringIO

import pandas as pd


def load_spruce_stock(filename):
    cleaned_lines = []
    header_found = False

    with open(filename, encoding="utf-8-sig") as f:
        for line in f:
            line = line.rstrip()

            # Wait until the table begins
            if not header_found:
                if line.startswith("Item,Description"):
                    header_found = True
                    cleaned_lines.append(line)
                continue

            # Skip repeated report headers
            if line.startswith("Branch:"):
                continue

            if line.startswith("Inventory Stock Status"):
                continue

            if line.startswith("All Keywords:"):
                continue

            if line.startswith("Item,Description"):
                continue

            if line.startswith("Page,"):
                continue

            if line == "":
                continue

            cleaned_lines.append(line)

    df = pd.read_csv(StringIO("\n".join(cleaned_lines)))

    # Remove category rows
    df = df[df["Description"].notna()]

    # Rename columns
    df = df.rename(columns={
        "Item": "sku",
        "Description": "description",
        "OnHand": "on_hand",
        "OnOrder": "on_order",
        "Avail": "available",
        "Min": "min_qty",
        "Max": "max_qty",
        "Sugg Qty": "suggested_qty",
        "U/M": "unit",
        "Last Recv": "last_received",
        "Last Cost": "last_cost",
        "WAVG Cost": "avg_cost"
    })

    numeric_columns = [
        "on_hand",
        "on_order",
        "available",
        "min_qty",
        "max_qty",
        "suggested_qty",
        "last_cost",
        "avg_cost"
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df