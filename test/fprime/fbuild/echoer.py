#!/usr/bin/env python
"""Fake CMake script for testing purposes

This script can be added to the front of the path to echo what arguments are sent to CMake allowing for tests that are
slightly closer to integration tests without involving the entirety of F Prime.
"""
import sys
import os
from pathlib import Path
import json

if __name__ == "__main__":
    print("[INFO] Running echoer program (stdout)")
    print("[INFO] Running echoer program (stderr)", file=sys.stderr)
    executable_path = Path(sys.argv[0])
    for i in range(0, 100):
        output_file_path = (
            executable_path.parent / f"faux-{executable_path.name}-{i}.json"
        )
        if not output_file_path.exists():
            with open(output_file_path, "w") as output_file:
                json.dump(
                    {
                        "arguments": sys.argv,
                        "cwd": str(Path.cwd()),
                        "environment": dict(os.environ),
                    },
                    output_file,
                )
                break
    else:
        print(
            f"[ERROR] Too many invocations of: {executable_path.name}", file=sys.stderr
        )
        sys.exit(1)
    sys.exit(0)
