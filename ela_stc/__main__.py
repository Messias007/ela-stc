"""CLI: python -m ela_stc <case.yaml> <rules.yaml> [out_prefix]"""
import os
import sys

from .loader import load_case, load_params
from .report import matrix_markdown, run_aml, traceability_csv
from .rules import load_rules


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    aml, inst = load_case(argv[0])
    run = run_aml(aml, inst, load_rules(argv[1]), load_params(argv[0]))
    md = matrix_markdown(run)
    print(md)
    if len(argv) > 2:
        os.makedirs(os.path.dirname(argv[2]) or ".", exist_ok=True)
        with open(argv[2] + "_matriz.md", "w", encoding="utf-8") as f:
            f.write(md)
        with open(argv[2] + "_rastreabilidade.csv", "w", encoding="utf-8") as f:
            f.write(traceability_csv(run))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
