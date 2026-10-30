import argparse
from . import run, compare

def main():
    ap = argparse.ArgumentParser(prog="byte-tree-quantum")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run"); r.add_argument("--depth", type=int, default=1); r.add_argument("--seed", type=int, default=42)
    c = sub.add_parser("compare"); c.add_argument("--n", type=int, default=10000); c.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    run(a.depth, a.seed) if a.cmd == "run" else compare(a.n, a.seed)

if __name__ == "__main__":
    main()
