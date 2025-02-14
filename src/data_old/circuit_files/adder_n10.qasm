OPENQASM 3.0;
include "stdgates.inc";
gate majority _gate_q_0, _gate_q_1, _gate_q_2 {
  cx _gate_q_2, _gate_q_1;
  cx _gate_q_2, _gate_q_0;
  ccx _gate_q_0, _gate_q_1, _gate_q_2;
}
gate unmaj _gate_q_0, _gate_q_1, _gate_q_2 {
  ccx _gate_q_0, _gate_q_1, _gate_q_2;
  cx _gate_q_2, _gate_q_0;
  cx _gate_q_0, _gate_q_1;
}
bit[5] ans;
qubit[1] cin;
qubit[4] a;
qubit[4] b;
qubit[1] cout;
x a[0];
x b[0];
x b[1];
x b[2];
x b[3];
majority cin[0], b[0], a[0];
majority a[0], b[1], a[1];
majority a[1], b[2], a[2];
majority a[2], b[3], a[3];
cx a[3], cout[0];
unmaj a[2], b[3], a[3];
unmaj a[1], b[2], a[2];
unmaj a[0], b[1], a[1];
unmaj cin[0], b[0], a[0];
ans[0] = measure b[0];
ans[1] = measure b[1];
ans[2] = measure b[2];
ans[3] = measure b[3];
ans[4] = measure cout[0];
