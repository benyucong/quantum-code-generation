#!/usr/bin/env bash

JOBID=6448965

for i in {35..299}
do
  echo "Canceling job ${JOBID}_${i}"
  scancel "${JOBID}_${i}"
done