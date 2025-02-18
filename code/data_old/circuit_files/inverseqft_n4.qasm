OPENQASM 3.0;
include "stdgates.inc";
bit[1] c0;
bit[1] c1;
bit[1] c2;
bit[1] c3;
qubit[4] q;
h q[0];
h q[1];
h q[2];
h q[3];
barrier q[0], q[1], q[2], q[3];
h q[0];
c0[0] = measure q[0];
if (c0 == 1) {
  u1(pi/2) q[1];
}
h q[1];
c1[0] = measure q[1];
if (c0 == 1) {
  u1(pi/4) q[2];
}
if (c1 == 1) {
  u1(pi/2) q[2];
}
h q[2];
c2[0] = measure q[2];
if (c0 == 1) {
  u1(pi/8) q[3];
}
if (c1 == 1) {
  u1(pi/4) q[3];
}
if (c2 == 1) {
  u1(pi/2) q[3];
}
h q[3];
c3[0] = measure q[3];
