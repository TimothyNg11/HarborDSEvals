#!/bin/bash
# Oracle: write the published DABstep dev-split answer to /output/answer.txt.
# Ground truth is supplied as a constant (the model has no access to this
# file when run as gemini-cli).
set -e
cat > /output/answer.txt <<'EOF'
E:13.57
EOF
echo "Oracle wrote answer: $(cat /output/answer.txt | head -c 80)..."
