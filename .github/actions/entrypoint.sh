#!/bin/sh -l

echo "Test: $1"
completed = $(True)
echo "::set-output name=completed::$completed"