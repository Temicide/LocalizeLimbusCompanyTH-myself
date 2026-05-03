#!/bin/bash
# Background commit loop for retranslation progress
# Commits every 5 minutes if there are changes

cd /Users/temicide/Documents/LocalizeLimbusCompanyTH-myself

echo "[$(date)] Starting background commit loop..."

while true; do
    sleep 300
    
    # Add StoryData changes and state
    git add TH/StoryData/ translation_state.json
    
    # Check if there are staged changes
    if ! git diff --cached --quiet; then
        git commit -m "wip: retranslation progress $(date '+%Y-%m-%d %H:%M:%S')"
        echo "[$(date)] Committed progress"
    else
        echo "[$(date)] No changes to commit"
    fi
done
