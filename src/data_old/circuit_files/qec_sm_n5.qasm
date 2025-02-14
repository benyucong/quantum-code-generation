OPENQASM 3.0;
include "stdgates.inc";
gate syndrome _gate_q_0, _gate_q_1, _gate_q_2, _gate_q_3, _gate_q_4 {
  cx _gate_q_0, _gate_q_3;
  cx _gate_q_1, _gate_q_3;
  cx _gate_q_1, _gate_q_4;
  cx _gate_q_2, _gate_q_4;
}
bit[3] c;
bit[2] syn;
qubit[3] q;
qubit[2] a;
x q[0];
barrier q[0], q[1], q[2];
syndrome q[0], q[1], q[2], a[0], a[1];
syn[0] = measure a[0];
syn[1] = measure a[1];
if (syn == 1) {
  x q[0];
}
if (syn == 2) {
  x q[2];
}
if (syn == 3) {
  x q[1];
}
c[0] = measure q[0];
c[1] = measure q[1];
c[2] = measure q[2];
