from app.agent.tools.mock_data import PRODUCTS


def _match_score(product: dict, keywords: list[str]) -> int:
    """计算商品与关键词列表的匹配度（命中关键词数量）。"""
    searchable = " ".join([
        product["name"],
        product["category"],
        product.get("description", ""),
        " ".join(str(v) for v in product.get("specs", {}).values()),
    ]).lower()
    return sum(1 for kw in keywords if kw in searchable)


def query_product(keyword: str) -> dict:
    """根据商品名称关键词或商品ID查询商品信息，包括价格、库存、规格等。"""
    if keyword in PRODUCTS:
        return {"success": True, "products": [PRODUCTS[keyword]]}

    keywords = [kw.lower() for kw in keyword.split() if kw.strip()]
    if not keywords:
        keywords = [keyword.lower()]

    scored = [(p, _match_score(p, keywords)) for p in PRODUCTS.values()]
    results = [p for p, score in scored if score > 0]

    if not results:
        return {
            "success": False,
            "products": [],
            "error": f"未找到与“{keyword}”匹配的商品",
        }
    return {"success": True, "products": results}
