#!/bin/bash
# Oracle: write the published DABstep answer to /output/answer.txt.
set -e
cat > /output/answer.txt <<'EOF'

EOF
echo "Oracle wrote answer: $(cat /output/answer.txt | head -c 80)..."
