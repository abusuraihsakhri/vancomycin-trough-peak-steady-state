# Vancomycin Trough Peak Steady State

> **Domain:** Clinical Pharmacology & Precision Pharmacotherapy  
> **Reference Guidelines:** CPIC Guidelines, FDA Pharmacogenomic Biomarkers

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)

---

## 📖 What It Does

Vancomycin 1-Compartment PK Simulator evaluates dosing parameters and classifies clinical risk based on a weighted scoring algorithm. It provides:

- Single-case evaluation via CLI
- Batch CSV processing
- FastAPI REST API with Prometheus metrics
- HMAC-SHA256 tamper-evident audit trail
- Zero-PHI outbound guard (blocks SSNs, MRNs, phone numbers, etc.)

Author: Dr. Abu Suraih Sakhri  
License: MIT

---

## ⚙️ Key Features

### Core PK Module (`vanco_pk.py`)
- **`calculate_metrics(**kwargs)`** — Computes a weighted score from numeric parameters (v1, v2, v3) and returns clinical classification (Low/Moderate/High).
- **`process_single(args)`** — Evaluates a single case from CLI arguments.
- **`process_batch(input_csv, output_csv)`** — Processes a CSV of cases and appends score/classification columns.

### Enterprise Agent Suite (`agents/`)
- **`SystemSupervisor`** — Orchestrates multi-worker task evaluation with PHI validation.
- **Specialized Workers** — QC Invariant, Safety Escalation, Protocol Conformance.
- **`AuditLogger`** — Cryptographic HMAC-SHA256 chained audit trail.
- **`PHIGuard`** — Outbound PHI detection and redaction.

### API Server (`agents/api.py`)
- `GET /health` — Service health check
- `GET /metrics` — Prometheus operational metrics
- `POST /api/audit` — Submit task for evaluation
- `POST /api/chat` — Supervisory chat endpoint
- `GET /api/audit/logs` — Retrieve and verify audit trail

---

## 💻 Quickstart

### Installation
```bash
pip install fastapi uvicorn pydantic pytest
```

### CLI Usage

#### Single Case Evaluation
```bash
python vanco_pk.py single --v1 14.5 --v2 4.2 --v3 1.8
```

#### Batch CSV Processing
```bash
python vanco_pk.py batch -i sample.csv -o results.csv
```

#### Enterprise Supervisor CLI
```bash
# Audit a single task
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2

# Batch processing
python cli.py batch -i sample.csv -o results.csv

# Verify audit trail integrity
python cli.py verify-audit

# Start API server
python cli.py serve --host 127.0.0.1 --port 8000
```

### Input Data Schema (for vanco_pk batch)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Patient identifier | Required |
| `v1` | Primary PK parameter | Required |
| `v2` | Secondary PK parameter | Optional |
| `v3` | Tertiary PK parameter | Optional |

---

## 🛡️ Security Architecture

* **Zero-PHI Outbound Interceptor:** AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation.
* **Path Traversal Protection:** All file paths validated against absolute paths and parent-directory traversal.
* **Secure Secret Management:** Audit signing key sourced from `AUDIT_SECRET_KEY` environment variable (no hardcoded defaults).

---

## 🧪 Testing

```bash
# Run all tests
pytest -v

# Run with coverage
pytest -v --cov=.
```

### Test Coverage
- `test_vanco_pk.py` — Core PK calculation and batch processing
- `tests/test_enrichment.py` — Enrichment module threshold escalation
- `tests/test_vancomycin_trough_peak_steady_state.py` — PHI guard, workers, supervisor consensus, audit integrity

---

## 🐳 Container Deployment

### Docker
```bash
docker build -t vancomycin-trough-peak-steady-state .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key vancomycin-trough-peak-steady-state
```

### Docker Compose
```bash
cp .env.example .env
# Edit .env to set your AUDIT_SECRET_KEY
docker compose up -d
```

---

## 📊 Simulation & Benchmarking

```bash
# Run high-throughput simulation (100 tasks)
python simulator.py 100

# Run benchmark suite
python -m pytest tests/ -v
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
