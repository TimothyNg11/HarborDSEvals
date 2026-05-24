#!/bin/bash
set -e
cat > /output/answer.txt <<'EOF'
117.857204
EOF
echo "Oracle wrote: $(cat /output/answer.txt)"
