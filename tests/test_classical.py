import random
from byte_tree_quantum import (LIT, DARK, computer, block_count, leaves, make_tree, rng, run, leaf_bit)

def test_rng_matches_js_mulberry32():
    # reference: JS mulberry32(42) first value
    assert abs(rng(42)() - 0.6011037519201636) < 1e-15

def test_majority():
    assert computer([LIT]*5 + [DARK]*3) == LIT
    assert computer([LIT]*4 + [DARK]*4) == DARK

def test_weighted():
    assert computer([LIT] + [DARK]*7, weights=[10]+[1]*7) == LIT
    assert computer([DARK] + [LIT]*7, weights=[10]+[0]*7, bias=1) == DARK

def test_leaf():
    assert leaf_bit(3, 3) == LIT and leaf_bit(2, 3) == DARK

def test_every_bit_gets_a_computer():
    for d in (1, 2, 3):
        t = make_tree(d, rng(1))
        assert leaves(t) == 8 ** d
        assert block_count(d) == 9 ** d
        def check(n, lvl):
            if lvl == 0:
                assert "leaf" in n; return
            assert len(n["kids"]) == 8
            for k in n["kids"]: check(k, lvl - 1)
        check(t, d)

def test_run_output():
    lines = []
    run(2, 42, out=lines.append)
    assert lines[0].startswith("byte-tree depth=2  blocks=81  leaf detectors=64")
