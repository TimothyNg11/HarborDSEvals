#!/bin/bash
set -e
cat > /output/answer.txt <<'EOF'
6764.6140
EOF
echo "Oracle wrote: $(cat /output/answer.txt)"
