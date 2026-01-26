#!/bin/bash
# Real-time benchmark monitor for Malaya LLM v2

echo "=== Malaya LLM v2 Benchmark Monitor ==="
echo "Press Ctrl+C to stop"
echo ""

while true; do
    STATUS=$(curl -s 'http://localhost:5050/api/benchmark?model=malaya-v2')
    
    MODEL=$(echo "$STATUS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('model', 'N/A'))")
    STATUS_VAL=$(echo "$STATUS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('status', 'unknown'))")
    RUNNING=$(echo "$STATUS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('running', False))")
    COMPLETED=$(echo "$STATUS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('completed', 0))")
    TOTAL=$(echo "$STATUS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('total', 100))")
    SCORE=$(echo "$STATUS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('score', 0))")
    ACCURACY=$(echo "$STATUS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"{d.get('accuracy', 0):.1f}\")")
    ETA=$(echo "$STATUS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('eta_minutes', 0))")
    
    clear
    echo "============================================"
    echo "  Malaya LLM v2 Benchmark Status"
    echo "============================================"
    echo ""
    echo "Model: $MODEL"
    echo "Status: $STATUS_VAL"
    echo "Running: $RUNNING"
    echo ""
    echo "Progress: $COMPLETED / $TOTAL cases"
    if [ "$TOTAL" -gt 0 ]; then
        PERCENT=$(python3 -c "print(f'{($COMPLETED/$TOTAL)*100:.1f}')")
        echo "Completion: ${PERCENT}%"
    fi
    echo ""
    echo "Current Score: $SCORE / $TOTAL"
    echo "Accuracy: ${ACCURACY}%"
    echo ""
    if [ "$ETA" -gt 0 ] && [ "$RUNNING" = "true" ]; then
        echo "ETA: ~${ETA} minutes remaining"
    fi
    echo ""
    echo "============================================"
    echo "Last updated: $(date '+%H:%M:%S')"
    echo "Press Ctrl+C to stop"
    
    sleep 2
done
