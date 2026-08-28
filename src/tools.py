import json
import os

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
    """
    Secure order lookup tool (Data Firewall).
    Strips all PII and cleans stale delivery data for dead orders.
    """
    if not order_id or not str(order_id).strip():
        return {"error": "Invalid order ID provided."}

    normalized_id = str(order_id).strip().upper()
    orders = load_orders()
    
    raw_order = next((o for o in orders if str(o.get("order_id", "")).upper() == normalized_id), None)
    if not raw_order:
        return {"error": f"Order {normalized_id} not found."}
    
    # Strictly allowlist safe fields (strips email, phone, address, risk_score)
    safe_order = {
        "order_id": raw_order.get("order_id"),
        "status": raw_order.get("status"),
        "items": [
            {"name": item.get("name"), "qty": item.get("qty")}
            for item in raw_order.get("items", [])
        ]
    }
    
    current_status = str(safe_order.get("status", "")).lower()
    
    # Remove stale delivery fields for cancelled/returned orders
    if current_status in ["cancelled", "returned", "refunded"]:
        safe_order["shipping_info"] = "Not applicable due to order status."
    else:
        if raw_order.get("carrier"):
            safe_order["carrier"] = raw_order.get("carrier")
        if raw_order.get("tracking_number"):
            safe_order["tracking_number"] = raw_order.get("tracking_number")
        if raw_order.get("estimated_delivery"):
            safe_order["estimated_delivery"] = raw_order.get("estimated_delivery")
            
    return safe_order