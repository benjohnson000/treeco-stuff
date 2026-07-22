import csv
import re
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


def load_spruce_usage(filename):
    """Load a Spruce Inventory Usage export into one row per SKU and month."""
    month_columns = None
    usage_rows = []

    with open(filename, encoding="utf-8-sig", newline="") as file:
        for row in csv.reader(file):
            if not row:
                continue

            first_value = row[0].strip()

            if first_value == "Item" and len(row) > 1 and row[1].strip() == "QOH":
                month_columns = [
                    value.strip()
                    for value in row[2:]
                    if _is_month_column(value)
                ]
                continue

            if not month_columns or _is_usage_report_row(first_value):
                continue

            # Category rows contain only a category name, not item usage values.
            expected_columns = 2 + 1 + len(month_columns) + 1
            if len(row) < expected_columns:
                continue

            sku = first_value
            monthly_values = row[3:3 + len(month_columns)]

            for month_label, quantity in zip(month_columns, monthly_values):
                year, month = _parse_month(month_label)
                usage_rows.append({
                    "sku": sku,
                    "year": year,
                    "month": month,
                    "quantity_used": pd.to_numeric(quantity, errors="coerce")
                })

    usage = pd.DataFrame(
        usage_rows,
        columns=["sku", "year", "month", "quantity_used"]
    )

    if usage.empty:
        return usage

    usage["sku"] = usage["sku"].str.strip()
    usage["quantity_used"] = usage["quantity_used"].fillna(0)
    return usage


def _is_month_column(value):
    return bool(re.fullmatch(r"\d{1,2}/\d{2,4}", value.strip()))


def _parse_month(value):
    month_text, year_text = value.strip().split("/")
    year = int(year_text)
    if year < 100:
        year += 2000
    return year, int(month_text)


def _is_usage_report_row(first_value):
    return first_value.startswith((
        "Branch:",
        "Inventory Usage",
        "KeyWord:",
        "Description",
        "Page,"
    ))
