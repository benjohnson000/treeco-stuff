import pandas as pd
import streamlit as st

from config import load_settings, save_settings
from database import engine
from metrics import build_inventory_projection


st.set_page_config(page_title="ECI Spruce Reorder Tool", layout="wide")


def load_projection(settings, include_inactive):
    try:
        inventory = pd.read_sql(
            "SELECT sku, description, on_hand, on_order, available FROM inventory",
            engine,
        )
        usage_history = pd.read_sql(
            "SELECT sku, year, month, quantity_used FROM usage_history",
            engine,
        )
    except Exception as error:
        st.error("No imported inventory data is available yet.")
        st.code("py -3.14 main.py", language="powershell")
        st.caption(f"Database detail: {error}")
        st.stop()

    return build_inventory_projection(
        inventory,
        usage_history,
        settings,
        include_inactive=include_inactive,
    )


def reset_editor_state():
    st.session_state.pop("inventory_editor", None)


def initialize_selection(projection):
    if "selected_skus" not in st.session_state:
        st.session_state.selected_skus = set()

    if not st.session_state.get("selection_initialized"):
        st.session_state.selected_skus = set(
            projection.loc[
                projection["recommended_order_qty"].fillna(0).gt(0), "sku"
            ]
        )
        st.session_state.selection_initialized = True

    if "order_amount_overrides" not in st.session_state:
        st.session_state.order_amount_overrides = {}


def update_order_state(edited_table, visible_skus):
    selected_visible_skus = set(
        edited_table.loc[edited_table["order_selected"], "sku"]
    )
    st.session_state.selected_skus.difference_update(visible_skus)
    st.session_state.selected_skus.update(selected_visible_skus)

    for row in edited_table.itertuples(index=False):
        recommended_amount = 0 if pd.isna(row.recommended_order_qty) else row.recommended_order_qty
        order_amount = 0 if pd.isna(row.order_amount) else row.order_amount

        if order_amount == recommended_amount:
            st.session_state.order_amount_overrides.pop(row.sku, None)
        else:
            st.session_state.order_amount_overrides[row.sku] = order_amount


def add_order_amounts(projection):
    display_projection = projection.copy()
    display_projection["order_amount"] = display_projection["sku"].map(
        st.session_state.order_amount_overrides
    )
    display_projection["order_amount"] = display_projection["order_amount"].fillna(
        display_projection["recommended_order_qty"]
    ).fillna(0)
    return display_projection


def main():
    st.title("ECI Spruce Inventory Reorder Tool")

    current_settings = load_settings()
    with st.sidebar:
        st.header("Reorder settings")
        with st.form("settings_form"):
            stock_target_days = st.number_input(
                "Stock target (days)",
                min_value=0.0,
                value=float(current_settings["stock_target_days"]),
                step=1.0,
            )
            vendor_lead_time_days = st.number_input(
                "Vendor lead time (days)",
                min_value=0.0,
                value=float(current_settings["vendor_lead_time_days"]),
                step=1.0,
            )
            buffer_days = st.number_input(
                "Buffer time (days)",
                min_value=0.0,
                value=float(current_settings["buffer_days"]),
                step=1.0,
            )
            save_clicked = st.form_submit_button("Save settings")

        if save_clicked:
            save_settings({
                "stock_target_days": stock_target_days,
                "vendor_lead_time_days": vendor_lead_time_days,
                "buffer_days": buffer_days,
            })
            reset_editor_state()
            st.success("Settings saved.")
            st.rerun()

        include_inactive = st.checkbox(
            "Show items with no stock and no sales",
            value=False,
        )

    projection = load_projection(current_settings, include_inactive)
    initialize_selection(projection)

    search_text = st.text_input("Search SKU or description")
    display_projection = add_order_amounts(projection)
    if search_text:
        matches = (
            display_projection["sku"].str.contains(search_text, case=False, na=False)
            | display_projection["description"].str.contains(
                search_text, case=False, na=False
            )
        )
        display_projection = display_projection.loc[matches]

    display_projection["order_selected"] = display_projection["sku"].isin(
        st.session_state.selected_skus
    )

    select_column, clear_column, summary_column = st.columns([1, 1, 3])
    with select_column:
        if st.button("Select visible recommended"):
            st.session_state.selected_skus.update(
                display_projection.loc[
                    display_projection["recommended_order_qty"].fillna(0).gt(0),
                    "sku",
                ]
            )
            reset_editor_state()
            st.rerun()
    with clear_column:
        if st.button("Clear selection"):
            st.session_state.selected_skus.clear()
            reset_editor_state()
            st.rerun()
    with summary_column:
        st.caption("Use the Order? checkbox to manually include or exclude an item.")

    edited_projection = st.data_editor(
        display_projection,
        key="inventory_editor",
        hide_index=True,
        width="stretch",
        height=600,
        disabled=[
            column
            for column in display_projection
            if column not in {"order_selected", "order_amount"}
        ],
        column_order=[
            "order_selected",
            "sku",
            "description",
            "on_hand",
            "on_order",
            "available",
            "last_12_month_sales",
            "avg_daily_sales",
            "projected_days_remaining",
            "recommended_order_qty",
            "order_amount",
        ],
        column_config={
            "order_selected": st.column_config.CheckboxColumn("Order?"),
            "on_hand": st.column_config.NumberColumn("On hand", format="%.0f"),
            "on_order": st.column_config.NumberColumn("On order", format="%.0f"),
            "last_12_month_sales": st.column_config.NumberColumn(
                "12-month sales", format="%.0f"
            ),
            "avg_daily_sales": st.column_config.NumberColumn(
                "Avg. daily sales", format="%.3f"
            ),
            "projected_days_remaining": st.column_config.NumberColumn(
                "Projected days", format="%.1f"
            ),
            "recommended_order_qty": st.column_config.NumberColumn(
                "Recommended order", format="%.0f"
            ),
            "order_amount": st.column_config.NumberColumn(
                "Order amount",
                min_value=0,
                step=1,
                format="%.0f",
            ),
        },
    )
    update_order_state(edited_projection, set(display_projection["sku"]))

    selected_items = add_order_amounts(projection).loc[
        projection["sku"].isin(st.session_state.selected_skus)
    ].copy()
    selected_items = selected_items.loc[selected_items["order_amount"].gt(0)]
    selected_units = selected_items["order_amount"].sum()
    item_metric, unit_metric = st.columns(2)
    item_metric.metric("Selected items", len(selected_items))
    unit_metric.metric("Recommended units", f"{selected_units:,.0f}")

    if not selected_items.empty:
        st.subheader("Purchase-order preview")
        st.dataframe(
            selected_items[
                ["sku", "description", "order_amount"]
            ],
            hide_index=True,
            width="stretch",
        )
        st.download_button(
            "Download selected items as CSV",
            selected_items[["sku", "description", "order_amount"]].to_csv(
                index=False
            ).encode("utf-8"),
            file_name="purchase_order_draft.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
