from app.agent.tools.mock_data import COUPONS


def query_coupons(status: str = "available") -> dict:
    """查询用户优惠券，可按状态筛选：available（可用）/ used（已用）/ expired（已过期）/ all（全部）。"""
    if status == "all":
        filtered = list(COUPONS.values())
    else:
        filtered = [c for c in COUPONS.values() if c["status"] == status]

    return {
        "success": True,
        "count": len(filtered),
        "coupons": filtered,
    }
