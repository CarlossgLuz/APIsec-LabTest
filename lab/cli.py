import argparse
import os
from pathlib import Path

from lab.reports import save_report
from lab.runner import SCENARIOS, run_scenario


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Executa simulações controladas de segurança."
    )
    parser.add_argument("--scenario", choices=["all", *SCENARIOS], default="all")
    parser.add_argument(
        "--output-dir", type=Path, default=Path(os.getenv("REPORTS_DIR", "reports"))
    )
    args = parser.parse_args()
    names = SCENARIOS if args.scenario == "all" else [args.scenario]
    passed = True
    for name in names:
        result = run_scenario(name)
        paths = save_report(result, args.output_dir)
        passed = passed and result["passed"]
        print(
            f"{name}: {'PASS' if result['passed'] else 'FAIL'} "
            f"— {paths[0]} — {paths[1]}"
        )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
