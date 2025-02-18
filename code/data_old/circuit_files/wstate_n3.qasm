OPENQASM 3.0;
include "stdgates.inc";
gate cH _gate_q_0, _gate_q_1 {
  h _gate_q_1;
  sdg _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  h _gate_q_1;
  t _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  t _gate_q_1;
  h _gate_q_1;
  s _gate_q_1;
  x _gate_q_1;
  s _gate_q_0;
}
bit[3] c;
qubit[3] q;
u3(1.91063, 0, 0) q[0];
cH q[0], q[1];
ccx q[0], q[1], q[2];
x q[0];
x q[1];
cx q[0], q[1];
c[0] = measure q[0];
c[1] = measure q[1];
c[2] = measure q[2];
