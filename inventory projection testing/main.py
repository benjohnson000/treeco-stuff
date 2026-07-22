import pandas as pd

from config import load_settings
from database import engine, upsert_usage_history
from importer import load_spruce_stock, load_spruce_usage
from metrics import build_inventory_projection


def main():
    settings = load_settings()

    stock = load_spruce_stock("data/stock.csv")
    stock.to_sql(
        "inventory",
        engine,
        if_exists="replace",
        index=False
    )
    print(f"Imported {len(stock)} inventory items.")

    usage = load_spruce_usage("data/usage.csv")
    matched_usage_rows, unmatched_usage_rows = upsert_usage_history(usage)
    print(
        f"Imported {matched_usage_rows} monthly usage records "
        f"({unmatched_usage_rows} records had no matching inventory SKU)."
    )

    inventory = pd.read_sql(
        "SELECT sku, description, on_hand, on_order, available FROM inventory",
        engine
    )

    usage_history = pd.read_sql(
        "SELECT sku, year, month, quantity_used FROM usage_history "
        "ORDER BY sku, year, month",
        engine
    )

    projection = build_inventory_projection(inventory, usage_history, settings)
    print("\nInventory projection")
    print(
        "Order coverage target: "
        f"{settings['stock_target_days']} stock days + "
        f"{settings['vendor_lead_time_days']} lead-time days + "
        f"{settings['buffer_days']} buffer days"
    )
    print(projection.to_string(index=False, na_rep="--"))


if __name__ == "__main__":
    main()
