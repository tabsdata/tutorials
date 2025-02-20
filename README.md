In this tutorial, we’ll walk through a simple yet common use case, following these steps:

* Read a raw CSV file, containing some dummy personal details of individuals, from a source system.
* Filter out columns that contain personally identifiable information.
* Push the cleaned data to a destination system.

To achieve this, we will be using a Python IDE and CLI to work with the Tabsdata system and various Tabsdata functions. Let’s dive in!

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
$ git clone https://github.com/tabsdata/tutorial_2
```

Your working directly should have the following files after cloning:

* persons.csv
* publisher.py
* subscriber.py
* README.md



## 3. Save the working directory path in a variable

Since Tabsdata operates at the server level, we are required to give a full system path in our Python code when defining input and output for the Tabsdata functions. Storing our working directory path in an environment variable streamlines that process.

Run this command in your CLI from the working directory, to save the full path to your working directory in the environment variable ``TDX``. I have used this variable in the Python code.

For Linux or MacOS:

```
$ export TDX=`pwd`
```

For Windows:

```
$ set TDX=%CD%
```


# Step 2. Login and Create a Collection

We are required to be logged into the Tabsdata server to interact with the Tabsdata system.

If you are not logged in, use the following command to login to Tabsdata:

```
$ td login localhost --user admin --password tabsdata
```

Collections are logical containers for Tabsdata tables and functions. Hence, before creating any tabsdata functions, we need to create a collection. You can read more about them [here](https://docs.tabsdata.com/latest/guide/03_key_concepts/main.html#collections).

To create a collection called ``tutorial``, run the following command:

```
$ td collection create tutorial
```

**Note**: If you have completed [Getting Started](https://docs.tabsdata.com/latest/guide/02_getting_started/main.html), you would already have a collection called ``tutorial`` in your system and don't need to do this step.


Now that we have created a collection, we’re ready to register a publisher with the collection.


# Step 3. Register the Publisher

A publisher is a type of a Tabsdata function that reads data from an external system and writes the data as one or more Tabsdata tables.

In ``publisher.py`` file in the github repo, we are defining a publisher with the name ``publish_t2`` that reads ``persons.csv`` from local system, drops the columns containing personally identifiable information, and saves the resultant table as ``persons_t2`` in the Tabsdata server.

To run this publisher in Tabsdata, we need to first register it with a collection inside Tabsdata.

Run the following CLI command from your working directory to register ``publish_t2`` publisher with the ``tutorial`` collection:

```
$ td fn register --collection tutorial --fn-path publisher.py::publish_t2
```


# Step 4. Register the Subscriber

A subscriber is a type of a Tabsdata function that reads data from one or more tables in the Tabsdata server and writes them to an external system.

In ``subscriber.py`` we are defining a subscriber with the name ``subscribe_t2`` that reads ``persons_t2`` table from Tabsdata, and writes it as ``persons_t2_output.jsonl`` in the local system.

To run this susbcriber in Tabsdata, we need to first register it with a collection inside Tabsdata.

Run the following CLI command from your working directory to register ``subscribe_t2`` subscriber with the ``tutorial`` collection:

```
$ td fn register --collection tutorial --fn-path subscriber.py::subscribe_t2
```



# Step 5. Trigger the Publisher


A trigger runs a Tabsdata function. Once triggered, a function takes its input data, processes it as defined, and creates a [new commit](https://docs.tabsdata.com/latest/guide/06_working_with_tables/table_frame_1.html#table-commits) for its output data. A new table commit is generated whenever a publisher is successfully executed.

A trigger can be initiated through a CLI command or by a new commit to its associated table. Consequently, changes to their input tables can automatically trigger functions, which in turn change other tables that trigger their associated functions, leading to a cascading workflow of updates. You can read more about triggers [here](https://docs.tabsdata.com/latest/guide/05_working_with_triggers/main.html).

Due to this cascading workflow of updates, when we trigger ``publish_t2``, a new commit for the table ``persons_t2`` is generated inside the Tabsdata server. This in turn triggers the function ``subscribe_t2``, generating the output file ``persons_t2_output.jsonl`` in the local system.

Run the following CLI command to trigger the publisher:

```
$ td fn trigger --collection tutorial --name publish_t2
```

After running the above we would see the output file ``persons_t2_output.jsonl`` in our working directory, containing the data from ``persons.csv`` without the personally identifiable information. The functions make take a couple of seconds to execute.

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

* Make some changes to the ``persons.csv`` file and trigger the publisher again. You should see the changes reflected in ``persons_t2_output.jsonl`` once both the publisher and subscriber have finished executing. 
* Make some changes in the publisher code to modify the columns filtered by the publisher, for example, dropping one more column or one less. After making the changes, trigger the publisher. You should see the changes reflected in ``persons_t2_output.jsonl`` output file.
* Add a Tabsdata [transformer](https://docs.tabsdata.com/latest/guide/04_working_with_functions/working_with_transformers/main.html) in the mix. Perform complex transformations on ``persons_t2`` table using a Tabsdata tranformer, and connect the output table from the transformer to a subscriber.
* Read files from and write files to different external systems beyond local file system. You can read more about them [here](https://docs.tabsdata.com/latest/guide/supported_sources_and_destinations/main.html).


I hope this gave you a good introduction to the Tabsdata system! I'd love to hear your thoughts—let us know how we can improve, what use cases you'd like us to cover in future blogs, or any other questions or feedback you have. Join the conversation on [Discord](https://discord.gg/XRC5XZWppc), [Github Discussions](https://github.com/tabsdata/tabsdata/discussions) or reach out to us [here](https://www.tabsdata.com/contact).