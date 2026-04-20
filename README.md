# Proof Demo — Bind-Time Admissibility

## Purpose

This is a minimal public-safe demonstration of a bind-time admissibility rule:

**No present-state proof at bind → no execution**

The demo does not expose internal system state, proprietary logic, or hidden architecture.  
It proves only that execution is allowed or blocked based on bind-time admissibility using sanitized fixtures, generated receipts, and an independent verifier.

---

## Boundary Rule

Execution is allowed only when required conditions are valid **at the moment of action**.

Earlier validation is not sufficient.

This demo enforces:

- present-state proof at bind
- fail-closed behavior
- independent receipt verification
- PASS only when required statuses are valid
- FAIL when proof is invalid or unverifiable

---

## Files

- `generate_receipt.py`  
  Generates a minimal bind-time receipt from a sanitized fixture.

- `verify_receipt.py`  
  Independently verifies the generated receipt and returns PASS or FAIL.

- `fixtures/pass.json`  
  Valid present-state proof example.

- `fixtures/fail_stale.json`  
  Invalid proof example.

- `fixtures/fail_unverifiable.json`  
  Unverifiable proof / dependency failure example.

- `receipts/*.json`  
  Generated bind-time receipts.

---

## How to Run

From the project directory:

```bat
python generate_receipt.py --fixture fixtures\pass.json --out receipts\pass_receipt.json
python verify_receipt.py --receipt receipts\pass_receipt.json

python generate_receipt.py --fixture fixtures\fail_stale.json --out receipts\fail_stale_receipt.json
python verify_receipt.py --receipt receipts\fail_stale_receipt.json

python generate_receipt.py --fixture fixtures\fail_unverifiable.json --out receipts\fail_unverifiable_receipt.json
python verify_receipt.py --receipt receipts\fail_unverifiable_receipt.json