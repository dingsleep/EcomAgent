import json

import pytest

from app.config.settings import settings
from app.schemas.response import IntentType

pytestmark = pytest.mark.unit


def fake_executor(calls, results):
    def execute(name, arguments):
        calls.append((name, arguments))
        return json.dumps(results[name], ensure_ascii=False)

    return execute


def test_logistics_fast_path_uses_only_logistics_tool():
    from app.agent.fast_path import try_fast_path

    calls = []
    response = try_fast_path(
        "订单 ORD-20240115-001 到哪了？",
        fake_executor(
            calls,
            {
                "query_logistics": {
                    "success": True,
                    "logistics": {
                        "carrier": "顺丰速运",
                        "status": "in_transit",
                        "events": [{"time": "2024-01-18 08:30", "description": "正在派送中"}],
                    },
                }
            },
        ),
    )

    assert calls == [("query_logistics", {"order_id": "ORD-20240115-001"})]
    assert response.intent is IntentType.ORDER_QUERY
    assert "顺丰速运" in response.reply


def test_unshipped_logistics_response_uses_tool_error():
    from app.agent.fast_path import try_fast_path

    calls = []
    response = try_fast_path(
        "订单 ORD-20240120-002 的快递到哪了？",
        fake_executor(calls, {"query_logistics": {"success": False, "error": "该订单尚未发货，暂无物流信息"}}),
    )

    assert calls == [("query_logistics", {"order_id": "ORD-20240120-002"})]
    assert "尚未发货" in response.reply


def test_order_fast_path_uses_only_order_tool():
    from app.agent.fast_path import try_fast_path

    calls = []
    response = try_fast_path(
        "订单号是 ORD-20240110-003，帮我查状态",
        fake_executor(
            calls,
            {"query_order": {"success": True, "order": {"items": [{"name": "小米14 Ultra 手机"}], "status": "delivered", "total": 899}}},
        ),
    )

    assert calls == [("query_order", {"order_id": "ORD-20240110-003"})]
    assert "小米14 Ultra" in response.reply
    assert "899" in response.reply


def test_order_list_fast_path_uses_only_list_tool():
    from app.agent.fast_path import try_fast_path

    calls = []
    response = try_fast_path(
        "我都买过哪些东西？",
        fake_executor(
            calls,
            {"list_user_orders": {"success": True, "orders": [{"order_id": "ORD-1", "items_summary": "Nike Air Max", "status": "已发货", "total": 899}]}},
        ),
    )

    assert calls == [("list_user_orders", {})]
    assert "Nike Air Max" in response.reply


def test_unspecified_order_request_asks_for_order_id_without_tool():
    from app.agent.fast_path import try_fast_path

    calls = []
    response = try_fast_path(
        "我想查询一下我的订单",
        fake_executor(calls, {"list_user_orders": {"success": True, "orders": []}}),
    )

    assert response.intent is IntentType.ORDER_QUERY
    assert "订单号" in response.reply
    assert calls == []


def test_policy_fast_path_only_uses_knowledge_result():
    from app.agent.fast_path import try_fast_path

    calls = []
    response = try_fast_path(
        "你们支持七天无理由退货吗？",
        fake_executor(
            calls,
            {"search_knowledge": {"success": True, "results": [{"doc": "退换货政策", "text": "签收后七天内支持无理由退货。"}]}},
        ),
    )

    assert calls == [("search_knowledge", {"query": "你们支持七天无理由退货吗？"})]
    assert response.intent is IntentType.RETURN_REQUEST
    assert "七天" in response.reply
    assert "退换货政策" in response.reply


def test_strong_complaint_escalates_to_human():
    from app.agent.fast_path import try_fast_path

    calls = []
    response = try_fast_path(
        "我要投诉，不然去消协告你们！",
        fake_executor(calls, {"escalate_complaint": {"success": True, "case_id": "CMP-001"}}),
    )

    assert calls == [("escalate_complaint", {"summary": "我要投诉，不然去消协告你们！"})]
    assert response.intent is IntentType.COMPLAINT
    assert response.requires_human is True


def test_refund_request_uses_order_status_for_after_sale_response():
    from app.agent.fast_path import try_fast_path

    calls = []
    response = try_fast_path(
        "订单号 ORD-20240118-004，尺码不合适，想退款",
        fake_executor(
            calls,
            {"query_order": {"success": True, "order": {"status": "refund_processing", "items": [{"name": "牛仔裤"}], "refund_status": "审核中"}}},
        ),
    )

    assert calls == [("query_order", {"order_id": "ORD-20240118-004"})]
    assert response.intent is IntentType.AFTER_SALE
    assert "退款" in response.reply


def test_agent_uses_fast_path_without_react(monkeypatch, tmp_path):
    from app.agent.chat import EcomAgent

    monkeypatch.setattr(settings, "memory_enabled", False)
    monkeypatch.setattr(settings, "mcp_enabled", False)
    agent = EcomAgent(session_path=str(tmp_path / "session.json"))
    monkeypatch.setattr(agent, "_react_loop", lambda: pytest.fail("ReAct should not run"))

    response = agent.chat("我要投诉，不然去消协告你们！")

    assert response.requires_human is True


def test_multi_agent_uses_fast_path_without_routing(monkeypatch, tmp_path):
    from app.multi_agent.orchestrator import MultiAgentOrchestrator

    monkeypatch.setattr(settings, "memory_enabled", False)
    monkeypatch.setattr(settings, "mcp_enabled", False)
    agent = MultiAgentOrchestrator(session_path=str(tmp_path / "session.json"))
    monkeypatch.setattr(agent.router, "route", lambda *_: pytest.fail("Router should not run"))
    calls = []
    execute = agent.agents["postsale"].tool_manager.execute_tool

    def traced_execute(name, arguments):
        calls.append(name)
        return execute(name, arguments)

    monkeypatch.setattr(agent.agents["postsale"].tool_manager, "execute_tool", traced_execute)

    response = agent.chat("我要投诉，不然去消协告你们！")

    assert response.requires_human is True
    assert calls == ["escalate_complaint"]
