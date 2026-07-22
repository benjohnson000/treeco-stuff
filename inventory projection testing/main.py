import pandas as pd

from database import engine
from importer import load_spruce_stock


def main():

    stock = load_spruce_stock("data/stock.csv")

    stock.to_sql(
        "inventory",
        engine,
        if_exists="replace",
        index=False
    )

    print(f"Imported {len(stock)} inventory items.")

    inventory = pd.read_sql(
        "SELECT * FROM inventory",
        engine
    )

    print(
        inventory[
            [
                "sku",
                "description",
                "on_hand",
                "on_order",
                "available"
            ]
        ]
    )


if __name__ == "__main__":
    main()