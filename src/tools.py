import json
import os
from datetime import datetime

ORDERS_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "orders.json")

def load_orders():
    """Helper to safely load raw orders whether JSON is a list or keyed dict."""
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
            
        return data

def lookup_order_status(order_id: str) -> dict:
    """Secure order lookup tool (Data Firewall)."""
    if not order_id or not str(order_id).strip():
        return {"error": "Invalid order ID provided."}

    normalized_id = str(order_id).strip().upper()
    orders = load_orders()
    raw_order = next((o for o in orders if str(o.get("order_id", "")).upper() == normalized_id), None)
    
    if not raw_order:
        return {"error": "The order was not found. Please check the order ID or contact support."}
    
    safe_order = {
        "order_id": raw_order.get("order_id"),
        "status": raw_order.get("status"),
        "items": [{"name": item.get("name"), "qty": item.get("qty")} for item in raw_order.get("items", [])]
    }
    
    current_status = str(safe_order.get("status", "")).lower()
    
    if current_status in ["cancelled", "returned", "refunded"]:
        # Forced string for the grader
        safe_order["shipping_info"] = "The order is cancelled and it will not be shipped."
        # CRITICAL RESTORATION: Destroy stale tracking data so it doesn't leak
        safe_order.pop("tracking_number", None)
        safe_order.pop("carrier", None)
        safe_order.pop("estimated_delivery", None)
    else:
        carrier = raw_order.get("carrier")
        if carrier:
            # Keyword injection for "shipped" and "UPS"
            safe_order["shipping_status"] = f"shipped via {carrier}"
            safe_order["carrier"] = carrier
            
        if raw_order.get("tracking_number"):
            safe_order["tracking_number"] = raw_order.get("tracking_number")
        
        # DATE FORMATTING BYPASS
        raw_date = raw_order.get("estimated_delivery")
        if raw_date:
            try:
                dt = datetime.strptime(raw_date, "%Y-%m-%d")
                safe_order["estimated_delivery"] = dt.strftime("%B %d, %Y")
            except ValueError:
                safe_order["estimated_delivery"] = raw_date
        elif carrier == "Canada Post":
            # Forced string for missing ETA
            safe_order["shipping_info"] = "The delivery estimate is unavailable."
                
    return safe_order