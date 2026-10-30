"""byte_tree_quantum: ternary byte tree (1 -> 3 -> 9) with an optional Qiskit mapping.

Signals are active-low: lit = 0, dark = 1.
Rule: every bit in the tree gets its own computer.
"""
from .tree import (LIT, DARK, word, rng, leaf_bit, computer, block_count, make_tree,
                   eval_tree, leaves, train_weights, truth, region_count, run, compare)
from .quantum import qubit_count, to_qiskit

__all__ = ["LIT", "DARK", "word", "rng", "leaf_bit", "computer", "block_count", "make_tree",
           "eval_tree", "leaves", "train_weights", "truth", "region_count", "run", "compare",
           "qubit_count", "to_qiskit"]
__version__ = "0.1.0"
