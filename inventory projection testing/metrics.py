import pandas as pd


DAYS_PER_MONTH = 30.4375


def build_inventory_projection(inventory, usage_history):
    """Join current inventory to recent usage and calculate days of supply."""
    recent_usage = _latest_twelve_months(usage_history)
    usage_by_sku = recent_usage.groupby("sku", as_index=False).agg(
        average_monthly_usage=("quantity_used", "mean")
    )
    usage_by_sku["daily_usage"] = (
        usage_by_sku["average_monthly_usage"] / DAYS_PER_MONTH
    )

    projection = inventory.merge(usage_by_sku, on="sku", how="left")
    projection["projected_days_remaining"] = (
        projection["available"] / projection["daily_usage"]
    )
    projection.loc[
        projection["daily_usage"].isna() | (projection["daily_usage"] <= 0),
        "projected_days_remaining"
    ] = pd.NA

    return projection[[
        "sku",
        "description",
        "on_hand",
        "on_order",
        "available",
        "projected_days_remaining"
    ]].round({"projected_days_remaining": 1})


def _latest_twelve_months(usage_history):
    ordered_usage = usage_history.sort_values(
        ["sku", "year", "month"],
        ascending=[True, False, False]
    )
    return ordered_usage.groupby("sku", group_keys=False).head(12)
