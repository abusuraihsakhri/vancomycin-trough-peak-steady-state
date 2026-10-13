import csv
import math
import pytest
from vanco_pk import calculate_metrics, process_batch

PARAMS = dict(dose_mg=1000, interval_h=12, infusion_h=1, elimination_rate_h=0.1, volume_l=50)


def test_steady_state_mass_balance_and_trough():
    r = calculate_metrics(**PARAMS)
    assert r["clearance_l_h"] == pytest.approx(5)
    assert r["half_life_h"] == pytest.approx(math.log(2) / 0.1)
    assert r["auc24_mg_h_l"] == pytest.approx(400)
    assert r["peak_mg_l"] == pytest.approx((1000 / 5) * (1-math.exp(-0.1)) / (1-math.exp(-1.2)))
    assert r["trough_mg_l"] == pytest.approx(r["peak_mg_l"] * math.exp(-1.1))
    assert r["sample_mg_l"] == pytest.approx(r["peak_mg_l"])


def test_sample_at_next_dose_equals_trough():
    r = calculate_metrics(**PARAMS, sample_after_infusion_h=11)
    assert r["sample_mg_l"] == pytest.approx(r["trough_mg_l"])


def test_infusions_back_to_back_have_equal_peak_and_trough():
    r = calculate_metrics(**{**PARAMS, "infusion_h": 12})
    assert r["peak_mg_l"] == pytest.approx(r["trough_mg_l"])


@pytest.mark.parametrize("field,value", [
    ("dose_mg", 0), ("volume_l", -1), ("elimination_rate_h", math.nan),
    ("interval_h", math.inf), ("infusion_h", "not a number"),
    ("sample_after_infusion_h", -1), ("sample_after_infusion_h", 12),
])
def test_invalid_inputs(field, value):
    with pytest.raises(ValueError):
        calculate_metrics(**{**PARAMS, field: value})


def test_infuser_longer_than_interval():
    with pytest.raises(ValueError, match="cannot exceed"):
        calculate_metrics(**{**PARAMS, "infusion_h": 13})


def test_invalid_extreme_output():
    with pytest.raises(ValueError, match="non-finite"):
        calculate_metrics(**{**PARAMS, "volume_l": 1e-300, "elimination_rate_h": 1e-300})


def test_batch(tmp_path):
    source = tmp_path / "input.csv"
    dest = tmp_path / "output.csv"
    source.write_text("label,dose_mg,interval_h,infusion_h,elimination_rate_h,volume_l\n=1+1,1000,12,1,0.1,50\n", encoding="utf-8")
    assert process_batch(str(source), str(dest)) == 1
    with dest.open(newline="", encoding="utf-8") as f:
        row = next(csv.DictReader(f))
    assert row["label"] == "'=1+1"
    assert float(row["auc24_mg_h_l"]) == pytest.approx(400)


def test_invalid_batch_no_partial_output(tmp_path):
    source = tmp_path / "input.csv"
    dest = tmp_path / "output.csv"
    source.write_text("dose_mg,interval_h,infusion_h,elimination_rate_h,volume_l\n1000,12,1,0.1,50\n0,12,1,0.1,50\n", encoding="utf-8")
    with pytest.raises(ValueError, match="line 3"):
        process_batch(str(source), str(dest))
    assert not dest.exists()


def test_csv_missing_and_equal_paths(tmp_path):
    src = tmp_path / "input.csv"
    src.write_text("dose_mg,volume_l\n1000,50\n")
    with pytest.raises(ValueError, match="required columns"):
        process_batch(str(src), str(tmp_path / "result.csv"))
    with pytest.raises(ValueError, match="must differ"):
        process_batch(str(src), str(src))
    with pytest.raises(ValueError, match="Path traversal"):
        process_batch("../input.csv", str(tmp_path / "result.csv"))
