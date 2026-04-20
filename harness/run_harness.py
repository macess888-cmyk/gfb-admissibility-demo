from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def load_scenarios(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("scenarios.json must contain a JSON array.")
    return data


def find_fixture_for_name(scenarios: list[dict], name: str) -> str:
    for item in scenarios:
        if item.get("name") == name:
            fixture = item.get("fixture")
            if not isinstance(fixture, str) or not fixture.strip():
                raise ValueError(f"Scenario '{name}' has no valid fixture path.")
            return fixture
    raise ValueError(f"Scenario '{name}' not found in scenarios.json")


def run_command(cmd: list[str], cwd: Path) -> int:
    print(f"\n> {' '.join(cmd)}\n")
    completed = subprocess.run(cmd, cwd=str(cwd))
    return completed.returncode


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the admissibility harness on a named scenario or a direct fixture."
    )
    parser.add_argument(
        "--scenario",
        help="Scenario name from harness/scenarios.json (e.g. clean_pass).",
    )
    parser.add_argument(
        "--fixture",
        help="Direct path to a fixture JSON file (alternative to --scenario).",
    )
    parser.add_argument(
        "--out",
        help="Output receipt path. If omitted, defaults to receipts/<scenario_or_fixture>_receipt.json",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    scenarios_path = repo_root / "harness" / "scenarios.json"

    if not args.scenario and not args.fixture:
        raise SystemExit("Provide either --scenario or --fixture")

    if args.scenario and args.fixture:
        raise SystemExit("Use either --scenario or --fixture, not both")

    if args.scenario:
        scenarios = load_scenarios(scenarios_path)
        fixture_rel = find_fixture_for_name(scenarios, args.scenario)
        receipt_name = f"{args.scenario}_receipt.json"
    else:
        fixture_rel = args.fixture
        receipt_name = f"{Path(args.fixture).stem}_receipt.json"

    fixture_path = repo_root / fixture_rel
    if not fixture_path.exists():
        raise SystemExit(f"Fixture not found: {fixture_path}")

    if args.out:
        receipt_path = repo_root / args.out
    else:
        receipt_path = repo_root / "receipts" / receipt_name

    receipt_path.parent.mkdir(parents=True, exist_ok=True)

    py = sys.executable

    gen_cmd = [
        py,
        "generate_receipt.py",
        "--fixture",
        str(fixture_path),
        "--out",
        str(receipt_path),
    ]

    verify_cmd = [
        py,
        "verify/verify_receipt.py",
        "--receipt",
        str(receipt_path),
    ]

    gen_rc = run_command(gen_cmd, repo_root)
    if gen_rc != 0:
        raise SystemExit(gen_rc)

    verify_rc = run_command(verify_cmd, repo_root)
    raise SystemExit(verify_rc)


if __name__ == "__main__":
    main()