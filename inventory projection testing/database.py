from sqlalchemy import Column, Float, Integer, MetaData, String, Table, create_engine, select
from sqlalchemy.dialects.sqlite import insert

DATABASE_NAME = "inventory.db"

engine = create_engine(f"sqlite:///{DATABASE_NAME}")

metadata = MetaData()

usage_history = Table(
    "usage_history",
    metadata,
    Column("sku", String, primary_key=True),
    Column("year", Integer, primary_key=True),
    Column("month", Integer, primary_key=True),
    Column("quantity_used", Float, nullable=False),
)


def upsert_usage_history(usage):
    """Store usage rows for inventory SKUs, updating only matching months."""
    metadata.create_all(engine, tables=[usage_history])

    with engine.begin() as connection:
        inventory_skus = set(connection.execute(
            select(Table("inventory", MetaData(), autoload_with=engine).c.sku)
        ).scalars())

        matched_usage = usage[usage["sku"].isin(inventory_skus)]
        records = matched_usage.to_dict("records")

        if records:
            statement = insert(usage_history).values(records)
            statement = statement.on_conflict_do_update(
                index_elements=["sku", "year", "month"],
                set_={"quantity_used": statement.excluded.quantity_used}
            )
            connection.execute(statement)

    return len(matched_usage), len(usage) - len(matched_usage)
