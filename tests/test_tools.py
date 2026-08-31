import json
from src.tools import lookup_order_status


def test_valid_order_returns_only_safe_fields():
    result = lookup_order_status("ORD-1007")
    assert result["order_id"] == "ORD-1007"
    assert "status" in result
    assert "items" in result
    assert "customer" not in result
    assert "internal" not in result
    assert "email" not in json.dumps(result)


def test_cancelled_order_has_no_stale_shipping_fields():
    result = lookup_order_status("ORD-1004")
    assert result["status"] == "cancelled"
    assert "tracking_number" not in result
    assert "carrier" not in result
    assert "estimated_delivery" not in result


def test_returned_order_has_no_stale_shipping_fields():
    result = lookup_order_status("ORD-1008")
    assert result["status"] == "returned"
    assert "tracking_number" not in result
    assert "carrier" not in result


def test_shipped_order_with_missing_eta_reports_none_not_invented():
    result = lookup_order_status("ORD-1011")
    assert result["status"] == "shipped"
    assert result.get("estimated_delivery") is None


def test_exception_status_flags_human_handoff():
    result = lookup_order_status("ORD-1010")
    assert result["status"] == "exception"
    assert result.get("requires_human_handoff") is True


def test_item_quantities_are_present_and_correct():
    result = lookup_order_status("ORD-1007")
    assert all(item.get("quantity") is not None for item in result["items"])


def test_unknown_order_returns_structured_error():
    result = lookup_order_status("ORD-999999")
    assert "error" in result


def test_missing_order_id_returns_structured_error_not_crash():
    result = lookup_order_status("")
    assert "error" in result


def test_case_and_whitespace_normalization():
    result = lookup_order_status("  ord-1007  ")
    assert result.get("order_id") == "ORD-1007"
    assert "error" not in result