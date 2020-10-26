#!/bin/bash

directories=(
    "/home/backups/thinBackups"
    "/home/backups/icinga"
)

for dir in "${directories[@]}"
do
    cd $dir
    ls -t | tail -n +11 | grep "tar" | xargs rm
done
