#!/usr/bin/env bash

# ==============================================================================
# Script Name : sys_guard.sh
# Description : Node health monitor for storage, memory, and CPU load.
# Author      : Iron Engine Operations
# ==============================================================================

# Strict Bash Mode: fail fast on errors or unset variables
set -euo pipefail

# ---------------- CONFIGURATION & THRESHOLDS ----------------
DISK_THRESHOLD_PERCENT=80
MEM_THRESHOLD_PERCENT=85
PROJECT_ROOT="$HOME/iron-engine"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/sys_guard.log"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Ensure the log directory exists
mkdir -p "$LOG_DIR"

# ---------------- METRIC COLLECTION ----------------
# 1. Disk Usage for root partition (/)
# Extract the 5th column from the 2nd line, then strip the '%' symbol using tr
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')

# 2. Memory Usage calculation
# Extract column 2 (total) and column 3 (used) from the line starting with 'Mem:'
MEM_TOTAL=$(free -m | awk '/^Mem:/ {print $2}')
MEM_USED=$(free -m | awk '/^Mem:/ {print $3}')
MEM_PERCENT=$(( 100 * MEM_USED / MEM_TOTAL ))

# 3. System Load Average (1-minute load)
LOAD_1MIN=$(uptime | awk -F'load average:' '{ print $2 }' | cut -d, -f1 | xargs)

# ---------------- LOGGING FUNCTION ----------------
log_event() {
    local level="$1"
    local message="$2"
    # Write to standard output AND append to the log file
    echo "[$TIMESTAMP] [$level] $message" | tee -a "$LOG_FILE"
}

# ---------------- EVALUATION & ALERTS ----------------
log_event "INFO" "Health Check: Disk=${DISK_USAGE}% | RAM=${MEM_PERCENT}% (${MEM_USED}MB/${MEM_TOTAL}MB) | LoadAvg=${LOAD_1MIN}"

# Check Disk Threshold
if [ "$DISK_USAGE" -ge "$DISK_THRESHOLD_PERCENT" ]; then
    log_event "WARNING" "High Disk Usage: ${DISK_USAGE}% exceeds ${DISK_THRESHOLD_PERCENT}% threshold!"
fi

# Check Memory Threshold
if [ "$MEM_PERCENT" -ge "$MEM_THRESHOLD_PERCENT" ]; then
    log_event "WARNING" "High RAM pressure: ${MEM_PERCENT}% exceeds ${MEM_THRESHOLD_PERCENT}% threshold!"
fi
