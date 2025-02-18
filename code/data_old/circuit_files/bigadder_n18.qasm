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
gate add4 _gate_q_0, _gate_q_1, _gate_q_2, _gate_q_3, _gate_q_4, _gate_q_5, _gate_q_6, _gate_q_7, _gate_q_8, _gate_q_9 {
  majority _gate_q_8, _gate_q_4, _gate_q_0;
  majority _gate_q_0, _gate_q_5, _gate_q_1;
  majority _gate_q_1, _gate_q_6, _gate_q_2;
  majority _gate_q_2, _gate_q_7, _gate_q_3;
  cx _gate_q_3, _gate_q_9;
  unmaj _gate_q_2, _gate_q_7, _gate_q_3;
  unmaj _gate_q_1, _gate_q_6, _gate_q_2;
  unmaj _gate_q_0, _gate_q_5, _gate_q_1;
  unmaj _gate_q_8, _gate_q_4, _gate_q_0;
}
bit[8] ans;
bit[1] carryout;
qubit[2] carry;
qubit[8] a;
qubit[8] b;
x a[0];
x b[0];
x b[1];
x b[2];
x b[3];
x b[4];
x b[5];
x b[6];
x b[7];
x b[6];
add4 a[0], a[1], a[2], a[3], b[0], b[1], b[2], b[3], carry[0], carry[1];
add4 a[4], a[5], a[6], a[7], b[4], b[5], b[6], b[7], carry[1], carry[0];
ans[0] = measure b[0];
ans[1] = measure b[1];
ans[2] = measure b[2];
ans[3] = measure b[3];
ans[4] = measure b[4];
ans[5] = measure b[5];
ans[6] = measure b[6];
ans[7] = measure b[7];
carryout[0] = measure carry[0];
