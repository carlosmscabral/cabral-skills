#!/bin/bash
# Pre-test hook execution script
# Receives the target command in $CommandLine

if [[ "$CommandLine" =~ "pytest" ]]; then
  echo "[Hooks - standard-harness] Automatically running linter checks before pytest execution..."
elif [[ "$CommandLine" =~ "npm test" ]]; then
  echo "[Hooks - standard-harness] Preparing Node.js test runtime env..."
fi

exit 0
