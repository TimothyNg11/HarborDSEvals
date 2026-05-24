#!/bin/bash
# Oracle: write the published DABstep dev-split answer to /output/answer.txt.
# Ground truth is supplied as a constant (the model has no access to this
# file when run as gemini-cli).
set -e
cat > /output/answer.txt <<'EOF'
384, 394, 276, 150, 536, 286, 163, 36, 680, 939, 428, 813, 556, 51, 53, 572, 960, 64, 709, 454, 595, 725, 473, 347, 477, 608, 868, 741, 231, 107, 626, 249, 123, 381
EOF
echo "Oracle wrote answer: $(cat /output/answer.txt | head -c 80)..."
