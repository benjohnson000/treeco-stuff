import pandas as pd

from config import load_settings
from database import engine, replace_imported_data
from importer import load_spruce_stock, load_spruce_usage
from metrics import build_inventory_projection


def main():
    settings = load_settings()
    inventory = load_spruce_stock("data/stock.csv")
    usage = load_spruce_usage("data/usage.csv")
    replace_imported_data(inventory, usage)

    print(f"Imported {len(inventory)} SKU/branch inventory records.")
    print(f"Imported {len(usage)} SKU/branch usage records.")

    inventory = pd.read_sql("SELECT * FROM inventory", engine)
    usage = pd.read_sql("SELECT * FROM usage_history", engine)
    projection = build_inventory_projection(inventory, usage, settings)
    print("\nInventory projection")
    print(projection.to_string(index=False, na_rep="--"))


if __name__ == "__main__":
    main()
