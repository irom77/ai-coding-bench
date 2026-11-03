#!/usr/bin/env bash
# Template for agents you can trigger from outside but not run as a normal CLI
# (e.g. an internal VS Code extension that watches a file or exposes a local API).
#
#   python3 run.py --name my-ext --note "my-ext v1.4, model X" \
#       --agent "$PWD/agents/ide_trigger_example.sh {workdir} {prompt_file}"
#
# Contract with run.py: start the agent on WORKDIR with the prompt, then BLOCK until the
# agent is finished, then exit. run.py grades as soon as this script exits, and kills it
# after --timeout. Anything printed here goes to agent.log.
set -euo pipefail
WORKDIR="$1"
PROMPT_FILE="$2"

# --- 1. trigger the agent (pick whatever your extension supports) -----------------------
# a) file handshake: the extension watches the workspace for a request file
#      code --new-window "$WORKDIR"
#      cp "$PROMPT_FILE" "$WORKDIR/.agent-request"
# b) local HTTP API:
#      curl -sf -X POST localhost:7777/run \
#        --data-binary @"$PROMPT_FILE" -H "X-Workdir: $WORKDIR"
echo "edit $0 to trigger your agent" >&2; exit 1

# --- 2. wait for it to signal completion ------------------------------------------------
# Keep request/status files out of git's view or delete them before exiting, otherwise
# they count toward the diff size.
#   while [ ! -f "$WORKDIR/.agent-done" ]; do sleep 2; done
#   rm -f "$WORKDIR/.agent-request" "$WORKDIR/.agent-done"
