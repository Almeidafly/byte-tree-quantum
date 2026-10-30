"""Map the byte tree onto a Qiskit circuit (optional extra: pip install byte-tree-quantum[qiskit]).

Per node: 8 data qubits + 1 computer qubit. Basis |0> = lit, |1> = dark (active-low).
The computer qubit is prepared dark (X), then for every 8-bit pattern with >= 5 lit bits
(93 patterns) a multi-controlled X flips it to lit. This computes exactly the classical
majority (>4 lit -> lit, ties dark) on basis-state inputs, and acts linearly on
superpositions. It is an honest reversible-logic mapping, not a quantum speed-up.
At depth d, each of the 8 bits is itself a depth d-1 subtree whose computer qubit
serves as the bit: every bit gets its own computer.
"""
from itertools import product

MAJ_PATTERNS = ["".join(p) for p in product("01", repeat=8) if p.count("0") >= 5]


def qubit_count(depth):
    """q(0)=1 (a bare data qubit), q(d)=8*q(d-1)+1 -> 9, 73, 585, ..."""
    return 1 if depth == 0 else 8 * qubit_count(depth - 1) + 1


def to_qiskit(depth=1, bits=None, measure=True, max_qubits=80):
    """Build the circuit. `bits`: optional list of 8**depth leaf values (0 lit / 1 dark).
    The root computer qubit is the last qubit; measured into classical bit 0."""
    try:
        from qiskit import QuantumCircuit
    except ImportError as e:  # pragma: no cover
        raise ImportError("Qiskit missing: pip install 'byte-tree-quantum[qiskit]'") from e
    if depth < 1:
        raise ValueError("depth must be >= 1")
    n = qubit_count(depth)
    if n > max_qubits:
        raise ValueError(f"depth {depth} needs {n} qubits (> max_qubits={max_qubits})")
    if bits is not None and len(bits) != 8 ** depth:
        raise ValueError(f"need {8 ** depth} leaf bits")
    qc = QuantumCircuit(n, 1 if measure else 0, name=f"byte_tree_d{depth}")
    leaf_iter = iter(bits or [])
    nxt = [0]

    def build(d):
        if d == 0:
            q = nxt[0]; nxt[0] += 1
            if bits is not None and next(leaf_iter) == 1:
                qc.x(q)
            return q
        data = [build(d - 1) for _ in range(8)]
        comp = nxt[0]; nxt[0] += 1
        qc.x(comp)  # start dark
        for pat in MAJ_PATTERNS:
            # qiskit ctrl_state is little-endian: last char <-> first control
            qc.mcx(data, comp, ctrl_state=pat[::-1])
        return comp

    root = build(depth)
    if measure:
        qc.measure(root, 0)
    return qc
