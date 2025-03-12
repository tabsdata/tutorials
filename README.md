# README

## Tutorial 1: Pre-processing, Publishing and Subscribing a CSV (`t01_csv_pub_sub`)

In this first tutorial, we’ll explore how Tabsdata enables Pub/Sub for Tables.

We'll start by setting up the system and creating a publisher that reads data from a CSV file called `customers.csv`
stored in an input directory in the local file system, and selects certain columns of interest from it. This data will
be published as a table called `CUSTOMER_LEADS` within a collection called `CUSTOMERS` in the Tabsdata system.

Next, we'll configure a subscriber to read data from this table and write it to an output directory on the local file
system.

Finally, we'll implement automated data engineering using Tabsdata to streamline the propagation of changes in the
input files to downstream users.
