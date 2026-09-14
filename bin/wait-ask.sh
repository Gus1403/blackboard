#!/bin/zsh
# Blocks until a new line lands in board/queue.jsonl, prints it, exits 0.
# Run in the background from the agent after every render (Claude Code hosts); the exit re-invokes the agent.
Q=${BLACKBOARD_HOME:-$HOME/.cache/blackboard}/queue.jsonl
touch "$Q"
python3 - "$Q" "${BLACKBOARD_WAIT_TIMEOUT:-3600}" <<'PY'
import os,sys,time
q,timeout=sys.argv[1],float(sys.argv[2])
start=os.path.getsize(q); t0=time.time()
while time.time()-t0<timeout:
    n=os.path.getsize(q)
    if n>start:
        with open(q,'rb') as f:
            f.seek(start); data=f.read(n-start)
        line=data.split(b'\n')[0].decode('utf-8','replace').strip()
        if line:
            print("BOARD REQUEST: "+line); sys.exit(0)
        start=n
    time.sleep(0.3)
print("no board request within timeout"); sys.exit(3)
PY
