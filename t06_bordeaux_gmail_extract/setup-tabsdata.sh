#!/bin/bash
#
# Copyright 2025. Tabs Data Inc.
#
#!/usr/bin/env bash

source ../source.sh
if [ "$1" = "databricks" ]; then
    destination="databricks"
else
    destination="local"
fi

tdserver stop --instance insurance
echo yes | tdserver delete --instance insurance
tdserver start --instance insurance

td login --server ${TD_SERVER} --user ${TD_USER} --password ${TD_PASSWORD} --role ${TD_ROLE}

td collection create --name claim_processing

#register publisher and local subscriber
td fn register --coll claim_processing --path 01_claim_fact_pub.py::claim_fact_pub
td fn register --coll claim_processing --path 03_policy_dim_pub.py::policy_dim_pub
td fn register --coll claim_processing --path 02_append_claims_today_to_master_trf.py::append_claims_today_to_master_trf
td fn register --coll claim_processing --path 04_master_fact_trf.py::master_fact_trf
td fn register --coll claim_processing --path 05_master_categorize_trf.py::master_categorize_trf
td fn register --coll claim_processing --path 07_local_sub.py::local_sub


#register databricks subscriber
(
if [ "$destination" = "databricks" ]; then
    td fn register --coll claim_processing --path 06_databricks_sub.py::databricks_sub
else
    echo "Skipping databricks Subscriber"
fi
)

td fn trigger --coll claim_processing --name claim_fact_pub





