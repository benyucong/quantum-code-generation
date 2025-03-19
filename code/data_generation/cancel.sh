#!/usr/bin/env bash

JOBID=6313764

for i in {10..127}
do
  echo "Canceling job ${JOBID}_${i}"
  scancel "${JOBID}_${i}"
done