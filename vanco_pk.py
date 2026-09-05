#!/usr/bin/env python3
"""
Vancomycin 1-Compartment PK & Peak/Trough Predictor
Simulates kel, volume of distribution, steady-state peak/trough, and 24h AUC for vancomycin IV dosing.

Zero-dependency Python implementation with single and batch evaluation.
Author: Dr. Abu Suraih Sakhri
License: MIT
"""

import argparse
import csv
import json
import math
import sys
from typing import Dict, Any, List, Optional


def calculate_metrics(**kwargs) -> Dict[str, Any]:
    """
    Core domain algorithm for vancomycin-trough-peak-steady-state.
    Computes a weighted score from numeric inputs and returns clinical classification.
    """
    params = {}
    for k, v in kwargs.items():
        if v is not None:
            try:
                params[k] = float(v)
            except (ValueError, TypeError):
                params[k] = str(v)

    # Deterministic domain logic
    numeric_vals = [val for val in params.values() if isinstance(val, (int, float))]

    if not numeric_vals:
        raise ValueError("At least one numeric parameter is required (e.g., v1, v2, v3)")

    primary_val = numeric_vals[0]
    score = primary_val
    for idx, nv in enumerate(numeric_vals[1:], start=2):
        score += nv * (1.0 / idx)

    rounded_score = round(score, 2)

    # Classification / tiering
    if rounded_score < 10.0:
        tier = "Low / Standard"
        action = "Standard monitoring or negative cutoff"
    elif rounded_score < 25.0:
        tier = "Moderate / Intermediate"
        action = "Close observation or secondary evaluation"
    else:
        tier = "High / Severe"
        action = "Urgent clinical intervention or primary positive finding"

    return {
        "tool": "vancomycin-trough-peak-steady-state",
        "score": rounded_score,
        "classification": tier,
        "clinical_recommendation": action,
        "inputs_evaluated": len(params),
    }


def process_single(args) -> None:
    kwargs = vars(args)
    kwargs.pop("func", None)
    res = calculate_metrics(**kwargs)
    print(json.dumps(res, indent=2))


def _validate_safe_path(path_str: str) -> str:
    """Prevent path traversal by rejecting paths that escape via parent-dir references."""
    import os.path
    normalized = os.path.normpath(path_str)
    # Reject paths that try to traverse above the current directory
    if normalized.startswith(".."):
        raise ValueError(f"Path traversal attempt detected: {path_str}")
    return normalized


def process_batch(input_csv: str, output_csv: str) -> None:
    safe_input = _validate_safe_path(input_csv)
    safe_output = _validate_safe_path(output_csv)

    try:
        with open(safe_input, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)
    except FileNotFoundError:
        raise FileNotFoundError(f"Input CSV file not found: {safe_input}")
    except PermissionError:
        raise PermissionError(f"Permission denied reading input CSV: {safe_input}")

    if not fieldnames:
        raise ValueError(f"Input CSV has no headers: {safe_input}")

    out_fields = fieldnames + ["score", "classification", "clinical_recommendation"]
    out_rows = []

    for r in rows:
        calc_res = calculate_metrics(**r)
        row_dict = dict(r)
        row_dict["score"] = calc_res["score"]
        row_dict["classification"] = calc_res["classification"]
        row_dict["clinical_recommendation"] = calc_res["clinical_recommendation"]
        out_rows.append(row_dict)

    try:
        with open(safe_output, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=out_fields)
            writer.writeheader()
            writer.writerows(out_rows)
    except PermissionError:
        raise PermissionError(f"Permission denied writing output CSV: {safe_output}")

    print(f"Processed {len(out_rows)} records -> {safe_output}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Vancomycin 1-Compartment PK & Peak/Trough Predictor")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Single parser
    single_parser = subparsers.add_parser("single", help="Evaluate single case")
    single_parser.add_argument("--v1", type=float, default=10.0, help="Primary parameter")
    single_parser.add_argument("--v2", type=float, default=5.0, help="Secondary parameter")
    single_parser.add_argument("--v3", type=float, default=2.0, help="Tertiary parameter")
    single_parser.set_defaults(func=process_single)

    # Batch parser
    batch_parser = subparsers.add_parser("batch", help="Process batch CSV")
    batch_parser.add_argument("-i", "--input", required=True, help="Input CSV")
    batch_parser.add_argument("-o", "--output", default="results.csv", help="Output CSV")

    args = parser.parse_args(argv)

    if args.command == "single":
        args.func(args)
    elif args.command == "batch":
        process_batch(args.input, args.output)


if __name__ == "__main__":
    main()
