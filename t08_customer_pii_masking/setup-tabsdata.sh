#!/bin/bash
#
# Copyright 2025. Tabs Data Inc.
#
#!/usr/bin/env bash

source ../source.sh
if [ "$1" = "aws" ]; then
    destination="aws"
else
    destination="local"
fi

tdserver stop --instance pii
echo yes | tdserver delete --instance pii
tdserver start --instance pii

td login --server ${TD_SERVER} --user ${TD_USER} --password ${TD_PASSWORD} --role ${TD_ROLE}

td collection create --name pii

echo
echo "Created 1 collection(s)"
echo

#loading data into mysql
(
td fn register --coll pii --path 00_mysql_setup_pub.py::mysql_setup_pub
td fn register --coll pii --path 00_mysql_setup_sub.py::mysql_setup_sub
td fn trigger --coll pii --name mysql_setup_pub 
echo delete | td fn delete --coll pii --name mysql_setup_pub
echo delete | td fn delete --coll pii --name mysql_setup_sub
echo delete | td table delete --coll pii --name input_data
)

echo
echo "Loaded Data into MySQL"
echo

#register publisher and transformer
(
td fn register --coll pii --path 01_mysql_pub.py::mysql_pub
td fn register --coll pii --path 02_mask_trf.py::mask_trf
)

echo
echo "Registered Publishers and Transformers"
echo

#register aws subscriber
(
if [ "$destination" = "aws" ]; then
    td fn register --coll pii --path 03_s3_sub.py::s3_sub
else
    echo "Skipping AWS Subscriber"
fi
)

#register mysql subscriber
td fn register --coll pii --path 04_mysql_sub.py::mysql_sub






