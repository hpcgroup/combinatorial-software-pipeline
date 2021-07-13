#!/bin/bash

function timestamp {
    date +"%Y-%m-%dT%H:%M:%S"
}

function diff_hours {
    difference=$(( $(date -d "$2" "+%s") - $(date -d "$1" "+%s") ))
    echo "scale=4 ; ${difference}/3600" | bc
}


function diff_minutes {
    difference=$(( $(date -d "$2" "+%s") - $(date -d "$1" "+%s") ))
    echo "scale=4 ; ${difference}/60" | bc
}

