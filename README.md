# README

## Tutorial 1: Pre-processing, Publishing and Subscribing a CSV (`t01_csv_pub_sub`)

In this first tutorial, we’ll explore how Tabsdata enables Pub/Sub for Tables using a CSV file input.

We will start by setting up Tabsdata and registering a publisher that reads data from a CSV file, selects
some aspects of it, and publishes it as a table within the system. 

Following that, we will register a subscriber that subscribes to this published table, and exports it to the file system in a JSON format.

We will then demonstrate that when the publisher is rerun to load new data, the subscriber automatically writes it to the external system.
