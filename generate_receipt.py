from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_FIXTURE_FIELDS = {
    "action_type",
    "proof_status",
    "authority_status",
    "dependency_status",
    "constraint_status",
    "refusal_available",
    "claims",
    "policy",
}

ALLOWED_STATUS = {"valid", "invalid", "unverifiable"}
ALLOWED_DECISION = {"PASS", "FAIL"}
VERIFIER_VERSION = "v1.0.0"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return data


def validate_fixture(data: dict[str, Any]) -> None:
    missing = REQUIRED_FIXTURE_FIELDS - set(data.keys())
    if missing:
        raise ValueError(f"Fixture missing required fields: {sorted(missing)}")

    for field in ("proof_status", "authority_status", "dependency_status", "constraint_status"):
        if data[field] not in ALLOWED_STATUS:
            raise ValueError(f"{field} must be one of {sorted(ALLOWED_STATUS)}")

    if not isinstance(data["refusal_available"], bool):
        raise ValueError("refusal_available must be a boolean.")

    if not isinstance(data["claims"], dict):
        raise ValueError("claims must be a JSON object.")

    if not isinstance(data["policy"], dict):
        raise ValueError("policy must be a JSON object.")


def derive_decision(data: dict[str, Any]) -> str:
    statuses = (
        data["proof_status"],
        data["authority_status"],
        data["dependency_status"],
        data["constraint_status"],
    )

    if not data["refusal_available"]:
        return "FAIL"

    if any(status != "valid" for status in statuses):
        return "FAIL"

    return "PASS"


def build_receipt(fixture: dict[str, Any]) -> dict[str, Any]:
    bind_timestamp_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    input_claims_hash = sha256_text(canonical_json(fixture["claims"]))
    policy_hash = sha256_text(canonical_json(fixture["policy"]))
    decision = derive_decision(fixture)

    receipt = {
        "receipt_schema": "bind_admissibility_receipt/v1",
        "action_type": fixture["action_type"],
        "bind_timestamp_utc": bind_timestamp_utc,
        "decision": decision,
        "proof_status": fixture["proof_status"],
        "authority_status": fixture["authority_status"],
        "dependency_status": fixture["dependency_status"],
        "constraint_status": fixture["constraint_status"],
        "refusal_available": fixture["refusal_available"],
        "input_claims_hash": input_claims_hash,
        "policy_hash": policy_hash,
        "verifier_version": VERIFIER_VERSION,
    }

    receipt["receipt_sha256"] = sha256_text(canonical_json(receipt))
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a minimal bind-time admissibility receipt.")
    parser.add_argument("--fixture", required=True, help="Path to sanitized input fixture JSON.")
    parser.add_argument("--out", required=True, help="Path to output receipt JSON.")
    args = parser.parse_args()

    fixture_path = Path(args.fixture)
    out_path = Path(args.out)

    fixture = load_json(fixture_path)
    validate_fixture(fixture)

    receipt = build_receipt(fixture)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Wrote receipt to: {out_path}")
    print(f"decision={receipt['decision']}")
    print(f"receipt_sha256={receipt['receipt_sha256']}")


if __name__ == "__main__":
    main()