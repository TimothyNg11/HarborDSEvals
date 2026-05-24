#!/bin/bash
set -e
cat > /output/answer.txt <<'EOF'
+6177.500620
EOF
echo "Oracle wrote: $(cat /output/answer.txt)"
