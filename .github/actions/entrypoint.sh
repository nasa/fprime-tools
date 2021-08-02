#!/bin/sh -l

echo "Test: $1"
time=$(date)
echo "::set-output name=time::$time"
