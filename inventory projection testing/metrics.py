import numpy as np
import pandas as pd


DAYS_PER_MONTH = 30.4375


def build_inventory_projection(
    inventory,
    usage_history,
    settings,
    include_inactive=False,
):
    """Join current inventory to recent usage and calculate days of supply."""
    recent_usage = _latest_twelve_months(usage_history)
    usage_by_sku = recent_usage.groupby("sku", as_index=False).agg(
        last_12_month_sales=("quantity_used", "sum"),
        average_monthly_usage=("quantity_used", "mean")
    )
    usage_by_sku["avg_daily_sales"] = (
        usage_by_sku["average_monthly_usage"] / DAYS_PER_MONTH
    )

    projection = inventory.merge(usage_by_sku, on="sku", how="left")
    if not include_inactive:
        projection = projection.loc[
            ~(
                projection["on_hand"].eq(0)
                & projection["last_12_month_sales"].fillna(0).eq(0)
            )
        ].copy()

    projection["projected_days_remaining"] = (
        projection["available"] / projection["avg_daily_sales"]
    )
    projection.loc[
        projection["avg_daily_sales"].isna() | (projection["avg_daily_sales"] <= 0),
        "projected_days_remaining"
    ] = pd.NA

    target_coverage_days = (
        settings["stock_target_days"]
        + settings["vendor_lead_time_days"]
        + settings["buffer_days"]
    )
    projection["recommended_order_qty"] = np.ceil(
        (
            projection["avg_daily_sales"] * target_coverage_days
            - projection["available"]
        ).clip(lower=0)
    )
    projection.loc[
        projection["avg_daily_sales"].isna() | (projection["avg_daily_sales"] <= 0),
        "recommended_order_qty"
    ] = pd.NA

    return projection[[
        "sku",
        "description",
        "on_hand",
        "on_order",
        "available",
        "last_12_month_sales",
        "avg_daily_sales",
        "projected_days_remaining",
        "recommended_order_qty"
    ]].round({
        "last_12_month_sales": 1,
        "avg_daily_sales": 3,
        "projected_days_remaining": 1,
        "recommended_order_qty": 0
    })


def _latest_twelve_months(usage_history):
    ordered_usage = usage_history.sort_values(
        ["sku", "year", "month"],
        ascending=[True, False, False]
    )
    return ordered_usage.groupby("sku", group_keys=False).head(12)
