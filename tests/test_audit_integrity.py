from agents.base import AuditTrail


def test_signed_chain_detects_mutations():
    trail = AuditTrail(secret_key="test-key")
    trail.log("unit", "test", "SAMPLE", {"id": "S-01"})
    trail.log("unit", "test", "SAMPLE", {"id": "S-02"})
    assert trail.verify_integrity() is True
    detached = trail.get_trail()
    detached[0]["event_type"] = "FORGED"
    assert trail.verify_integrity() is True
    trail.logs[0]["event_type"] = "FORGED"
    assert trail.verify_integrity() is False


def test_detects_rehashed_chain_without_key():
    trail = AuditTrail(secret_key="test-key")
    trail.log("unit", "test", "SAMPLE", {"id": "S-01"})
    trail.logs[0]["current_hash"] = "0" * 64
    assert trail.verify_integrity() is False
