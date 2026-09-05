import pytest
import os
from vanco_pk import calculate_metrics, process_batch


def test_vanco_pk_single():
    res = calculate_metrics(v1=12.0, v2=4.0)
    assert "score" in res
    assert "classification" in res
    assert res["score"] > 0


def test_vanco_pk_single_high_score():
    res = calculate_metrics(v1=30.0, v2=15.0, v3=10.0)
    assert res["classification"] == "High / Severe"
    assert res["score"] > 25.0


def test_vanco_pk_single_moderate_score():
    res = calculate_metrics(v1=15.0, v2=5.0)
    assert res["classification"] == "Moderate / Intermediate"


def test_vanco_pk_single_low_score():
    res = calculate_metrics(v1=5.0, v2=2.0)
    assert res["classification"] == "Low / Standard"


def test_vanco_pk_no_numeric_raises():
    with pytest.raises(ValueError, match="numeric parameter is required"):
        calculate_metrics(Patient_ID="PT-001", Name="Test Patient")


def test_vanco_pk_batch(tmp_path):
    csv_in = tmp_path / "in.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text("Patient,v1,v2\nPat_001,15.0,3.0\nPat_002,5.0,1.0\n", encoding="utf-8")

    process_batch(str(csv_in), str(csv_out))
    assert csv_out.exists()
    content = csv_out.read_text(encoding="utf-8")
    assert "Pat_001" in content
    assert "score" in content


def test_vanco_pk_batch_missing_file():
    with pytest.raises(FileNotFoundError):
        process_batch("nonexistent_file.csv", "output.csv")


def test_vanco_pk_batch_path_traversal():
    with pytest.raises(ValueError, match="Path traversal"):
        process_batch("../etc/passwd", "output.csv")

    with pytest.raises(ValueError, match="Path traversal"):
        process_batch("foo/../../../etc/passwd", "output.csv")


def test_vanco_pk_batch_empty_headers(tmp_path):
    csv_in = tmp_path / "empty.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="no headers"):
        process_batch(str(csv_in), str(csv_out))


def test_vanco_pk_weighted_calculation():
    """Verify weighted scoring: score = v1 + v2/2 + v3/3"""
    res = calculate_metrics(v1=10.0, v2=4.0, v3=6.0)
    expected_score = round(10.0 + 4.0/2 + 6.0/3, 2)
    assert res["score"] == expected_score
