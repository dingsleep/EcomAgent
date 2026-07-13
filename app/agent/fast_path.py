"""High-confidence requests that can be answered without an LLM round-trip."""

import json
import re
from collections.abc import Callable
from typing import Optional

from app.schemas.response import CustomerServiceResponse, IntentType


_ORDER_ID = re.compile(r"\bORD-\d{8}-\d{3}\b")
_LOGISTICS_WORDS = ("物流", "快递", "到哪", "派送", "运单")
_ORDER_WORDS = ("订单", "订单号", "查状态", "状态", "查询订单")
_ORDER_LIST_WORDS = ("都买过", "全部订单", "所有订单")
_ORDER_INQUIRY_WORDS = ("订单", "查订单", "查询订单")
_POLICY_WORDS = ("七天无理由", "退货政策", "换货政策", "退换货", "支持退货", "支持换货")
_COMPLAINT_WORDS = ("投诉", "消协", "赔偿", "曝光", "举报", "监管", "告你们")
_AFTER_SALE_WORDS = ("退款", "退货", "换货", "售后")


def try_fast_path(
    user_input: str,
    execute_tool: Callable[[str, dict], str],
) -> Optional[CustomerServiceResponse]:
    """Return a deterministic response for a narrow, safe subset of requests."""
    if _is_strong_complaint(user_input):
        escalation = _call(execute_tool, "escalate_complaint", {"summary": user_input})
        case_id = escalation.get("case_id")
        status = "已提交投诉升级"
        if case_id:
            status += f"（受理编号：{case_id}）"
        return CustomerServiceResponse(
            intent=IntentType.COMPLAINT,
            confidence=0.99,
            reply=(
                f"很抱歉给您带来不好的体验，{status}并转交人工专员。"
                "请提供订单号和质量问题的具体情况，专员会尽快联系您处理。"
            ),
            requires_human=True,
            follow_up_question="请提供订单号和具体问题经过，便于人工专员尽快核实。",
        )

    order_id = _find_order_id(user_input)
    if order_id and _contains(user_input, _LOGISTICS_WORDS):
        return _logistics_response(_call(execute_tool, "query_logistics", {"order_id": order_id}))
    if order_id and _contains(user_input, _AFTER_SALE_WORDS):
        return _after_sale_response(_call(execute_tool, "query_order", {"order_id": order_id}))
    if order_id and _contains(user_input, _ORDER_WORDS):
        return _order_response(_call(execute_tool, "query_order", {"order_id": order_id}))
    if _contains(user_input, _ORDER_LIST_WORDS):
        return _order_list_response(_call(execute_tool, "list_user_orders", {}))
    if _contains(user_input, _POLICY_WORDS):
        return _knowledge_response(_call(execute_tool, "search_knowledge", {"query": user_input}))
    if not order_id and _contains(user_input, _ORDER_INQUIRY_WORDS):
        return CustomerServiceResponse(
            intent=IntentType.ORDER_QUERY,
            confidence=0.95,
            reply="请提供订单号，我可以帮您查询订单状态、物流或售后进度。",
            requires_human=False,
            follow_up_question="请提供需要查询的订单号。",
        )
    return None


def _is_strong_complaint(text: str) -> bool:
    return "投诉" in text and _contains(text, _COMPLAINT_WORDS[1:])


def _find_order_id(text: str) -> Optional[str]:
    match = _ORDER_ID.search(text)
    return match.group(0) if match else None


def _contains(text: str, words: tuple[str, ...]) -> bool:
    return any(word in text for word in words)


def _call(execute_tool: Callable[[str, dict], str], name: str, arguments: dict) -> dict:
    try:
        result = execute_tool(name, arguments)
        return json.loads(result) if isinstance(result, str) else result
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        return {"success": False, "error": f"工具调用失败：{error}"}


def _tool_error(payload: dict) -> CustomerServiceResponse:
    return CustomerServiceResponse(
        intent=IntentType.ORDER_QUERY,
        confidence=0.95,
        reply=f"抱歉，{payload.get('error', '暂时无法查询，请稍后重试。')}",
        requires_human=False,
        follow_up_question=None,
    )


def _logistics_response(payload: dict) -> CustomerServiceResponse:
    if not payload.get("success"):
        return _tool_error(payload)
    logistics = payload.get("logistics", {})
    events = logistics.get("events") or []
    latest = events[-1] if events else {}
    progress = ""
    if latest:
        progress = f"最新进度：{latest.get('time', '')} {latest.get('description', '')}。"
    return CustomerServiceResponse(
        intent=IntentType.ORDER_QUERY,
        confidence=0.98,
        reply=(
            f"订单物流由{logistics.get('carrier', '承运商')}承运，"
            f"当前状态：{_status_label(logistics.get('status', ''))}。{progress}"
        ),
        requires_human=False,
        follow_up_question=None,
    )


def _order_response(payload: dict) -> CustomerServiceResponse:
    if not payload.get("success"):
        return _tool_error(payload)
    order = payload.get("order", {})
    items = "、".join(item.get("name", "") for item in order.get("items", [])) or "商品"
    details = [f"订单商品：{items}"]
    if order.get("total") is not None:
        details.append(f"订单金额：¥{order['total']}")
    details.append(f"当前状态：{_status_label(order.get('status', ''))}")
    if order.get("carrier") and order.get("tracking_number"):
        details.append(f"物流：{order['carrier']}（运单号 {order['tracking_number']}）")
    if order.get("estimated_delivery"):
        details.append(f"预计送达：{order['estimated_delivery']}")
    return CustomerServiceResponse(
        intent=IntentType.ORDER_QUERY,
        confidence=0.98,
        reply="；".join(details) + "。如需查询物流或办理售后，请告诉我。",
        requires_human=False,
        follow_up_question=None,
    )


def _order_list_response(payload: dict) -> CustomerServiceResponse:
    if not payload.get("success"):
        return _tool_error(payload)
    orders = payload.get("orders") or []
    if not orders:
        reply = "暂未查询到您的订单。"
    else:
        lines = [
            f"{order.get('order_id', '订单')}：{order.get('items_summary', '商品')}（{order.get('status', '未知状态')}）"
            for order in orders
        ]
        reply = "您购买过的订单如下：" + "；".join(lines) + "。"
    return CustomerServiceResponse(
        intent=IntentType.ORDER_QUERY,
        confidence=0.98,
        reply=reply,
        requires_human=False,
        follow_up_question=None,
    )


def _after_sale_response(payload: dict) -> CustomerServiceResponse:
    if not payload.get("success"):
        return CustomerServiceResponse(
            intent=IntentType.AFTER_SALE,
            confidence=0.9,
            reply=f"抱歉，{payload.get('error', '暂时无法查询售后进度。')}",
            requires_human=True,
            follow_up_question="请提供订单号，人工客服可进一步为您核实。",
        )
    order = payload.get("order", {})
    items = "、".join(item.get("name", "") for item in order.get("items", [])) or "该商品"
    if order.get("status") == "refund_processing":
        refund_status = order.get("refund_status", "处理中")
        reply = f"{items}的退款申请已提交，当前状态为{refund_status}，无需重复申请，请耐心等待审核结果。"
    else:
        reply = f"已查询到{items}的订单状态：{_status_label(order.get('status', ''))}。"
    return CustomerServiceResponse(
        intent=IntentType.AFTER_SALE,
        confidence=0.98,
        reply=reply,
        requires_human=False,
        follow_up_question=None,
    )


def _knowledge_response(payload: dict) -> CustomerServiceResponse:
    if not payload.get("success"):
        return CustomerServiceResponse(
            intent=IntentType.RETURN_REQUEST,
            confidence=0.8,
            reply=f"抱歉，{payload.get('error', '暂时无法查询退换货政策。')}",
            requires_human=True,
            follow_up_question="请提供订单号，人工客服可进一步为您核实。",
        )
    results = payload.get("results") or []
    if not results:
        return CustomerServiceResponse(
            intent=IntentType.RETURN_REQUEST,
            confidence=0.8,
            reply="暂未查询到对应的退换货政策，已为您转人工进一步核实。",
            requires_human=True,
            follow_up_question="请提供订单号，人工客服可进一步为您核实。",
        )
    hit = results[0]
    return CustomerServiceResponse(
        intent=IntentType.RETURN_REQUEST,
        confidence=0.96,
        reply=f"根据《{hit.get('doc', '知识库')}》：{hit.get('text', '')}",
        requires_human=False,
        follow_up_question=None,
    )


def _status_label(status: str) -> str:
    return {
        "pending": "待发货",
        "shipped": "已发货",
        "in_transit": "运输中",
        "delivered": "已签收",
        "refund_processing": "退款处理中",
    }.get(status, status or "暂无状态")
