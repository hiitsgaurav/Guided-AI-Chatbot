"""
Basic unit tests for the tool functions. Run with:
    python -m pytest tests/
or simply:
    python tests/test_tools.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tools import search_faq, check_order_status, create_support_ticket, escalate_to_human


def test_search_faq_finds_match():
    result = search_faq("what is your return policy")
    assert result["found"] is True
    assert any("return" in r["category"] for r in result["results"])


def test_search_faq_no_match():
    result = search_faq("xyzabc nonsense query")
    assert result["found"] is False


def test_check_order_status_found():
    result = check_order_status("ORD1001")
    assert result["found"] is True
    assert result["status"] == "Shipped"


def test_check_order_status_not_found():
    result = check_order_status("ORD9999")
    assert result["found"] is False


def test_create_support_ticket():
    result = create_support_ticket(
        customer_name="Test User",
        email="test@example.com",
        issue_summary="Item arrived damaged",
        priority="high",
    )
    assert result["created"] is True
    assert result["ticket"]["priority"] == "high"


def test_escalate_to_human():
    result = escalate_to_human(reason="Customer requested a human agent", urgency="urgent")
    assert result["escalated"] is True


if __name__ == "__main__":
    test_search_faq_finds_match()
    test_search_faq_no_match()
    test_check_order_status_found()
    test_check_order_status_not_found()
    test_create_support_ticket()
    test_escalate_to_human()
    print("All tests passed!")
