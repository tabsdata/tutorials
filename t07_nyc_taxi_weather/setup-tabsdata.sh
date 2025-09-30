#!/bin/bash
#
# Copyright 2025. Tabs Data Inc.
#
#!/usr/bin/env bash
# set -Eeo pipefail
# trap 'echo "Error on line $LINENO while running: $BASH_COMMAND" >&2; exit 1' ERR


source ../source.sh
if [ "$1" = "aws" ]; then
    destination="aws"
else
    destination="local"
fi

tdserver stop --instance nyc_taxi
echo yes | tdserver delete --instance nyc_taxi
tdserver start --instance nyc_taxi

td login --server ${TD_SERVER} --user ${TD_USER} --password ${TD_PASSWORD} --role ${TD_ROLE}

td collection create --name taxi

echo
echo "Created 1 collection(s)"
echo


(
td fn register --coll taxi --path 01_nyc_taxi_pub.py::nyc_taxi_pub
td fn register --coll taxi --path 02_agg_taxi_metrics_trf.py::agg_taxi_metrics_trf
td fn register --coll taxi --path 03_weather_pub.py::weather_pub
td fn register --coll taxi --path 04_join_weather_trf.py::join_weather_trf
)

echo
echo "Registered the publisher functions"
echo

(
if [ "$destination" = "aws" ]; then
    td fn register --coll taxi --path 05_s3_sub.py::s3_sub
else
    td fn register --coll taxi --path 05_local_sub.py::local_sub
fi
)






