import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from agents.api import PKRequest, api_pk


def test_pk_endpoint_uses_same_pk_equations():
    payload = PKRequest(
        dose_mg=1000, interval_h=12, infusion_h=1,
        elimination_rate_h=0.1, volume_l=50,
    )
    result = api_pk(payload)
    assert result["auc24_mg_h_l"] == pytest.approx(400)
    assert result["peak_mg_l"] == pytest.approx(27.23577382621341)


def test_pk_endpoint_rejects_inconsistent_schedule():
    payload = PKRequest(
        dose_mg=1000, interval_h=12, infusion_h=13,
        elimination_rate_h=0.1, volume_l=50,
    )
    with pytest.raises(HTTPException) as info:
        api_pk(payload)
    assert info.value.status_code == 422


def test_pk_endpoint_rejects_nonfinite_inputs():
    with pytest.raises(ValidationError):
        PKRequest(
            dose_mg=float("nan"), interval_h=12, infusion_h=1,
            elimination_rate_h=0.1, volume_l=50,
        )
