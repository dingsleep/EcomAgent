"""Complaint escalation tool for the local mock service."""

import hashlib


def escalate_complaint(summary: str) -> dict:
    """Create a deterministic mock complaint record for human follow-up."""
    if not summary or not summary.strip():
        return {"success": False, "error": "投诉内容不能为空"}
    case_id = f"CMP-{hashlib.sha256(summary.encode()).hexdigest()[:8].upper()}"
    return {
        "success": True,
        "case_id": case_id,
        "status": "已升级至人工客服",
    }
