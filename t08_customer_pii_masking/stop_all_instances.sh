#!/bin/bash
#
# Copyright 2025. Tabs Data Inc.


DIRECTORY=$HOME/.tabsdata/instances


for folder in "$DIRECTORY"/*/; do

  if [ -d "$folder" ]; then

    folder_name=$(basename "$folder")
    tdserver stop --instance $folder_name
  fi
done




