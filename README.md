# README

## Tutorial 1: Hello Pub/Sub for Tables

This first tutorial sets the ground by introducing Pub/Sub for Tables. We create the following Tabsdata functions:

**Publisher:**

* To read a raw CSV file, containing some dummy personal details of individuals, from a source system.
* To filter out columns containing personally identifiable information, before pushing to the Tabsdata system.

**Subscriber:**

* To push the cleaned data to a destination system.
