# README

In the tutorials below, we show how to make the most of Tabsdata, when working with various sources and destinations. We have shown only specific connectors in the tutorials below. However, in a real-world scenario, your data source could be any other database, or file storage location (cloud or on-prem), and the subscriber could write data to various endpoints such as a database or file system. You can check the list of source and destination connectors in [Tabsdata documentation](https://docs.tabsdata.com/latest/guide/04_01_working_with_publishers/main.html). 

## Tutorial 10: Sessionizing E-commerce Log Data (`t10_sessionizing_ecommerce_data`)

In this tutorial, we'll explore how Tabsdata enables stitching multiple event streams into shopper sessions and publishing the results downstream. We will do the following steps:

* Set up Tabsdata and (optionally) Snowflake credentials
* Register a publisher that parses web, cart, and purchase logs with Grok patterns
* Register transformers that unify batches, append history, sessionize users, and aggregate session metrics
* Register an optional subscriber that writes `sessionized_logs` and `aggregated_sessions` to Snowflake
* Trigger the workflow and inspect the sessionized outputs

## Tutorial 9: Publishing and Subscribing Salesforce Reports (`t09_salesforce_report_ingestion`)

In this tutorial, we’ll explore how Tabsdata enables querying Salesforce Reports and subscribing them anywhere. We will do the following steps:

* Set up Tabsdata along with Snowflake and Salesforce credentials
* Register a publisher that pulls data from a Salesforce report
* Register transformers to reshape the report output for subscribers
* Register subscribers that deliver the report data to Snowflake or local storage
* Demonstrate that when the publisher is re-run, the subscriber automatically writes the refreshed data

## Tutorial 8: Masking and Subscribing Customer Data with Tabsdata (`t08_customer_pii_masking`)

In this tutorial, we’ll explore how Tabsdata enables masking and redacting PII before sharing customer datasets. We will do the following steps:

* Set up Tabsdata with AWS and MySQL credentials
* Register a publisher that ingests customer data from MySQL
* Register transformers that mask and redact PII fields
* Register subscribers that publish the sanitized data to AWS Glue or back to MySQL
* Demonstrate that when the publisher is re-run, the subscriber automatically writes the masked data

## Tutorial 7: Publishing and Subscribing NYC Taxi Data into AWS Glue (`t07_nyc_taxi_weather`)

In this tutorial, we’ll explore how Tabsdata enables ingesting external data sources and enriching them for downstream use. We will do the following steps:

* Set up Tabsdata with AWS credentials
* Register publishers that ingest NYC Taxi trips and historical weather data
* Register transformers that aggregate daily trip metrics and enrich them with weather attributes
* Register subscribers that write the enriched metrics to AWS Glue and S3
* Demonstrate that when the publisher is re-run, the subscriber automatically writes the refreshed data

## Tutorial 6: Ingesting Insurance Claim Data from Gmail into Databricks (`t06_bordeaux_gmail_extract`)

In this tutorial, we’ll explore how Tabsdata enables collecting emailed claim files, enriching them, and publishing to Databricks. We will do the following steps:

* Set up Tabsdata along with Gmail, MySQL, and Databricks credentials
* Register a publisher that fetches claim bordereaux attachments from Gmail
* Register transformers that merge claims into a master fact, enrich with policy data, and flag high-value subsets
* Register subscribers that deliver the curated claims to Databricks
* Demonstrate that when the publisher is re-run, the subscriber automatically writes the refreshed data

## Tutorial 5: Publishing, Transforming, and Subscribing a CDC Stream from Oracle into PostgreSQL and S3 (`t05_oracle_cdc`)

In this tutorial, we'll explore how Tabsdata enables generating a CDC stream from a table in Oracle and subscribe that CDC stream to AWS Iceberg and PostgreSQL. We will do the following steps:

* Set up an Oracle Database in a Docker container
* Set up Tabsdata
* Register a publisher function to read customer data from an Oracle table
* Register a transformer function to capture data changes and store the CDC stream in a new table
* Register subscriber functions to deliver the CDC stream and customer table to PostgreSQL and AWS Iceberg


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
