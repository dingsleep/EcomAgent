import copy

import pytest

pytestmark = pytest.mark.unit

import app.agent.tools.refund as refund
from app.agent.tools.mock_data import ORDERS
from app.agent.tools.product import query_product
from app.agent.tools.registry import TOOL_DEFINITIONS


@pytest.fixture(autouse=True)
def restore_mock_orders():
    original_orders = copy.deepcopy(ORDERS)
    refund.REFUND_REQUESTS.clear()
    yield
    ORDERS.clear()
    ORDERS.update(original_orders)
    refund.REFUND_REQUESTS.clear()


def test_unknown_product_is_not_fabricated():
    result = query_product("不存在的商品")

    assert result == {
        "success": False,
        "products": [],
        "error": "未找到与“不存在的商品”匹配的商品",
    }


def test_unconfirmed_refund_does_not_change_order_state():
    order_id = "ORD-20240120-002"

    result = refund.apply_refund(order_id, "不想要了", confirmed=False)

    assert result["success"] is False
    assert result["confirmation_required"] is True
    assert ORDERS[order_id]["status"] == "pending"


def test_confirmed_refund_updates_order_state():
    order_id = "ORD-20240120-002"

    result = refund.apply_refund(
        order_id,
        "不想要了",
        confirmed=True,
        request_id="refund-request-001",
    )

    assert result["success"] is True
    assert ORDERS[order_id]["status"] == "refund_processing"
    assert ORDERS[order_id]["refund_reason"] == "不想要了"


def test_confirmed_refund_request_id_is_idempotent():
    order_id = "ORD-20240120-002"
    request_id = "refund-request-002"

    first = refund.apply_refund(order_id, "不想要了", confirmed=True, request_id=request_id)
    repeated = refund.apply_refund(order_id, "不想要了", confirmed=True, request_id=request_id)

    assert first["success"] is True
    assert repeated["success"] is True
    assert repeated["idempotent"] is True
    assert repeated["message"] == first["message"]


def test_confirmed_pending_order_keeps_cancellation_message():
    result = refund.apply_refund(
        "ORD-20240120-002",
        "不想要了",
        confirmed=True,
        request_id="refund-request-003",
    )

    assert "尚未发货，已直接取消并发起退款" in result["message"]


def test_refund_schema_exposes_confirmation_and_request_id():
    refund_tool = next(
        tool for tool in TOOL_DEFINITIONS if tool["function"]["name"] == "apply_refund"
    )
    properties = refund_tool["function"]["parameters"]["properties"]

    assert properties["confirmed"]["default"] is False
    assert properties["request_id"]["type"] == "string"
