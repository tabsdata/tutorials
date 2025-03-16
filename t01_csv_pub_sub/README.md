# Tutorial 1: Pre-processing, Publishing and Subscribing a CSV (`t01_csv_pub_sub`)

In this tutorial, we’ll explore how Tabsdata enables Pub/Sub for Tables.

We will start by setting up Tabsdata and registering a publisher that reads data from a CSV file, selects
some aspects of it, and publishes it as a table within the system. Following that, we will register a subscriber that
subscribes to this published table, and exports it to the file system in a JSON format. We will then demonstrate
that when the publisher is rerun to load new data, the subscriber automatically writes it to the external system.

In a real-world scenario, your data source could be a database, an S3 bucket, or another storage location, while the 
subscriber could write data to various endpoints such as a database or file system.

Let’s dive in!

## Step 1. Setting up the system

### 1.1 Install/Update Tabsdata

To install/update the Tabsdata Python package, run this command in your CLI:

```
pip install tabsdata --upgrade
```

Please note that you need **Python 3.12 or later**, to install the package. Additionally, you need **Tabsdata python
package 0.9.2 or later** to successfully run the functions from this article.

### 1.2 Start the Tabsdata Server

To start the Tabsdata server, use the following command:

```
tdserver start
```

To verify that the Tabsdata server instance is running:

```
tdserver status
```

Output:

<img src="./assets/tdserver_status.png" alt="Server Status" height="80">

The presence of supervisor and apiserv confirms that the server is running.

### 1.3 Login to the Tabsdata server

Before you can use Tabsdata, you must login to the server which can be done as follows:

```
td login localhost --user admin
```

When prompted from password put:

```
tabsdata
```

Output:
```
Login successful.
```

### 1.4 Copy the GitHub repo

If you haven't already, copy the GitHub repo to your system.

Using SSH:
```
git clone git@github.com:tabsdata/tutorials.git
```

Using GitHub CLI:
```
gh repo clone tabsdata/tutorials
```

### 1.5 Setting up directory path for referencing files

In this tutorial, our data source for the publisher is a CSV file on our file system in a particular input directory. Similarly, our
table subscriber will capture the table data in a JSON format file in a particular output directory.

For convenience we will use an environment variable called `TDX` for referencing the input and output location used
by the publisher and subscriber functions. To do that, let's setup this variable to point to the base
directory of this tutorial. You can do this using the appropriate commands from below:

For Linux or macOS:

```
cd tutorials
cd t01_csv_pub_sub
export TDX=`pwd`
```

For Windows Command Prompt:

```
cd tutorials
cd t01_csv_pub_sub
set TDX=%CD%
```

If you run an `ls` (for Linux or macOS) or `dir` (Windows) on `t01_csv_pub_sub` you would see the following files and folders:

```
README.md
input/
|__ customers.csv
|__ customers_02.csv
publisher.py
subscriber.py
assets/
|_table_sample.png 
|_table_schema.png
```

Here the folder `input` contains two files `customers_01.csv` and `customers_02.csv` that serve as input files. To begin with, we'll duplicate `customers_01.csv` as `customers.csv` within the `input` folder, to be used by the publisher function. Later we will replace the `customers.csv` file with `customers_02.csv` by overwriting it to demonstrate another core functionality of the system.

There are two Python source files - `publisher.py` and `subscriber.py` - which contain the publisher and subscriber
functions. Feel free to take a peak at them - they are pretty straightforward. The assets folder has images for this
README file.

## Step 2: Publishing the input CSV as a table


Now that Tabsdata server is up and running, we can proceed to create our first publisher. A publisher is a simple
Python function that uses built-in connectors provided by Tabsdata to read data from external source(s) and map
it to one or more tables. A few things of note before we proceed:

* The publisher function uses decorators to define the input data source details and output table names.
* A publisher function is registered to a _Collection_ which acts as a container for tables. Consequently, any table(s)
created by the registered publisher function are contained in the collection where it is registered.
* The actual act of reading data from the data source(s) and publishing it to defined table(s) only happens when the
publisher function is invoked by a _trigger_. In this example, we will manually trigger the publisher function to make
it read the CSV file and publish it to a table within Tabsdata.


### 2.1 Creating a collection

In order to register our first publisher, we must create a collection. By default there are no collections within a 
Tabsdata server until you create one. You can see this by running the following command:

```
td collection list
```

For this tutorial, we will create a collection called CUSTOMERS where we will register our publisher function. To
create this collection use the following command:

```
td collection create CUSTOMERS
```

This should have created the collection that you can verify by running the previous list command. You can also see
more details about this collection using the `info` command as follows:

```
td collection info CUSTOMERS
```

Output:

<img src="./assets/collection_info.png" alt="Collection Info" height="100">

This output confirms that the collection called `CUSTOMERS` has been created.

### 2.2 Registering the publisher function

We will now register a publisher function that reads data from a CSV file on a specific input directory and publishes
some selected columns of this data to a table. For convenience, we have this function ready to use in the file
`publisher.py` and the name of this function is `publish_customers`. Here is what this function looks like:


```
@td.publisher(
    source = td.LocalFileSource(os.path.join(os.getenv("TDX"), "input", "customers.csv")),
    tables = ["CUSTOMER_LEADS"],
)

def publish_customers(tf: td.TableFrame):
    output_tf = tf.select(["FIRST_NAME","LAST_NAME","COMPANY_NAME","EMAIL","WEB"])
    return output_tf

```

Here the `@td.publisher` decorator defines the following metadata:
* Data will be read from a local file located at `$TDX/input/customers.csv`
* And the output of this function will be publised as a table called `CUSTOMER_LEADS`

The function definition is very simple in this case with the following details:
* The function name is `publish_customers` that takes a `TableFrame` called `tf`. Note that a `TableFrame` is the API
similar to a traditional `DataFrame` for use with Tabsdata. Note also that when this function executes, this input
`TableFrame` will be populated by the data read from the `$TDX/input/customers.csv` file as specified in the decorator.
* This function selects five specific columns from the input `TableFrame` and returns it as an output. Note that this
output `TableFrame` will be mapped to a table called `CUSTOMER_LEADS` as specified in the decorator.

That is all there is to a publisher. In a real world scenario, your publisher function can have many more inputs and
may produce many more out outputs. Moreover, the body of the function may do more complex operations on the data before
publishing them to output tables.

Register this publisher function to the `CUSTOMERS` collection using the following command.

```
td fn register --collection CUSTOMERS --fn-path $TDX/publisher.py::publish_customers
```

You can now verify that the function was registered successfully by running the following command:

```
td fn list --collection CUSTOMERS
```
Output:

<img src="./assets/list_function_pulisher.png" alt="List functions" height="100">

This output confirms that the function `publish_customers` has been registered within the collection `CUSTOMERS`.


### 2.3 Triggering the publisher

As a reminder, registering a function in a collection does not execute it, and it must be invoked by a trigger. And if
a publisher function has never been triggered, its corresponding output tables will not be initialized in the system.

<!-- 
Before we manually trigger the publisher function, we must make sure that the input CSV file exists in the correct
path. For our first run we will copy the provided sample input file `customers_01.csv` to the input location using
the following command:

For Linux or macOS:
```
cp $TDX/input/customers_01.csv $TDX/input/customers.csv
```

For Windows Command Prompt:
```
copy %TDX%\input\customers_01.csv %TDX%\input\customers.csv
``` -->

<!-- With this input CSV file now in place, let's trigger our publisher. This can be done using the following command: -->

Let's trigger our publisher. This can be done using the following command:

```
td fn trigger --collection CUSTOMERS --name publish_customers
```

You can see the status whether the functions have finished executing by using the following command:

```
td exec list-trxs
```

Output:

<img src="./assets/function_published.png" alt="Function Published" height="100">

If the function has finished executing, you will see Published in the status.


### 2.4 Checking the publisher output

The Tabsdata table `CUSTOMER_LEADS` has been created in the `CUSTOMERS` collection. This table can now be subscribed
to, by various stakeholders within the organization.

To check the schema of the table in Tabsdata, run this command in your CLI:

```
td table schema --collection CUSTOMERS --name CUSTOMER_LEADS
```

Output:

<img src="./assets/table_schema.png" alt="Schema" width="300">

The columns `$td.id` and `$td.src` are internal columns created by Tabsdata to track row level provenance
of data.

To check the sample of the table in Tabsdata, run this command in your CLI:

```
td table sample --collection CUSTOMERS --name CUSTOMER_LEADS
```

Output:

<img src="./assets/table_sample.png" alt="Sample" height="200">

## Step 3: Subscribing to a published Table in Tabsdata

With the customer data available in Tabsdata as a table, it’s now ready for subscription. To demonstrate this we will
create our first subscriber. A subscriber is a simple Python function that reads data from tables published within
Tabsdata and uses built-in connectors provided by Tabasdata to send the data out to an external system. A few things
of note before we proceed:

* The subscriber function uses decorators to define the input table names an output data destinations.
* A subscriber function is registered to a Collection just like a publisher function. For the purposes of this tutorial
we will register our subscriber function within the same collection that we previously created -- `CUSTOMERS`.
* The actual act of reading data from the input tables and writing it to external systems only happens when the
subscriber function is invoked by a trigger. In this tutorial we will demonstrate two types of triggers for a
subscriber function -- a manual trigger that we will do to create our first output; and a dependency trigger that
automatically that happens when the source table changes.


### 3.1 Registering the subscriber function

We will now register a subscriber function that reads data from the CUSTOMERS_LEADS table created by our publisher
function in the prior steps, and externalizes this data in JSON line format to a specific output directory. For
convenience we have this function ready to use in the `subscriber.py` and the name of the function is
`subscribe_customers`. Here is what this function looks like:

```
@td.subscriber(
    tables = ["CUSTOMER_LEADS"],
    destination = td.LocalFileDestination(os.path.join(os.getenv("TDX"), "output", "customer_leads.jsonl")),
)

def subscribe_customers(tf: td.TableFrame):
    return tf
```

Here the `@td.subscriber` decorator defines the following metadata:
* Input data will be read from the table called `CUSTOMER_LEADS`
* And output of this function will be pushed to a file located at `$TDX/output/customer_leads.jsonl`

The function definition is very simple with following details:
* The function name is `subscribe_customers` that takes a `TableFrame` as input. When executed, this input will be
populated by the data coming from the `CUSTOMER_LEADS` table.
* The function simply returns the input data as its output, which is mapped to a specific output file as defined
by the decorator.

That is all there is to a subscriber. In a real world scenario, your subscriber function may take input data from
multiple tables, process it and create a derived output that is then sent to an external system.

Register this subscriber function to the `CUSTOMERS` collection using the following command:

```
td fn register --collection CUSTOMERS --fn-path $TDX/subscriber.py::subscribe_customers
```

You can now verify that the function was registered successfully bu running the following command:

```
td fn list --collection CUSTOMERS
```
Output:

<img src="./assets/list_function_both.png" alt="List both functions" height="150">

This output confirms that the `subscribe_customers` has been registered within the collection `CUSTOMERS`.

### 3.2 Triggering the subscriber

As is the case with publisher functions, registering the subscriber function does not execute it. It must be
executed by a trigger. In this step we will manually trigger the subscriber function for the first time and verify
the generated output.

We begin by making sure that there is no output directory present on our system. The following command should error
out with `No such file or directory`:

For Linux or macOS:
```
ls $TDX/output
```

For Windows:
```
dir %TDX%\output
```


If this directory exists, go ahead and delete it. When the subscribe function is triggerd it will create the necessary
output directory store the output file.

Let's now manually trigger our subscriber function using the following command:

```
td fn trigger --collection CUSTOMERS --name subscribe_customers
```

Remember that you can see the status whether the functions have finished executing by using the following command:

```
td exec list-trxs
```

If the function has finished executing, you will see Published in the status.


### 3.3 Checking the subscriber output:

Once executed, the subscriber would have generated the output file `customer_leads.jsonl` in the `$TDX/output`
directory.

Here is some sample data from `customer_leads.jsonl`:

```
{"FIRST_NAME":"Peter","LAST_NAME":"Gutierres","COMPANY_NAME":"Niagara Custombuilt Mfg Co","EMAIL":"peter_gutierres@yahoo.com","WEB":"https://www.niagaracustombuiltmfgco.co.uk"}
{"FIRST_NAME":"Octavio","LAST_NAME":"Salvadore","COMPANY_NAME":"Practical Periphrals","EMAIL":"octavio.salvadore@yahoo.com","WEB":"https://www.practicalperiphrals.co.uk"}
{"FIRST_NAME":"Martha","LAST_NAME":"Teplica","COMPANY_NAME":"Curtin, Patricia M Esq","EMAIL":"mteplica@teplica.co.uk","WEB":"https://www.curtinpatriciamesq.co.uk"}
```

As you see from the output file, only the columns selected from the `customers.csv` defined in `publisher.py` file have
been exported, and the `jsonl` file is ready for consumption.

## Step 4: Automatic execution of dependencies

What happens when there is an update in your input data? How do you update the data used by the downstream users?

Let’s say there is an update in your CSV file, and 20 new customers get added to the CSV file. The `customers_02.csv`
file in the `input` directory presents one such scenario. This file has 20 new customers in addition to the customers
present in the `customers.csv` file that we loaded via the publisher when we triggered it for the first time.

Here are details of 3 new customers from the 20 who have been added:

| First Name | Last Name  | Company                       | Address         | Ward                              | County         | Postal Code | Phone 1       | Phone 2       | Email                         | Website                                   |
|-------------|-------------|--------------------------------|------------------|--------------------------------------|----------------|----------------|------------------|------------------|--------------------------------------|------------------------------------------------|
| Aleshia     | Tomkiewicz | Alan D Rosenburg Cpa Pc       | 14 Taylor St      | St. Stephens Ward                | Kent            | CT2 7PP          | 01835-703597   | 01944-369967   | atomkiewicz@hotmail.com   | [alandrosenburgcpapc.co.uk](https://www.alandrosenburgcpapc.co.uk) |
| Evan         | Zigomalas     | Cap Gemini America                | 5 Binney St        | Abbey Ward                            | Buckinghamshire | HP11 2AX          | 01937-864715   | 01714-737668   | evan.zigomalas@gmail.com      | [capgeminiamerica.co.uk](https://www.capgeminiamerica.co.uk) |
| France       | Andrade         | "Elliott, John W Esq"              | 8 Moor Place      | East Southbourne and Tuckton W | Bournemouth     | BH6 3BE          | 01347-368222   | 01935-821636   | france.andrade@hotmail.com    | [elliottjohnwesq.co.uk](https://www.elliottjohnwesq.co.uk) |

<br/>

## 4.1 Provisioning new input file

Before we can demonstrate the automatic execution of this workflow, we must provision the new input file in the correct
location for the publisher to read and publish it accordingly. This can be done using the following command:

For Linux or macOS:
```
cp $TDX/input/customers_02.csv $TDX/input/customers.csv
```

For Windows Command Prompt:
```
copy %TDX%\input\customers_02.csv %TDX%\input\customers.csv
```

<!-- This will overwrite the `customers.csv` file that was previously copied from `customers_01.csv` file for our first
execution. -->

This will overwrite the previous version of `customers.csv` file that we were working with.

## 4.2 Saving first output file for comparison

When this new workflow executes, the subscriber will overwrite the output file `$TDX/output/customer_leads.jsonl` with
new data. Hence, let's create a backup of this file for later comparison using the following command:

For Linux or macOS:
```
cp $TDX/output/customer_leads.jsonl $TDX/output/customer_leads_01.jsonl
```

For Windows Command Prompt:
```
copy %TDX%\output\customer_leads.jsonl %TDX%\output\customer_leads_01.jsonl
```

## 4.3 Trigger the pub/sub workflow

The publisher function that we registered earlier creates a table called `CUSTOMER_LEADS`. This table in turn has a
registered subscriber. Together, this publisher/subscriber pair makes a simple data engineering workflow. When the
publisher activates and updates the table, it will automatically trigger any subscribers for the updated tables.

To demonstrate this, we will trigger our publisher function manually. This should automatically trigger the subscriber
function which in turn should overwrite our expected output file. Since the new input file has 20 more customer
records, we expect that the output file will also have 20 more customer records available.

Use the following command to trigger the publisher to read new input file:

```
td fn trigger --collection CUSTOMERS --name publish_customers
```

Remember that you can see the status whether the functions have finished executing by using the following command:

```
td exec list-trxs
```

If the function has finished executing, you will see Published in the status.

In this example, there is only one subscriber that was executed on refresh of the published table. However, it will work for any number of subscribers that are registered and have their input tables associated with the publisher.

## Check the Subscriber Output:

Once the publisher has been executed, you can check the `customer_leads.jsonl` file in the `output` folder to see if the changes are getting reflected.

Here is some sample data from the new `customer_leads.jsonl`:

```
{"FIRST_NAME":"Aleshia","LAST_NAME":"Tomkiewicz","COMPANY_NAME":"Alan D Rosenburg Cpa Pc","EMAIL":"atomkiewicz@hotmail.com","WEB":"https://www.alandrosenburgcpapc.co.uk"}
{"FIRST_NAME":"Evan","LAST_NAME":"Zigomalas","COMPANY_NAME":"Cap Gemini America","EMAIL":"evan.zigomalas@gmail.com","WEB":"https://www.capgeminiamerica.co.uk"}
{"FIRST_NAME":"France","LAST_NAME":"Andrade","COMPANY_NAME":"Elliott, John W Esq","EMAIL":"france.andrade@hotmail.com","WEB":"https://www.elliottjohnwesq.co.uk"}
```

The above users were not present in the JSON file before, and have been added after the publisher was triggered with
the new `customers.csv` file. You can verify this by comparing the `customer_leads.jsonl` file with
`customer_leads_01.jsonl` that we saved for comparison earlier.


## Conclusion

We have successfully implemented a Pub/Sub for Tables using Tabsdata. We published the data from a CSV file as a table
after selecting certain columns from it. We then subscribed to the published table. We also demonstrated automatic
execution of the entire workflow when a data source was refreshed.


## Next Steps

For the next steps, here are a couple of experiements you can try:

* Add a Tabsdata
  [transformer](https://docs.tabsdata.com/latest/guide/04_working_with_functions/working_with_transformers/main.html)
  in the mix. Perform complex transformations on ``CUSTOMER_LEADS`` table using a Tabsdata tranformer, and connect the
  output table from the transformer to a subscriber.
* Read files from and write files to different external systems beyond local file system. You can read more about them
  [here](https://docs.tabsdata.com/latest/guide/supported_sources_and_destinations/main.html).


I hope this gave you a good introduction to the Tabsdata system! I'd love to hear your thoughts—let us know how we can
improve, what use cases you'd like us to cover in future blogs, or any other questions or feedback you have. Join the
conversation on [Discord](https://discord.gg/XRC5XZWppc),
[GitHub Discussions](https://github.com/tabsdata/tabsdata/discussions) or reach out to us
[here](https://www.tabsdata.com/contact).
