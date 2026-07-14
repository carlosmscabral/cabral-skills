#!/bin/bash
# Command blocker hook script
# Receives the target command in $CommandLine

if [[ "$CommandLine" =~ "curl" || "$CommandLine" =~ "wget" ]]; then
  echo -e "\n\033[91m[Hooks - SECURE BANKING] Blocked command: '$CommandLine'\033[0m" >&2
  echo -e "\033[91mDownloading external files or binaries is strictly prohibited in our regulated banking environment.\033[0m\n" >&2
  exit 1
fi

exit 0
