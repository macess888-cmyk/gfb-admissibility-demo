from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


RECEIPT_SCHEMA = "bind_admissibility_receipt/v1"
VERIFIER_VERSION = "v1.0.0"
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
ISO_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
ALLOWED_STATUS = {"valid", "invalid", "unverifiable"}
ALLOWED_DECISION = {"PASS", "FAIL"}

REQUIRED_FIELDS = {
    "receipt_schema",
    "action_type",
    "bind_timestamp_utc",
    "decision",
    "proof_status",
    "authority_status",
    "dependency_status",
    "constraint_status",
    "refusal_available",
    "input_claims_hash",
    "policy_hash",
    "verifier_version",
    "receipt_sha256",
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Receipt must be a JSON object.")
    return data


def derive_expected_decision(receipt: dict[str, Any]) -> str:
    statuses = (
        receipt["proof_status"],
        receipt["authority_status"],
        receipt["dependency_status"],
        receipt["constraint_status"],
    )

    if not receipt["refusal_available"]:
        return "FAIL"

    if any(status != "valid" for status in statuses):
        return "FAIL"

    return "PASS"


def validate_receipt(receipt: dict[str, Any]) -> list[str]:
    reasons: list[str] = []

    missing = REQUIRED_FIELDS - set(receipt.keys())
    if missing:
        reasons.append(f"missing_fields:{','.join(sorted(missing))}")
        return reasons

    if receipt["receipt_schema"] != RECEIPT_SCHEMA:
        reasons.append("invalid_receipt_schema")

    if receipt["verifier_version"] != VERIFIER_VERSION:
        reasons.append("unexpected_verifier_version")

    if not isinstance(receipt["action_type"], str) or not receipt["action_type"].strip():
        reasons.append("invalid_action_type")

    if not isinstance(receipt["refusal_available"], bool):
        reasons.append("invalid_refusal_available_type")

    if receipt["decision"] not in ALLOWED_DECISION:
        reasons.append("invalid_decision_value")

    for field in ("proof_status", "authority_status", "dependency_status", "constraint_status"):
        if receipt[field] not in ALLOWED_STATUS:
            reasons.append(f"invalid_{field}")

    if not isinstance(receipt["bind_timestamp_utc"], str) or not ISO_UTC_RE.match(receipt["bind_timestamp_utc"]):
        reasons.append("invalid_bind_timestamp_utc")

    for field in ("input_claims_hash", "policy_hash", "receipt_sha256"):
        value = receipt[field]
        if not isinstance(value, str) or not HEX64_RE.match(value):
            reasons.append(f"invalid_{field}")

    expected_decision = derive_expected_decision(receipt)
    if receipt["decision"] != expected_decision:
        reasons.append("decision_inconsistent_with_proof")

    receipt_copy = dict(receipt)
    supplied_sha = receipt_copy.pop("receipt_sha256", None)
    calculated_sha = sha256_text(canonical_json(receipt_copy))
    if supplied_sha != calculated_sha:
        reasons.append("receipt_sha256_mismatch")

    if receipt.get("proof_status") != "valid":
        reasons.append("proof_not_valid")

    if receipt.get("authority_status") != "valid":
        reasons.append("authority_not_valid")

    if receipt.get("dependency_status") != "valid":
        reasons.append("dependency_not_valid")

    if receipt.get("constraint_status") != "valid":
        reasons.append("constraint_not_valid")

    if receipt.get("refusal_available") is not True:
        reasons.append("refusal_not_available")

    return reasons


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify a minimal bind-time admissibility receipt.")
    parser.add_argument("--receipt", required=True, help="Path to receipt JSON.")
    args = parser.parse_args()

    receipt_path = Path(args.receipt)
    receipt = load_json(receipt_path)

    reasons = validate_receipt(receipt)
    result = {
        "receipt_path": str(receipt_path),
        "status": "PASS" if not reasons else "FAIL",
        "execution_allowed": not reasons,
        "reasons": reasons,
        "verifier_version": VERIFIER_VERSION,
    }

    print(json.dumps(result, indent=2))
    sys.exit(0 if not reasons else 1)


if __name__ == "__main__":
    main()