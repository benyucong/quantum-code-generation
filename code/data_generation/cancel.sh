#!/usr/bin/env bash

JOBID=6371865

for i in {30..127}
do
  echo "Canceling job ${JOBID}_${i}"
  scancel "${JOBID}_${i}"
done