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
bit[4] c;
qubit[2] q;
h q[0];
ctu q[0], q[1];
ctu q[0], q[1];
ctu q[0], q[1];
ctu q[0], q[1];
ctu q[0], q[1];
ctu q[0], q[1];
ctu q[0], q[1];
ctu q[0], q[1];
h q[0];
c[0] = measure q[0];
reset q[0];
h q[0];
ctu q[0], q[1];
ctu q[0], q[1];
ctu q[0], q[1];
ctu q[0], q[1];
if (c == 1) {
  u1(-pi/2) q[0];
}
h q[0];
c[1] = measure q[0];
reset q[0];
h q[0];
ctu q[0], q[1];
ctu q[0], q[1];
if (c == 1) {
  u1(-pi/4) q[0];
}
if (c == 2) {
  u1(-pi/2) q[0];
}
if (c == 3) {
  u1(-3*pi/4) q[0];
}
h q[0];
c[2] = measure q[0];
reset q[0];
h q[0];
ctu q[0], q[1];
if (c == 1) {
  u1(-pi/8) q[0];
}
if (c == 2) {
  u1(-pi/4) q[0];
}
if (c == 3) {
  u1(-3*pi/8) q[0];
}
if (c == 4) {
  u1(-pi/2) q[0];
}
if (c == 5) {
  u1(-5*pi/8) q[0];
}
if (c == 6) {
  u1(-3*pi/4) q[0];
}
if (c == 7) {
  u1(-7*pi/8) q[0];
}
h q[0];
c[3] = measure q[0];
