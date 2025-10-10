#!/bin/bash
#
# Copyright 2025. Tabs Data Inc.
#
#!/usr/bin/env bash

source ../source.sh
if [ "$1" = "snowflake" ]; then
    destination="snowflake"
else
    destination="local"
fi

instance="salesforce"

tdserver stop --instance $instance
echo yes | tdserver delete --instance $instance
tdserver start --instance $instance

td login --server ${TD_SERVER} --user ${TD_USER} --password ${TD_PASSWORD} --role ${TD_ROLE}

td collection create --name salesforce



#register publisher and local subscriber
td fn register --coll salesforce --path 01_salesforce_pub.py::salesforce_pub
td fn register --coll salesforce --path 03_local_sub.py::local_sub



#register aws subscriber
(
if [ "$destination" = "snowflake" ]; then
    td fn register --coll salesforce --path 02_snowflake_sub.py::snowflake_sub
else
    echo "Skipping Snowflake Subscriber"
fi
)

td fn trigger --coll salesforce --name salesforce_pub





