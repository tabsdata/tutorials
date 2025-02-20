In this tutorial, we will walk through a simple and common use case: taking a raw data file, filtering some columns from it, and sharing it with the downstream users. To achieve this, we will be using our respective preferred Python IDE and CLI to work with the Tabsdata system and various Tabsdata functions.

Before we start, here is a brief overview of some key concepts that we’ll be covering in this article:

**A collection** is a logical container for Tabsdata tables and functions. A collection normally defines a domain. For example, all tables and functions related to sales might be grouped into a single collection for easier maintenance and control.

**A publisher** is a type of a Tabsdata function that reads data from an external system and writes the data as one or more Tabsdata tables.

**A subscriber** is a type of a Tabsdata function that reads data from one or more tables in the Tabsdata server and writes them to an external system.

**A trigger** executes a Tabsdata function. Once triggered, a function takes its input data, processes it as defined, and creates the output data.

You can find detailed information on the key concepts in the documentation here. <add hyperlink>

With the context set, let’s dive in!

----

We will be working with a publisher that reads a file ``persons.csv`` from the local file system, drops some columns related to personally identifiable information from it, and writes the resultant data to a Tabsdata table. We will also be working with a subscriber that reads the Tabsdata table created by the publisher and writes it to the local file system.

# Step 1. Pre-requisites

## 1. Install Tabsdata and Start the Server

To install Tabsdata, run the following command in your CLI:

```
$ pip install tabsdata
```

**Important:** Your virtual environment or alternative installation location must have **Python 3.12 or later**.


To start the Tabsdata server, use the following command:

```
$ tdserver start
```


To verify that the Tabsdata server instance is running:

```
$ tdserver status
```


## 2. Copy the github repo

If you haven't already, copy the github repo to the working directory in your system.

```
git clone https://..........
```

Your working directly would have the following files after cloning:

* persons.csv
* publisher.py
* subscriber.py
* README.md



## 3. Save the working directory path in a variable

Since Tabsdata operates at the server level, we are required to give a full system path in our Python code when defining input and output for publishers and subscribers. Storing our working directory path in an environment variable streamlines that process.

Run this command in your CLI from the working directory, to save the full path to your working directory in the environment variable ``TDX``.

```
export TDX=`pwd`
```

# Step 2. Login and Create a Collection

We are required to be logged into the Tabsdata server to interact with the Tabsdata system.

If you are not logged in, use the following command to login to Tabsdata:

```
$ td login localhost --user admin --password tabsdata
```

Collections are logical containers for Tabsdata tables and functions. We use collections to enable different business domains to have their own organizational space. You can read more about them here. <add hyperlink>

**Note**: If you have completed Getting Started<add hyperlink>, then you would already have a collection called ``tutorial`` and don't need to do this step.

To create a collection called ``tutorial``, run the following command:

```
$ td collection create tutorial
```

Now that we have created a collection, we’re ready to implement a publisher.


# Step 3. Register the Publisher

A publisher is a type of a Tabsdata function that reads data from an external system and writes the data as one or more Tabsdata tables.

In ``publisher.py`` we are defining a publisher with the name ``publish_t1`` that reads ``persons.csv`` from local system, drops the columns containing personally identifiable information, and saves the resultant table as ``persons_t1`` in the Tabsdata server.

To run this publisher in Tabsdata, we need to first register it with a collection inside Tabsdata.

Use the following command to register ``publish_t1`` publisher with the ``tutorial`` collection:

```
$ td fn register --collection tutorial --fn-path publisher.py::publish_t1
```


# Step 4. Register the Subscriber

A subscriber is a type of a Tabsdata function that reads data from one or more tables in the Tabsdata server and writes them to an external system.

In ``subscriber.py`` we are defining a subscriber with the name ``subscribe_t1`` that reads ``persons`` table from Tabsdata, and writes it as ``persons_t1_output.jsonl`` in the local system.

To run this susbcriber in Tabsdata, we need to first register it with a collection inside Tabsdata.

Use the following command to register ``subscribe_t1`` subscriber with the ``tutorial`` collection:

```
$ td fn register --collection tutorial --fn-path subscriber.py::subscribe_t1
```



# Step 5. Trigger the Publisher


A trigger executes a Tabsdata function. Once triggered, a function takes its input data, processes it as defined, and creates the output data.

A trigger can be initiated through a CLI command or by a new commit <add hyperlink> to its associated table. Consequently, changes on tables can automatically trigger functions, which in turn change other tables that trigger their assocaited functions, leading to a cascading workflow of updates. You can read more about triggers here. <add hyperlink>

Due to this cascading workflow of updates, when we trigger ``publish_t1``, a new commit for the table ``persons_t1`` is generated inside the Tabsdata server. This in turn triggers the function ``subscribe_t1``, generating an updated output file ``persons_t1_output.jsonl`` in the local system.

Use the following command to trigger the publisher:

```
$ td fn trigger --collection tutorial --name publish_t1
```

After running the above we would see the output file ``persons_t1_output.jsonl`` in our working directory. The functions make take a couple of seconds to execute. 

You can see the status whether the functions have finsihed executing by using the following command:

```
$ td exec list-trxs
```

Sample output:

<<add image>>

**Mission Accomplished!!**

We have successfully created a publisher and a subscriber, registered them with a Tabsdata collection, and triggered the functions successfully.


## Next Steps:

Here are a couple of experiements you can try:

* Make some changes to the ``persons.csv`` file and trigger the publisher again. You should see the changes reflected in ``persons_t1_output.jsonl`` once both the publisher and subscriber have finished executing. 
* Make some changes in the columns filtered by the publisher, for example, dropping one more column or one less, and trigger the publisher. You should see the changes reflected in ``persons_t1_output.jsonl``. 
* Add a Tabsdata transformer <add hyperlink> in the mix. Perform complex transformations on ``persons_t1`` table using a Tabsdata tranformer, and connect the output table from the transformer to a subscriber.
* Read files from and write files to different external systems beyond local file system. You can read more about them here, <add hyperlink>
