#!/usr/bin/env python3
"""Deterministic one-compartment IV-infusion vancomycin PK calculations.

Educational steady-state simulation only. Requires externally estimated kel and Vd;
not a Bayesian estimator, dose recommendation, or substitute for measured TDM.
"""

import argparse
import csv
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Any, Dict

REQUIRED_FIELDS = ("dose_mg", "interval_h", "infusion_h", "elimination_rate_h", "volume_l")


def _positive(name: str, value: Any, *, allow_zero: bool = False) -> float:
    try:
        n = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not math.isfinite(n) or (n < 0 if allow_zero else n <= 0):
        raise ValueError(f"{name} must be finite and {'nonnegative' if allow_zero else 'greater than zero'}")
    return n


def calculate_metrics(
    *, dose_mg: float, interval_h: float, infusion_h: float,
    elimination_rate_h: float, volume_l: float,
    sample_after_infusion_h: float = 0.0,
) -> Dict[str, float]:
    """Predict steady-state exposure with first-order elimination and repeated IV infusions.

    Peak is immediately at infusion completion; trough is immediately before next dose.
    Sample time is hours after infusion completion, within the dosing interval.
    Units: dose mg, time h, elimination constant h^-1, Vd L, concentration mg/L.
    """
    dose = _positive("dose_mg", dose_mg)
    tau = _positive("interval_h", interval_h)
    t_inf = _positive("infusion_h", infusion_h)
    kel = _positive("elimination_rate_h", elimination_rate_h)
    vd = _positive("volume_l", volume_l)
    post = _positive("sample_after_infusion_h", sample_after_infusion_h, allow_zero=True)

    if t_inf > tau:
        raise ValueError("infusion_h cannot exceed interval_h")
    if post > tau - t_inf:
        raise ValueError("sample_after_infusion_h must fall before the next dose")

    clearance = kel * vd
    # expm1 avoids cancellation for small kel * infusion/dosing interval.
    if not math.isfinite(clearance) or clearance == 0 or t_inf * clearance == 0:
        raise ValueError("Inputs produce non-finite PK outputs; check their magnitudes")
    try:
        peak = (dose / (t_inf * clearance)) * (
            -math.expm1(-kel * t_inf) / -math.expm1(-kel * tau)
        )
    except (ZeroDivisionError, OverflowError) as exc:
        raise ValueError("Inputs produce non-finite PK outputs; check their magnitudes") from exc
    trough = peak * math.exp(-kel * (tau - t_inf))
    sample = peak * math.exp(-kel * post)
    auc24 = 24.0 * dose / (tau * clearance)
    half_life = math.log(2.0) / kel
    results = {
        "clearance_l_h": clearance,
        "half_life_h": half_life,
        "peak_mg_l": peak,
        "trough_mg_l": trough,
        "sample_mg_l": sample,
        "auc24_mg_h_l": auc24,
        "approx_steady_state_h": 5.0 * half_life,
    }
    if not all(math.isfinite(v) for v in results.values()):
        raise ValueError("Inputs produce non-finite PK outputs; check their magnitudes")
    return results


def _validate_safe_path(path_str: str) -> Path:
    path = Path(path_str)
    if ".." in path.parts:
        raise ValueError(f"Path traversal attempt detected: {path_str}")
    return path


def _csv_safe(value: Any) -> Any:
    """Avoid formula execution when raw input columns are opened in spreadsheets."""
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def process_batch(input_csv: str, output_csv: str) -> int:
    source = _validate_safe_path(input_csv)
    destination = _validate_safe_path(output_csv)
    if source.resolve() == destination.resolve():
        raise ValueError("Input and output CSV paths must differ")

    with source.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        if not fields:
            raise ValueError("Input CSV has no headers")
        missing = set(REQUIRED_FIELDS) - set(fields)
        if missing:
            raise ValueError("Input CSV missing required columns: " + ", ".join(sorted(missing)))
        output_columns = ["clearance_l_h", "half_life_h", "peak_mg_l", "trough_mg_l", "sample_mg_l", "auc24_mg_h_l", "approx_steady_state_h"]
        if set(fields) & set(output_columns):
            raise ValueError("Input CSV contains reserved output column names")
        records = []
        for line, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Malformed CSV at record starting near line {line}")
            try:
                kwargs = {k: row[k] for k in REQUIRED_FIELDS}
                if "sample_after_infusion_h" in fields:
                    kwargs["sample_after_infusion_h"] = row["sample_after_infusion_h"]
                values = calculate_metrics(**kwargs)
            except ValueError as exc:
                raise ValueError(f"Invalid input near line {line}: {exc}") from exc
            records.append({**{k: _csv_safe(v) for k, v in row.items()}, **values})

    # Write atomically so input errors cannot leave partially generated CSV results.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", dir=destination.parent, delete=False) as f:
            temporary = Path(f.name)
            writer = csv.DictWriter(f, fieldnames=[*fields, *output_columns])
            writer.writeheader()
            writer.writerows(records)
        os.replace(temporary, destination)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return len(records)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="One-compartment vancomycin IV infusion steady-state simulator (educational; not for clinical dosing)")
    commands = parser.add_subparsers(dest="command", required=True)
    single = commands.add_parser("single", help="Predict a single steady-state dosing schedule")
    for flag in REQUIRED_FIELDS:
        single.add_argument("--" + flag.replace("_", "-"), type=float, required=True)
    single.add_argument("--sample-after-infusion-h", type=float, default=0.0)
    batch = commands.add_parser("batch", help="Process a CSV containing all five PK inputs")
    batch.add_argument("-i", "--input", required=True)
    batch.add_argument("-o", "--output", default="results.csv")
    args = parser.parse_args(argv)
    try:
        if args.command == "single":
            inputs = {k: getattr(args, k) for k in REQUIRED_FIELDS}
            inputs["sample_after_infusion_h"] = args.sample_after_infusion_h
            print(json.dumps(calculate_metrics(**inputs), indent=2))
        else:
            count = process_batch(args.input, args.output)
            print(f"Processed {count} records -> {args.output}")
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
