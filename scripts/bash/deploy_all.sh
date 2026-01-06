#!/bin/bash
# Batch Deploy Script
# Executes all deploy_*.sh scripts in the current directory

echo "========================================="
echo "Robotools Plugin Batch Deployment"
echo "========================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Count total scripts
TOTAL=$(ls -1 "$SCRIPT_DIR"/deploy_*.sh 2>/dev/null | grep -v deploy_all.sh | wc -l | tr -d ' ')

if [ "$TOTAL" -eq 0 ]; then
    echo "No deploy_*.sh scripts found in $SCRIPT_DIR"
    exit 0
fi

echo "Found $TOTAL deployment script(s)"
echo ""

# Counter for tracking
SUCCESS=0
FAILED=0
CURRENT=0

# Loop through all deploy_*.sh files (excluding this script)
for script in "$SCRIPT_DIR"/deploy_*.sh; do
    # Skip if it's this batch script itself
    if [[ "$(basename "$script")" == "deploy_all.sh" ]]; then
        continue
    fi
    
    CURRENT=$((CURRENT + 1))
    SCRIPT_NAME=$(basename "$script")
    
    echo "[$CURRENT/$TOTAL] Running: $SCRIPT_NAME"
    echo "-----------------------------------------"
    
    # Make sure the script is executable
    chmod +x "$script"
    
    # Execute the script
    if bash "$script"; then
        echo "✓ $SCRIPT_NAME completed successfully"
        SUCCESS=$((SUCCESS + 1))
    else
        echo "✗ $SCRIPT_NAME failed"
        FAILED=$((FAILED + 1))
    fi
    
    echo ""
done

echo "========================================="
echo "Batch Deployment Complete"
echo "========================================="
echo "Total: $TOTAL | Success: $SUCCESS | Failed: $FAILED"
echo ""
