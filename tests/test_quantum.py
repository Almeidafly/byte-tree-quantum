import random
import pytest
from byte_tree_quantum import computer, qubit_count, to_qiskit

def test_qubit_counts():
    assert [qubit_count(d) for d in (1, 2, 3)] == [9, 73, 585]

qiskit = pytest.importorskip("qiskit")
aer = pytest.importorskip("qiskit_aer")

def _run(qc):
    from qiskit import transpile
    sim = aer.AerSimulator()
    res = sim.run(transpile(qc, sim), shots=16).result().get_counts()
    assert len(res) == 1
    return int(next(iter(res)))

def test_depth1_matches_classical():
    rnd = random.Random(0)
    cases = [[0]*8, [1]*8, [0]*5+[1]*3, [0]*4+[1]*4] + [[rnd.randint(0,1) for _ in range(8)] for _ in range(12)]
    for bits in cases:
        assert _run(to_qiskit(1, bits)) == computer(bits), bits

def test_depth2_builds():
    qc = to_qiskit(2, [0]*64)
    assert qc.num_qubits == 73
    with pytest.raises(ValueError):
        to_qiskit(3)
