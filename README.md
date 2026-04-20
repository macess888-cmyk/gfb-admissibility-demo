# Bind-Time Admissibility — Minimal Proof (GFB)

A minimal, reproducible demonstration of execution-bound admissibility.

---

## Core Rule

**No present-state proof at bind → no execution**

Execution is allowed only if validity can be proven at the exact moment of action.  
If proof is invalid or cannot be established, execution is blocked.

---

## What This Shows

Three cases:

- valid present-state → PASS  
- stale state → FAIL  
- unverifiable / dependency failure → FAIL  

---

## How It Works

- sanitized fixtures simulate system state  
- a receipt is generated at bind-time  
- an independent verifier evaluates the receipt  
- execution is allowed or blocked based on proof  

---

## Run

```bat
python generate_receipt.py --fixture fixtures\pass.json --out receipts\pass_receipt.json
python verify_receipt.py --receipt receipts\pass_receipt.json

python generate_receipt.py --fixture fixtures\fail_stale.json --out receipts\fail_stale_receipt.json
python verify_receipt.py --receipt receipts\fail_stale_receipt.json

python generate_receipt.py --fixture fixtures\fail_unverifiable.json --out receipts\fail_unverifiable_receipt.json
python verify_receipt.py --receipt receipts\fail_unverifiable_receipt.json