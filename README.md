# README

In the tutorials below, we show how to make the most of Tabsdata, when working with various sources and destinations. We have shown only specific connectors in the tutorials below. However, in a real-world scenario, your data source could be any other database, or file storage location (cloud or on-prem), and the subscriber could write data to various endpoints such as a database or file system. You can check the list of source and destination connectors in [Tabsdata documentation](https://docs.tabsdata.com/latest/guide/04_01_working_with_publishers/main.html). 

## Tutorial 4: Pre-processing, Publishing and Subscribing a Google Sheet to Neon PostgreSQL (`t04_gsheet_neon`)

In this tutorial, we’ll explore how Tabsdata enables exporting data from Google Sheet to Neon PostgreSQL. We will do the following steps:

* Set up Tabsdata
* Register a publisher to read from Google Sheet, drop some columns from it, and publish the data as a table into Tabsdata.
* Register a subscriber that subscribes to this published table, and writes it to PostgreSQL Table in Neon.


## Tutorial 3: Pre-processing, Publishing and Subscribing a CSV to AWS Glue Iceberg (`t03_csv_icerberg_pub_sub`)

In this tutorial, we’ll explore how Tabsdata enables publishing CSV data from local file system and subscribing as an Iceberg table to AWS. We will do the following steps:

* Set up Tabsdata
* Register a publisher that reads data from a CSV file, selects some aspects of it, and publishes it as a table within Tabsdata.
* Register a subscriber that subscribes to this published table, and exports it as an Iceberg Table to AWS.
* Demonstrate that when the publisher is re-run to load new data, the subscriber automatically writes the new data to AWS.

## Tutorial 2: Publishing and Subscribing a PostgreSQL Table (``t02_postgresql_pub_sub``)

In this tutorial, we’ll explore how Tabsdata enables Pub/Sub for Tables with source and destination data being a locally hosted PostgreSQL database. We will do the following steps:

* Set up Tabsdata
* Register a publisher that reads data from PostgreSQL, and publishes that as a table to Tabsdata.
* Register a subscriber that subscribes to this published table, filters some data, and exports it to PostgreSQL.
* Demonstrate that when the publisher is re-run to load new data, the subscriber automatically writes the new data to PostgreSQL.


## Tutorial 1: Pre-processing, Publishing and Subscribing a CSV (`t01_csv_pub_sub`)

In this first tutorial, we’ll explore how Tabsdata enables Pub/Sub for Tables using a CSV file input. We will do the following steps:

* Set up Tabsdata
* Register a publisher that reads data from a CSV file, selects some aspects of it, and publishes it as a table within the system.
* Register a subscriber that subscribes to this published table, and exports it to the file system in a JSON format.
* Demonstrate that when the publisher is re-run to load new data, the subscriber automatically writes the new data to the CSV in local file system.
