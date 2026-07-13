"""工具注册表：OpenAI function calling schema + 分发执行"""

import json
from typing import Callable

from app.agent.tools.order import query_order
from app.agent.tools.product import query_product
from app.agent.tools.logistics import query_logistics
from app.agent.tools.refund import apply_refund
from app.agent.tools.knowledge import search_knowledge
from app.agent.tools.user_orders import list_user_orders
from app.agent.tools.memory_tool import recall_user_memory
from app.agent.tools.skill_tool import load_skill
from app.agent.tools.coupon import query_coupons
from app.agent.tools.complaint import escalate_complaint

_TOOL_MAP: dict[str, Callable] = {
    "query_order": query_order,
    "query_product": query_product,
    "query_logistics": query_logistics,
    "apply_refund": apply_refund,
    "search_knowledge": search_knowledge,
    "list_user_orders": list_user_orders,
    "recall_user_memory": recall_user_memory,
    "load_skill": load_skill,
    "query_coupons": query_coupons,
    "escalate_complaint": escalate_complaint,
}

TOOL_DEFINITIONS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "query_order",
            "description": "根据订单号查询订单详情，包括订单状态、商品信息、金额、物流单号等",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "订单号，例如 ORD-20240115-001",
                    }
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_product",
            "description": "根据商品名称关键词或商品ID查询商品信息，包括价格、库存、规格等。支持模糊搜索",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "商品名称关键词或商品ID，例如「耳机」「运动鞋」「SHOE-270-BK-42」",
                    }
                },
                "required": ["keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_logistics",
            "description": "根据订单号查询物流轨迹信息，包括快递公司、运单号、运输状态和轨迹事件",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "订单号，例如 ORD-20240115-001",
                    }
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": (
                "检索云商城的政策与帮助文档（退换货政策、配送说明、会员权益、常见问题 FAQ）。"
                "当顾客询问规则、流程、时效、是否支持等政策类问题时使用，"
                "比如「能退货吗」「多久到账」「钻石会员有什么权益」「偏远地区包邮吗」。"
                "返回 Top-K 命中片段及来源文档，请基于检索结果回答，不要编造政策"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "用顾客的原问题或一句简洁中文描述要查的政策点",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回片段数，默认 3，最大 5",
                        "default": 3,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_user_orders",
            "description": (
                "查询当前用户的所有订单概要列表（订单号、状态、商品、金额、下单时间）。"
                "当用户想查订单但未提供订单号，或提供的订单号查不到时，"
                "调用此工具列出订单供用户确认"
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "apply_refund",
            "description": "为指定订单申请退款。必须先明确征得用户确认，并将 confirmed 设为 true",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "要退款的订单号",
                    },
                    "reason": {
                        "type": "string",
                        "description": "退款原因，例如「尺码不合适」「质量问题」「不想要了」",
                    },
                    "confirmed": {
                        "type": "boolean",
                        "description": "用户是否已明确确认提交退款申请",
                        "default": False,
                    },
                    "request_id": {
                        "type": "string",
                        "description": "可选的退款请求唯一标识，用于重试时避免重复提交",
                    },
                },
                "required": ["order_id", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recall_user_memory",
            "description": (
                "查询当前用户的记忆信息，包括本次对话提取的短期记忆和跨会话的长期记忆。"
                "当需要回顾用户的偏好、历史问题、会员信息等时使用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "可选的查询关键词，用于过滤记忆内容",
                        "default": "",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "load_skill",
            "description": (
                "加载指定技能的完整操作指令。"
                "当用户问题匹配某个可用技能时，调用此工具获取该技能的详细处理流程，"
                "然后按流程指引使用已有工具完成用户请求。"
                "可用技能会在系统提示中列出。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_name": {
                        "type": "string",
                        "description": "要加载的技能名称，如 process-return、track-order、product-recommend",
                    }
                },
                "required": ["skill_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_coupons",
            "description": (
                "查询当前用户账户下的优惠券列表。"
                "当用户询问「有没有优惠券」「有什么优惠」「能便宜吗」等问题时使用。"
                "支持按状态筛选：available（可用）、used（已用）、expired（已过期）、all（全部）"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "优惠券状态筛选，默认 available（仅可用），可选 all/available/used/expired",
                        "default": "available",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_complaint",
            "description": "创建投诉升级记录并转交人工客服跟进。",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "用户投诉内容摘要",
                    }
                },
                "required": ["summary"],
            },
        },
    },
]


def execute_tool(name: str, arguments: dict) -> str:
    """根据工具名称分发执行，返回 JSON 字符串结果。"""
    func = _TOOL_MAP.get(name)
    if not func:
        return json.dumps({"error": f"未知工具: {name}"}, ensure_ascii=False)
    try:
        result = func(**arguments)
    except Exception as e:
        result = {"error": f"工具执行出错: {e}"}
    return json.dumps(result, ensure_ascii=False)
