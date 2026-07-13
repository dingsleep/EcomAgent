import pytest

from app.evaluation import metrics


pytestmark = pytest.mark.unit


def test_complaint_escalation_is_faithfulness_evidence():
    assert "escalate_complaint" in metrics.FACT_TOOLS
