#!/bin/bash
set -e
cat > /output/answer.txt <<'EOF'
NexPay:0.140395
EOF
echo "Oracle wrote: $(cat /output/answer.txt)"
