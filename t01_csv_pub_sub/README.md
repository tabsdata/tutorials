In this tutorial, we’ll walk through a simple yet common use case, following these steps:

* Read a raw CSV file, containing some dummy personal details of individuals, from a source system.
* Filter out columns that contain personally identifiable information.
* Push the cleaned data to a destination system.

To achieve this, we will be using a Python IDE and CLI to work with the Tabsdata system and various Tabsdata functions.

Through this article you will understand how Tabsdata can help you

* connect with external systems with ease through our built-in connectors, and
* process data as tables when defining Tabsdata functions.

Let’s dive in! We’ll start with setting up the system to prepare us to work with the Tabsdata functions.

# Step 1. Setting up the system

## 1. Install Tabsdata

To install Tabsdata, run the following command in your CLI:

```
$ pip install tabsdata
```

**Important:** Your virtual environment or alternative installation location must have **Python 3.12 or later**.

## 2. Start the Tabsdata Server

To start the Tabsdata server, use the following command:

```
$ tdserver start
```


To verify that the Tabsdata server instance is running:

```
$ tdserver status
```


## 3. Copy the github repo

If you haven't already, copy the github repo to the working directory in your system.

```
$ git clone https://github.com/tabsdata/tutorials
```

Your working directly should have the ``tutorials`` folder containing ``tutorial_1`` folder that has README, CSV and python files.

## 4. Save the directory path of ``tutorial_1`` in an environment variable

Since Tabsdata operates at the server level, you are required to give a full system path in your Python code when defining input and output for the Tabsdata functions. Storing our working directory path in an environment variable streamlines that process.

Open ``tutorial_1`` folder in your CLI and save the full path this folder in the environment variable ``TDX``.

For Linux or MacOS:

```
cd tutorials
cd tutorial_1
$ export TDX=`pwd`
```

For Windows:

```
cd tutorials
cd tutorial_1
$ set TDX=%CD%
```

## 5. Login to the Tabsdata server

You are required to login to the Tabsdata server to interact with the Tabsdata system.

To login to the server, run the following command in your CLI:

```
$ td login localhost --user admin --password tabsdata
```


# Step 2. Create a Collection

Collections are logical containers for Tabsdata tables and functions. Hence, before creating any tabsdata functions, we need to create a collection. You can read more about them [here](https://docs.tabsdata.com/latest/guide/03_key_concepts/main.html#collections).

To create a collection called ``tutorial``, run the following command:

```
$ td collection create tutorial
```

**Note**: If you have completed [Getting Started](https://docs.tabsdata.com/latest/guide/02_getting_started/main.html), you would already have a collection called ``tutorial`` in your system and don't need to do this step.


Now that we have created a collection, we’re ready to register a publisher with the collection.


# Step 3. Register the Publisher

A publisher is a type of a Tabsdata function that reads data from an external system and writes the data as one or more Tabsdata tables. You need a publisher to read the persons.csv file from your source, which is the local file system in this example, into the Tabsdata collection.

In ``publisher.py`` file in the github repo, we are defining a publisher with the name ``publish_t1`` that reads ``persons.csv`` from local system, drops the columns containing personally identifiable information, and saves the resultant table as ``persons_t1`` in the Tabsdata server.

The publisher code is divided in two parts: decorator and the decorated function

**Decorator**

This part of the code defines the input and output of the publisher.

```
@td.publisher(
    # Absolute system path to the file to be imported by the Publisher.
    source = td.LocalFileSource(os.path.join(os.getenv("TDX"), "persons.csv")),

    # Name of the table created in the Tabsdata collection.
    tables = ["persons_t1"],
)
```
**source** parameter defines the path to the file to be imported by the publisher. LocalFileSource is the built-in Tabsdata connector to read data from Local File System. Tabsdata has similar connectors for other file storage systems, such as AWS and Azure, and databases, such as MySQL, MariaDB, Oracle, and, Postgres. You can read more about them in the [documentation](https://docs.tabsdata.com/latest/guide/04_working_with_functions/working_with_publishers/reading_from_file_storage/main.html).

**tables** parameter defines the names of tables created in the Tabsdata collection. The table names are required to be unique within a Tabsdata collection.

**Decorated Function**

This part of the code defines how the publisher should process the data.

```
def publish_t1(tf:td.TableFrame):
    
    # Drop columns from the input file before publishing to Tabsdata.
    tf = tf.drop("name","surname","first_name","last_name","full_name","phone_number","telephone","email")

    return tf

```
In this example, we drop the columns related to personally identifiable information, before publishing the data to Tabsdata. Dropping columns is one of the many operations supported on the tables. Many projections, filters, aggregation, and join functions are also supported. Full list can be found in the [documentation](https://docs.tabsdata.com/latest/guide/06_working_with_tables/table_frame_1.html#table-operations).

The publisher name ``publish_t1`` is also defined here. The function names are required to be unique within a Tabsdata collection.

To run this publisher in Tabsdata, we need to first register it with a collection inside Tabsdata.

Run the following CLI command from your working directory to register ``publish_t1`` publisher with the ``tutorial`` collection:

```
$ td fn register --collection tutorial --fn-path publisher.py::publish_t1
```


# Step 4. Register the Subscriber

A subscriber is a type of a Tabsdata function that reads data from one or more tables in the Tabsdata server and writes them to an external system.

In ``subscriber.py`` we are defining a subscriber with the name ``subscribe_t1`` that reads ``persons_t1`` table from Tabsdata, and writes it as ``persons_t1_output.jsonl`` in the local system.

The subscriber code is divided in two parts: decorator and the decorated function

**Decorator**

The subscriber code is divided in two parts: decorator and the decorated function

```
@td.subscriber(
    # Name of the table to be exported from Tabsdata.
    tables = ["persons_t1"],

    # Absolute system path to the file to be written by the Subscriber.
    destination = td.LocalFileDestination(os.path.join(os.getenv("TDX"), "persons_t1_output.jsonl")), 
)
```

**tables** parameter defines the tables to be read by the subscriber. They can be from any collection in the Tabsdata system. To read tables from outside the collection that the subscriber is going to be registered in, use the syntax "<collection_name>/<input_table_2>".

**destination** parameter defines the path to the folder, the file name, and the file format, to be written by the subscriber. LocalFileDestination is the built-in Tabsdata connector to write data to Local File System. Tabsdata has similar connectors for other file storage systems, such as AWS and Azure, and databases, such as MySQL, MariaDB, Oracle, and, Postgres. You can read more about them in the [documentation](https://docs.tabsdata.com/latest/guide/04_working_with_functions/working_with_subscribers/writing_to_file_storage/main.html).

**Decorated Function:**

This part of the code defines how the subscriber should process the data.

```
def subscribe_t1(persons_t1: td.TableFrame):
    return persons_t1
```

In this example, we are not performing any processing with the subscriber. However, you can perform all table operations inside the subscriber as well. Full list of all the supported operations can be found in the [documentation](https://docs.tabsdata.com/latest/guide/06_working_with_tables/table_frame_1.html#table-operations).

The subscriber name subscribe_t1 is also defined here. The function names are required to be unique within a Tabsdata collection.


To run this susbcriber in Tabsdata, we need to first register it with a collection inside Tabsdata.

Run the following CLI command from your working directory to register ``subscribe_t1`` subscriber with the ``tutorial`` collection:

```
$ td fn register --collection tutorial --fn-path subscriber.py::subscribe_t1
```


# Step 5. Trigger the Publisher


A trigger runs a Tabsdata function. Once triggered, a function takes its input data, processes it as defined, and creates a [new commit](https://docs.tabsdata.com/latest/guide/06_working_with_tables/table_frame_1.html#table-commits) for its output data. A new table commit is generated whenever a publisher is successfully executed.

A trigger can be initiated through a CLI command or by a new commit to its associated table. Consequently, changes to their input tables can automatically trigger functions, which in turn change other tables that trigger their associated functions, leading to a cascading workflow of updates. You can read more about triggers [here](https://docs.tabsdata.com/latest/guide/05_working_with_triggers/main.html).

Due to this cascading workflow of updates, when you trigger ``publish_t1``, a new commit for the table ``persons_t1`` is generated inside the Tabsdata server. This in turn triggers the function ``subscribe_t1``, generating the output file ``persons_t1_output.jsonl`` in the local system.

Run the following CLI command to trigger the publisher:

```
$ td fn trigger --collection tutorial --name publish_t1
```

After running the above you would see the output file ``persons_t1_output.jsonl`` in our working directory, containing the data from ``persons.csv`` without the personally identifiable information. The functions make take a couple of seconds to execute.

You can see the status whether the functions have finsihed executing by using the following command:

```
$ td exec list-trxs
```

Sample output:

![Sample output for execution list](https://docs.tabsdata.com/latest/_images/transf_trx.png)

**Mission Accomplished!!**

We have successfully created a publisher and a subscriber, registered them with a Tabsdata collection, triggered the functions successfully, and verified the output.


## Next Steps:

For the next step, here are a couple of experiements you can try:

* Make some changes to the ``persons.csv`` file and trigger the publisher again. You should see the changes reflected in ``persons_t1_output.jsonl`` once both the publisher and subscriber have finished executing. 
* Make some changes in the publisher code to modify the columns filtered by the publisher, for example, dropping one more column or one less. After making the changes, trigger the publisher. You should see the changes reflected in ``persons_t1_output.jsonl`` output file.
* Add a Tabsdata [transformer](https://docs.tabsdata.com/latest/guide/04_working_with_functions/working_with_transformers/main.html) in the mix. Perform complex transformations on ``persons_t1`` table using a Tabsdata tranformer, and connect the output table from the transformer to a subscriber.
* Read files from and write files to different external systems beyond local file system. You can read more about them [here](https://docs.tabsdata.com/latest/guide/supported_sources_and_destinations/main.html).


I hope this gave you a good introduction to the Tabsdata system! I'd love to hear your thoughts—let us know how we can improve, what use cases you'd like us to cover in future blogs, or any other questions or feedback you have. Join the conversation on [Discord](https://discord.gg/XRC5XZWppc), [Github Discussions](https://github.com/tabsdata/tabsdata/discussions) or reach out to us [here](https://www.tabsdata.com/contact).