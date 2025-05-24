# README

In the tutorials below, we show how to make the most of Tabsdata, when working with various sources and destinations. We have shown only specific connectors in the tutorials below. However, in a real-world scenario, your data source could be any other database, or file storage location (cloud or on-prem), and the subscriber could write data to various endpoints such as a database or file system. You can check the list of source and destination connectors in [Tabsdata documentation](https://docs.tabsdata.com/latest/guide/04_01_working_with_publishers/main.html). 

## Tutorial 3: Pre-processing, Publishing and Subscribing a CSV to AWS Glue Iceberg (`t03_csv_icerberg_pub_sub`)

In this tutorial, we’ll explore how Tabsdata enables publishing CSV data from local file system and subscribing as an Iceberg table to AWS.

We will start by setting up Tabsdata and registering a publisher that reads data from a CSV file, selects
some aspects of it, and publishes it as a table within Tabsdata.

Following that, we will register a subscriber that subscribes to this published table, and exports it as an Iceberg Table to AWS. We will then demonstrate
that when the publisher is rerun to load new data, the subscriber automatically writes it to the external system.

## Tutorial 2: Publishing and Subscribing a PostgreSQL Table (``t02_postgresql_pub_sub``)

In this tutorial, we’ll explore how Tabsdata enables Pub/Sub for Tables with source and destination data being a locally hosted PostgreSQL database.

We will start by setting up Tabsdata, and PostgreSQL. Then we register and run a publisher that reads data from PostgreSQL, and publishes that as a table to Tabsdata. 

Following that, we will register a subscriber that subscribes to this published table, filters some data, and exports it to PostgreSQL. We will then demonstrate that when the publisher is re-run to load new data, the subscriber automatically writes it to Postgres.


## Tutorial 1: Pre-processing, Publishing and Subscribing a CSV (`t01_csv_pub_sub`)

In this first tutorial, we’ll explore how Tabsdata enables Pub/Sub for Tables using a CSV file input.

We will start by setting up Tabsdata and registering a publisher that reads data from a CSV file, selects
some aspects of it, and publishes it as a table within the system. 

Following that, we will register a subscriber that subscribes to this published table, and exports it to the file system in a JSON format.

We will then demonstrate that when the publisher is rerun to load new data, the subscriber automatically writes it to the external system.
