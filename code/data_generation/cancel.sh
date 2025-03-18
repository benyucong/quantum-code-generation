#!/usr/bin/env bash

JOBID=6293961

for i in {10..127}
do
  echo "Canceling job ${JOBID}_${i}"
  scancel "${JOBID}_${i}"
done