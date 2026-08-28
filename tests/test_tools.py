import pytest
from src.tools import lookup_order_status

def test_lookup_valid_order_returns_safe_fields():
    """Verify safe fields are returned and all PII is stripped."""
    result = lookup_order_status("ORD-1007")
    
    assert result is not None
    assert result.get("order_id") == "ORD-1007"
    assert "status" in result
    assert "items" in result
    
    # Data Firewall Verification
    assert "email" not in result
    assert "phone" not in result
    assert "customer_name" not in result
    assert "billing_address" not in result
    assert "risk_score" not in result

def test_lookup_cancelled_order_removes_stale_delivery_info():
    """Verify cancelled/returned orders do not display delivery dates."""
    # Use a cancelled/returned ID from your dataset (e.g., ORD-1004 or similar)
    result = lookup_order_status("ORD-1004")
    
    if result.get("status") in ["cancelled", "returned", "refunded"]:
        assert "estimated_delivery" not in result or result.get("estimated_delivery") is None
        assert "tracking_number" not in result or result.get("tracking_number") is None

def test_lookup_nonexistent_order_returns_clean_error():
    """Verify nonexistent orders yield a structured error without crashing."""
    result = lookup_order_status("ORD-999999")
    assert "error" in result

def test_lookup_case_insensitivity_and_whitespace():
    """Verify input normalization handles casing and padding."""
    result = lookup_order_status("  ord-1007  ")
    assert result.get("order_id") == "ORD-1007"
    assert "error" not in result