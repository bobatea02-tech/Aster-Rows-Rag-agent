import json
import os
from datetime import datetime

ORDERS_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "orders.json")

# Orders in these statuses will not move further; any carrier/tracking/ETA
# still present on the raw record is stale and must not be shown as current.
TERMINAL_STATUSES_NO_TRACKING = {"cancelled", "returned", "refunded"}


def load_orders():
    """Load the mock orders dataset. Returns a list of order dicts."""
    if not os.path.exists(ORDERS_FILE_PATH):
        return []

    with open(ORDERS_FILE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict) and "orders" in data:
        return data["orders"]

    if isinstance(data, dict):
        orders_list = []
        for key, val in data.items():
            if isinstance(val, dict):
                val["order_id"] = val.get("order_id", key)
                orders_list.append(val)
        return orders_list

    if isinstance(data, list):
        return data

    return []


def _format_date(raw_date):
    """Convert an ISO date (YYYY-MM-DD) to 'Month DD, YYYY'. Falls back to the raw string on bad input."""
    if not raw_date:
        return None
    try:
        return datetime.strptime(raw_date, "%Y-%m-%d").strftime("%B %d, %Y")
    except (ValueError, TypeError):
        return raw_date


def lookup_order_status(order_id: str) -> dict:
    """
    Order lookup tool. Returns only customer-safe fields (see
    data/orders-data-dictionary.md). Never exposes customer.*, internal.*,
    or any other private block. `status` is authoritative; stale shipping
    fields are dropped for orders that will not move further.
    """
    if not order_id or not str(order_id).strip():
        return {"error": "missing_order_id", "message": "An order ID is required, e.g. ORD-1007."}

    normalized_id = str(order_id).strip().upper()
    orders = load_orders()

    raw_order = next(
        (o for o in orders if str(o.get("order_id", "")).strip().upper() == normalized_id),
        None,
    )
    if not raw_order:
        return {"error": "not_found", "message": f"No order matching '{normalized_id}' was found."}

    status = str(raw_order.get("status", "")).strip().lower()

    safe_order = {
        "order_id": raw_order.get("order_id"),
        "status": status,
        "membership_tier": raw_order.get("membership_tier"),
        "items": [
            {
                "name": item.get("name"),
                "quantity": item.get("quantity"),
                "final_sale": item.get("final_sale"),
            }
            for item in raw_order.get("items", [])
        ],
        "placed_at": raw_order.get("placed_at"),
        "status_updated_at": raw_order.get("status_updated_at"),
        # Authored, human-correct text per order (differentiates cancelled
        # vs. returned vs. delayed vs. exception correctly, unlike a single
        # hardcoded string reused across all of them).
        "customer_safe_message": raw_order.get("customer_safe_message"),
    }

    if status not in TERMINAL_STATUSES_NO_TRACKING:
        if raw_order.get("carrier"):
            safe_order["carrier"] = raw_order.get("carrier")
        if raw_order.get("tracking_number"):
            safe_order["tracking_number"] = raw_order.get("tracking_number")

        # Explicit None (not omitted) so the model can see the estimate is
        # known-to-be-unavailable rather than confusing "absent" with
        # "wasn't asked for."
        safe_order["estimated_delivery"] = _format_date(raw_order.get("estimated_delivery"))

    if status == "exception":
        safe_order["requires_human_handoff"] = True

    return safe_order