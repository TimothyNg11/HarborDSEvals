#!/bin/bash
set -e
cat > /output/answer.txt <<'EOF'
+6690.646000
EOF
echo "Oracle wrote: $(cat /output/answer.txt)"
