from app.agent.tools.mock_data import ORDERS

REFUND_REQUESTS: dict[str, dict] = {}


def apply_refund(
    order_id: str,
    reason: str,
    confirmed: bool = False,
    request_id: str | None = None,
) -> dict:
    """为指定订单申请退款；确认后执行，并支持请求 ID 幂等。"""
    order = ORDERS.get(order_id)
    if not order:
        return {"success": False, "error": f"未找到订单 {order_id}，请核实订单号"}

    if not reason.strip():
        return {"success": False, "error": "请提供退款原因"}

    if not confirmed:
        return {
            "success": False,
            "confirmation_required": True,
            "message": f"请确认是否为订单 {order_id} 提交退款申请，退款原因：{reason}。",
        }

    cache_key = f"{order_id}:{request_id}" if request_id else None
    if cache_key and cache_key in REFUND_REQUESTS:
        return {**REFUND_REQUESTS[cache_key], "idempotent": True}

    if order["status"] == "refund_processing":
        return {"success": False, "error": "该订单已有退款申请正在处理中，请耐心等待"}

    was_pending = order["status"] == "pending"
    order["status"] = "refund_processing"
    order["refund_reason"] = reason
    order["refund_status"] = "审核中"

    if was_pending:
        result = {
            "success": True,
            "message": (
                f"订单 {order_id} 尚未发货，已直接取消并发起退款。"
                f"退款原因：{reason}。退款将在 1-3 个工作日内原路退回。"
            ),
        }
    else:
        result = {
            "success": True,
            "message": (
                f"退款申请已提交。订单 {order_id}，退款原因：{reason}。"
                f"预计 1-3 个工作日内审核完成，届时会通知您退货地址。"
            ),
        }

    if cache_key:
        REFUND_REQUESTS[cache_key] = result
    return result
