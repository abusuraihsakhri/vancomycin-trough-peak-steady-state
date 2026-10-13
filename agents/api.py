"""
FastAPI REST API Server for Vancomycin Trough Peak Steady State.
"""
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from vanco_pk import calculate_metrics
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Vancomycin Trough Peak Steady State API",
    description="Enterprise Distributed Component Platform (Clinical Pharmacology & Pharmacogenomics)",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "vancomycin-trough-peak-steady-state", "domain": "Clinical Pharmacology & Pharmacogenomics", "standard": "Demonstration-only rules; not clinical guidance", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}


class PKRequest(BaseModel):
    """Externally supplied one-compartment parameters; no patient identifiers."""
    dose_mg: float = Field(gt=0, allow_inf_nan=False)
    interval_h: float = Field(gt=0, allow_inf_nan=False)
    infusion_h: float = Field(gt=0, allow_inf_nan=False)
    elimination_rate_h: float = Field(gt=0, allow_inf_nan=False)
    volume_l: float = Field(gt=0, allow_inf_nan=False)
    sample_after_infusion_h: float = Field(default=0, ge=0, allow_inf_nan=False)


@app.post("/api/pk")
def api_pk(payload: PKRequest):
    """Educational PK simulation, not clinical dose optimization."""
    try:
        return calculate_metrics(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
