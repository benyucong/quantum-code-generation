OPENQASM 3.0;
include "stdgates.inc";
gate cu1fixed _gate_q_0, _gate_q_1 {
  u1(-3*pi/8) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  u1(3*pi/8) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
}
gate ctu _gate_q_0, _gate_q_1 {
  cu1fixed _gate_q_0, _gate_q_1;
}
gate cu1(p0) _gate_q_0, _gate_q_1 {
  u1(p0/2) _gate_q_0;
  cx _gate_q_0, _gate_q_1;
  u1(-p0/2) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  u1(p0/2) _gate_q_1;
}
bit[4] c;
qubit[5] q;
h q[0];
h q[1];
h q[2];
h q[3];
ctu q[3], q[4];
ctu q[2], q[4];
ctu q[2], q[4];
ctu q[1], q[4];
ctu q[1], q[4];
ctu q[1], q[4];
ctu q[1], q[4];
ctu q[0], q[4];
ctu q[0], q[4];
ctu q[0], q[4];
ctu q[0], q[4];
ctu q[0], q[4];
ctu q[0], q[4];
ctu q[0], q[4];
ctu q[0], q[4];
h q[0];
cu1(-pi/2) q[0], q[1];
h q[1];
cu1(-pi/4) q[0], q[2];
cu1(-pi/2) q[1], q[2];
h q[2];
cu1(-pi/8) q[0], q[3];
cu1(-pi/4) q[1], q[3];
cu1(-pi/2) q[2], q[3];
h q[3];
c[0] = measure q[0];
c[1] = measure q[1];
c[2] = measure q[2];
c[3] = measure q[3];
