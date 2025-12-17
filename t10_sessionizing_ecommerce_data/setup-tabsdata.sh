#!/bin/bash
#
# Copyright 2025. Tabs Data Inc.
#
#!/usr/bin/env bash

source ../source.sh
destination=${1:-local}

instance="session_analysis"
collection="session_analysis"

# Reset the tutorial instance to ensure a clean slate
tdserver stop --instance "${instance}"
tdserver delete --instance "${instance}" --force 
tdserver start --instance "${instance}"

td login --server "${TD_SERVER}" --user "${TD_USER}" --password "${TD_PASSWORD}" --role "${TD_ROLE}"

# Create (or recreate) the collection
td collection create --name "${collection}"

# Register publisher and transformers
td fn register --coll "${collection}" --path 01_publish_logs.py::publish_logs
td fn register --coll "${collection}" --path 02_create_unified_log.py::create_unified_log
td fn register --coll "${collection}" --path 03_sessionize_log_data.py::sessionize_log_data
td fn register --coll "${collection}" --path 04_aggregate_sessions.py::aggregate_sessions

# Register the Snowflake subscriber only if requested
if [ "${destination}" = "snowflake" ]; then
    td fn register --coll "${collection}" --path 05_subscribe_sessions_snowflake.py::subscribe_sessions
else
    echo "Skipping Snowflake subscriber registration (local-only run)."
fi

# Kick off the workflow
td fn trigger --coll "${collection}" --name publish_logs
