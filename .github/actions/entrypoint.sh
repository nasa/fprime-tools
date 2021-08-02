#!/bin/sh -l

echo "Test: $INPUT_TEST"
time=$(date)
echo "::set-output name=OUTPUTS_TIME::$time"
