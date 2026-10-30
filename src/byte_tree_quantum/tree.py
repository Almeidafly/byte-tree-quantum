"""Pure-Python port of byte-tree.mjs (same PRNG, same rules)."""
import math, time

LIT, DARK = 0, 1
M32 = 0xFFFFFFFF


def word(b):
    return "lit" if b == LIT else "dark"


def _imul(a, b):
    return (a * b) & M32


class rng:
    """mulberry32, bit-identical to the JS version, plus Box-Muller gauss()."""

    def __init__(self, seed):
        self.a = int(seed) & M32

    def __call__(self):
        self.a = (self.a + 0x6D2B79F5) & M32
        t = self.a
        t = _imul(t ^ (t >> 15), t | 1)
        t ^= (t + _imul(t ^ (t >> 7), t | 61)) & M32
        return ((t ^ (t >> 14)) & M32) / 4294967296

    def gauss(self):
        return math.sqrt(-2 * math.log(self() + 1e-12)) * math.cos(2 * math.pi * self())


def leaf_bit(count, threshold):
    return LIT if count >= threshold else DARK


def computer(bits, weights=None, bias=None):
    """Majority vote of 8 bits (>4 lit -> lit, ties dark) or weighted threshold."""
    if not weights:
        return LIT if sum(1 for b in bits if b == LIT) > 4 else DARK
    s = sum(w for b, w in zip(bits, weights) if b == LIT)
    return LIT if s >= (bias if bias is not None else sum(weights) / 2) else DARK


def block_count(d):
    return 9 ** d


C, R, NOISE, K, THRESH = (0.5, 0.5), 0.3, 0.12, 5, 3


def _in_disc(x, y, cx, cy, r):
    return (x - cx) ** 2 + (y - cy) ** 2 <= r * r


def truth(p):
    return LIT if _in_disc(p[0], p[1], C[0], C[1], R) else DARK


def _sub_regions(r, n=8, jitter=0.06):
    out = []
    for _ in range(n):
        a = C[0] + (r() - 0.5) * 2 * jitter
        b = C[1] + (r() - 0.5) * 2 * jitter
        c = R + (r() - 0.5) * 0.06
        out.append((a, b, c))
    return out


def region_count(p, reg, r, k=K):
    c = 0
    for _ in range(k):
        x = p[0] + r.gauss() * NOISE
        y = p[1] + r.gauss() * NOISE
        if _in_disc(x, y, *reg):
            c += 1
    return c


def make_tree(depth, r):
    """Every bit gets its own computer: each of the 8 bits is a depth-1 smaller tree."""
    if depth == 0:
        return {"leaf": _sub_regions(r, 1)[0]}
    return {"kids": [make_tree(depth - 1, r) for _ in range(8)], "weights": None, "bias": None}


def eval_tree(t, p, r, k=K, th=THRESH):
    if "leaf" in t:
        return leaf_bit(region_count(p, t["leaf"], r, k), th)
    bits = [eval_tree(c, p, r, k, th) for c in t["kids"]]
    t["last_bits"] = bits
    return computer(bits, t["weights"], t["bias"])


def leaves(t):
    return 1 if "leaf" in t else sum(leaves(c) for c in t["kids"])


def train_weights(t, train, r, epochs=5):
    t["weights"] = [1.0] * 8
    t["bias"] = 4.0
    for _ in range(epochs):
        for p in train:
            pred, y = eval_tree(t, p, r), truth(p)
            if pred != y:
                d = 1 if y == LIT else -1
                for i, b in enumerate(t["last_bits"]):
                    if b == LIT:
                        t["weights"][i] = max(0.0, t["weights"][i] + 0.1 * d)
                t["bias"] -= 0.1 * d


def _print_tree(t, p, r, indent="", out=print):
    ans = eval_tree(t, p, r)
    lb = t["last_bits"]
    out(f"{indent}[computer] answer={word(ans)} ({ans})  byte={' '.join(map(word, lb))}  ({''.join(map(str, lb))})")
    if "kids" in t["kids"][0]:
        for i, c in enumerate(t["kids"]):
            out(f"{indent}  bit{i}:")
            _print_tree(c, p, r, indent + "    ", out)


def run(depth=1, seed=42, out=print):
    depth = max(1, int(depth))
    r = rng(seed)
    t = make_tree(depth, r)
    p = (r(), r())
    out(f"byte-tree depth={depth}  blocks={block_count(depth)}  leaf detectors={leaves(t)}")
    out("structure: 1 block -> 3 blocks (1 computer + 2 data) -> 9 blocks (1 computer + 8 data bits = 1 byte)")
    out(f"input point=({p[0]:.3f}, {p[1]:.3f})  truth={word(truth(p))}")
    _print_tree(t, p, r, "", out)
    return t


def compare(n=10000, seed=42, out=print):
    r = rng(seed)
    test = [(r(), r()) for _ in range(n)]
    train = [(r(), r()) for _ in range(2000)]
    rows = []

    def bench(name, blocks, samples, f):
        t0 = time.perf_counter()
        ok = sum(1 for p in test if f(p) == truth(p))
        rows.append([name, blocks, samples, f"{100 * ok / n:.2f}%", f"{(time.perf_counter() - t0) * 1000:.1f} ms"])

    target = (C[0], C[1], R)
    bench("(a) single detector, K=5", 1, K, lambda p: leaf_bit(region_count(p, target, r), THRESH))
    bench("(a2) single detector, K=40 (budget = depth1)", 1, 40, lambda p: leaf_bit(region_count(p, target, r, 40), 20))
    bench("(a3) single detector, K=320 (budget = depth2)", 1, 320, lambda p: leaf_bit(region_count(p, target, r, 320), 160))
    t1 = make_tree(1, r); bench("(b) depth-1 byte tree, majority", 9, 8 * K, lambda p: eval_tree(t1, p, r))
    t1w = make_tree(1, r); train_weights(t1w, train, r)
    bench("(b2) depth-1 byte tree, learned weights", 9, 8 * K, lambda p: eval_tree(t1w, p, r))
    t2 = make_tree(2, r); bench("(c) depth-2 recursive tree, majority", 81, 64 * K, lambda p: eval_tree(t2, p, r))
    t2w = make_tree(2, r); train_weights(t2w, train, r)
    bench("(c2) depth-2 recursive tree, learned top weights", 81, 64 * K, lambda p: eval_tree(t2w, p, r))
    out(f"byte-tree compare  N={n} test points, seed={seed}, noise sd={NOISE}, K={K} obs/leaf, leaf threshold={THRESH}")
    out("task: is point inside disc (0.5,0.5) r=0.3? lit(0)=inside, dark(1)=outside")
    h = ["method", "blocks", "noisy obs/pt", "accuracy", "runtime"]
    w = [max(len(h[i]), *(len(str(x[i])) for x in rows)) for i in range(5)]
    for row in [h] + rows:
        out("  ".join(str(c).ljust(w[i]) for i, c in enumerate(row)))
    return rows
