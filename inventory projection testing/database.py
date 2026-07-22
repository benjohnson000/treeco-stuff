from sqlalchemy import create_engine


DATABASE_NAME = "inventory.db"
engine = create_engine(f"sqlite:///{DATABASE_NAME}")


def replace_imported_data(inventory, usage):
    """Replace the current multi-branch report snapshot in SQLite."""
    inventory.to_sql("inventory", engine, if_exists="replace", index=False)
    usage.to_sql("usage_history", engine, if_exists="replace", index=False)
