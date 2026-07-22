import csv

import pandas as pd

from branches import load_branches
from vendors import find_vendor, load_vendors


STOCK_COLUMNS = [
    "sku", "description", "branch_id", "branch_name", "on_hand", "on_order",
    "available", "min_qty", "max_qty", "suggested_qty", "unit", "last_received",
    "last_cost", "avg_cost", "vendor",
]
USAGE_COLUMNS = ["sku", "branch_id", "last_3_month_sales"]


def load_spruce_stock(filename, vendors_filename=None, branches_filename=None):
    """Load a combined Spruce Stock Status report into one SKU/branch row."""
    branches = load_branches(branches_filename) if branches_filename else load_branches()
    vendors = load_vendors(vendors_filename) if vendors_filename else load_vendors()
    records = []
    current_item = None

    for row in _csv_rows(filename):
        if _is_stock_report_row(row):
            continue

        if _is_item_row(row):
            current_item = {"sku": row[0].strip(), "description": row[1].strip()}
            continue

        if not current_item or not _is_branch_stock_row(row, branches):
            continue

        records.append({
            "sku": current_item["sku"],
            "description": current_item["description"],
            "branch_id": row[0].strip(),
            "branch_name": branches[row[0].strip()],
            "on_hand": _number(row[1]),
            "on_order": _number(row[2]),
            "available": _number(row[3]),
            "min_qty": _number(row[4]),
            "max_qty": _number(row[5]),
            "suggested_qty": _number(row[6]),
            "unit": row[7].strip(),
            "last_received": row[8].strip(),
            "last_cost": _number(row[9]),
            "avg_cost": _number(row[10]),
            "vendor": find_vendor(current_item["description"], vendors),
        })

    inventory = pd.DataFrame(records, columns=STOCK_COLUMNS)
    if inventory.empty:
        return inventory

    return inventory.loc[
        ~inventory["description"].str.strip().str.startswith("##")
    ].reset_index(drop=True)


def load_spruce_usage(filename, branches_filename=None):
    """Load the combined Spruce Usage report's rolling three-month sales."""
    branches = load_branches(branches_filename) if branches_filename else load_branches()
    records = []
    current_sku = None

    for row in _csv_rows(filename):
        if _is_usage_report_row(row):
            continue

        if _is_item_row(row):
            current_sku = row[0].strip()
            continue

        if not current_sku or not _is_branch_usage_row(row, branches):
            continue

        records.append({
            "sku": current_sku,
            "branch_id": row[0].strip(),
            "last_3_month_sales": _number(row[1]),
        })

    return pd.DataFrame(records, columns=USAGE_COLUMNS)


def _csv_rows(filename):
    with open(filename, encoding="utf-8-sig", newline="") as file:
        for row in csv.reader(file, escapechar="\\"):
            yield [value.strip() for value in row]


def _is_item_row(row):
    # Item numbers may be numeric, but branch rows have a numeric quantity in
    # their second field while item rows have a text description.
    return len(row) >= 2 and row[0] and row[1] and not _looks_numeric(row[1])


def _is_branch_stock_row(row, branches):
    return len(row) >= 11 and row[0] in branches


def _is_branch_usage_row(row, branches):
    return len(row) >= 8 and row[0] in branches


def _is_stock_report_row(row):
    if not row:
        return True
    return row[0].startswith((
        "Branch:", "Inventory Stock Status", "All Keywords:", "Any Keywords:",
        "Item", "Page,",
    ))


def _is_usage_report_row(row):
    if not row:
        return True
    return row[0].startswith((
        "Branch:", "Inventory Usage", "KeyWord:", "Description", "Item", "Page,",
    ))


def _number(value):
    return pd.to_numeric(str(value).replace(",", ""), errors="coerce")


def _looks_numeric(value):
    return not pd.isna(_number(value))
