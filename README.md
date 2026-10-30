# byte-tree-quantum

Python port of [Almeidafly/byte-tree](https://github.com/Almeidafly/byte-tree): a ternary block tree,
**1 block -> 3 blocks (1 computer + 2 data) -> 9 blocks (1 computer + 8 data bits = 1 byte)**.
Signals are active-low: **lit = 0, dark = 1**.

## The rule: every bit gets its own computer
Every bit in the tree must get its own computer. At depth 1, 8 leaf bits feed one computer.
At depth d, each of those 8 bits is itself a full depth d-1 tree with its own computer,
so depth d has `9**d` blocks and `8**d` leaf detectors.

## Install
    pip install byte-tree-quantum            # pure Python, zero dependencies
    pip install "byte-tree-quantum[qiskit]"  # + Qiskit / Aer circuit mapping
(Not yet published to PyPI; for now `pip install git+https://github.com/Almeidafly/byte-tree-quantum`.)

## Classical usage
    python -m byte_tree_quantum run --depth 2 --seed 42
    python -m byte_tree_quantum compare --n 10000 --seed 42

```python
from byte_tree_quantum import computer, make_tree, eval_tree, train_weights, rng, LIT, DARK
computer([LIT]*5 + [DARK]*3)   # majority: >4 lit -> lit (0); ties -> dark
r = rng(42); t = make_tree(2, r); eval_tree(t, (0.5, 0.5), r)
```
Same mulberry32 PRNG, majority vote and perceptron-learned weights as the JS version; outputs for
the same seed match the JS output.

## Quantum mapping (`to_qiskit`)
```python
from byte_tree_quantum import to_qiskit, qubit_count
qc = to_qiskit(1, bits=[0,0,0,0,0,1,1,1])   # root computer measured into clbit 0 -> 0 (lit)
```
Per node: 8 data qubits + 1 computer qubit (|0> = lit, |1> = dark). The computer starts dark and
a multi-controlled X flips it to lit for each of the 93 byte patterns with >= 5 lit bits, so on
basis-state inputs it computes exactly the classical majority. Recursively, each data bit is the
computer qubit of its own subtree.

| depth | qubits | blocks |
|---|---|---|
| 1 | 9 | 9 |
| 2 | 73 | 81 |
| 3 | 585 (refused by default, `max_qubits=80`) | 729 |

Honest note: this is a reversible-logic encoding of a classical vote, not a quantum speed-up.
Depth 1 is verified against the classical computer on the Aer simulator; depth 2 is built and
checked for size (73 qubits is too large for a statevector simulation in CI).

## Tests
    pip install -e ".[test,qiskit]" && pytest

## License
License: not yet chosen, all rights reserved.
