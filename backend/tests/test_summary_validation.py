import pytest
from pydantic import ValidationError

from app.models import SummaryResponse


def test_summary_requires_three_bullets() -> None:
    with pytest.raises(ValidationError):
        SummaryResponse(
            paper_id="2401.12345",
            summary_bullets=["one", "two"],
            contributions=["contribution"],
            limitations=["limitation"],
            follow_up_papers=["follow up"],
        )


def test_summary_strips_empty_items() -> None:
    summary = SummaryResponse(
        paper_id="2401.12345",
        summary_bullets=[" one ", "two", "three"],
        contributions=[" method ", ""],
        limitations=[" data only "],
        follow_up_papers=[" related work "],
    )

    assert summary.contributions == ["method"]
    assert summary.limitations == ["data only"]
