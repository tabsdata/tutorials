In this tutorial, we’ll explore how Tabsdata enables Pub/Sub for Tables.

We'll start by setting up the system and creating a publisher that reads data from a CSV file called `customers.csv` stored in an input directory in the local file system. This data will be published as a table called CUSTOMER_LEADS within a collection called CUSTOMERS. Collections are containers for related tables in Tabsdata, to make data organization and management more efficient. On the subscriber side, we'll set up a subscriber that reads data from this table and writes it to an output directory in the local file system. 

In a real-world scenario, your data source could be a database, an S3 bucket, or another storage location, while the subscriber could write data to various endpoints such as a database or file system.

Through this article you will understand how Tabsdata can help you

* connect with external systems with ease through our built-in connectors, and
* process data as tables when defining Tabsdata functions.

Let’s dive in! We’ll start by setting up the system to prepare us to work with the Tabsdata functions.

# Step 1. Setting up the system

## 1. Install Tabsdata

To install/update the Tabsdata Python package, run this command in your CLI:

```
pip install tabsdata --upgrade
```

Please note that you need **Python 3.12 or later**, to install the package. Additionally, you need **Tabsdata python package 0.9.2 or later** to successfully run the functions from this article.

## 2. Start the Tabsdata Server

To start the Tabsdata server, use the following command:

```
tdserver start
```


To verify that the Tabsdata server instance is running:

```
tdserver status
```


## 3. Copy the github repo

If you haven't already, copy the github repo to your system.

```
git clone https://github.com/tabsdata/tutorials
```

## 4. Save the working directory path in an environment variable

As shared earlier, our data input in this example is present in a directory in the local file system, and the data output is sent to another directory in the local file system. To define these input and output directories we will use an environment variable called `TDX`. You can choose to define the absolute working directory of your input and output files in any other manner of your choice.

To store the value of your working directory in the variable `TDX`, run the following command in your CLI from the directory where you have copied the Github repo:

For Linux or MacOS:

```
cd tutorials
cd t01_csv_pub_sub
export TDX=`pwd`
```

For Windows:

```
cd tutorials
cd t01_csv_pub_sub
set TDX=%CD%
```

If you run an `ls` on `t01_csv_pub_sub` you would see the following files and folders:

```
README.md
input/
|__ customers.csv
input_02/
|__ customers.csv
publisher.py
subscriber.py
```

Here the folders `input` and `input_02` contain the `customers.csv` file that serve as input files for our tutorial. We'll start by using the file in the `input` folder. Towards the end of the tutorial, we'll use the one in `input_02`. Python source files - `publisher.py` and `subscriber.py` - contain the publisher and subscriber functions. Feel free to take a peak at them - they are pretty straightforward.

## 5. Login to the Tabsdata server

Before you can use Tabsdata, you must login to the server which can be done as follows:

```
td login localhost --user admin --password tabsdata
```


# Step 2: Publishing the CSV to Tabsdata

Once set up, we can now use Tabsdata to process the CSV file to select certain columns from it and publish the resultant data as a table.

Tabsdata organizes data using collections, which act as containers for structured datasets. Hence, before publishing the data, we first create a `CUSTOMERS` collection to store the table to be created inside Tabsdata. To do that, run the following command in your CLI:

```
td collection create CUSTOMERS
```

Once the `CUSTOMERS` collection has been created, you can publish the CSV as a Tabsdata table. To do that, run the following CLI commands from your working directory:

```
td fn register --collection CUSTOMERS --fn-path publisher.py::publish_customers
td fn trigger --collection CUSTOMERS --name publish_customers
```

In the above commands you are first registering the function `publish_customers` with the Tabsdata collection and then triggering its execution. You can read more about these steps in the [Tabsdata documentation](https://docs.tabsdata.com/latest/guide/04_working_with_functions/main_1.html).

The Tabsdata function `publish_customers` reads the `customers.csv` file from the local file system, selects certain columns from it, and writes the data as a table in the `CUSTOMERS` collection as a table called `CUSTOMER_LEADS`. The function is defined in the `publisher.py` file in the working directory, with the following Python code:

```
@td.publisher(
    source = td.LocalFileSource(os.path.join(os.getenv("TDX"), "input",  "customers.csv")),
    tables = ["CUSTOMER_LEADS"],
)

def publish_customers(tf: td.TableFrame):
    tf = tf.select(["IDENTIFIER", "GENDER", "NATIONALITY", "LANGUAGE", "OCCUPATION"])
    return tf

```
where,

**source** defines the location of the file.

**tables** defines the name of the table (`CUSTOMER_LEADS`) to be created by the publisher.

## Check the Publisher Output:

The Tabsdata table `CUSTOMER_LEADS` has been created in the `CUSTOMERS` collection. This table can now be subscribed to, by various stakeholders within the organization.

To check the schema of the table in Tabsdata, run this command in your CLI:

```
td table schema --collection CUSTOMERS --name CUSTOMER_LEADS
```

Output:

<img src="./assets/table_schema.png" alt="Schema" width="300">

The columns `$td.id` and `$td.src` are internal columns created by Tabsdata to track row level lineage and provenance of data.

To check the sample of the table in Tabsdata, run this command in your CLI:

```
td table sample --collection CUSTOMERS --name CUSTOMER_LEADS
```

Output:

<img src="./assets/table_sample.png" alt="Sample" height="300">

# Step 3: Subscribing to the Table in Tabsdata

Now that the customer data is available in the Tabsdata system as a table, it’s ready for subscription. For instance, if the sales team requests customer data in JSON list format for their SaaS software, you can simply point them to the `CUSTOMER_LEADS` table in Tabsdata. They can then subscribe to this table to receive the data. To simulate this process and subscribe to the `CUSTOMER_LEADS` table, run the following CLI commands from your working directory:

```
td fn register --collection CUSTOMERS --fn-path subscriber.py::subscribe_customers
td fn trigger --collection CUSTOMERS --name subscribe_customers
```

In the above commands you are first registering the function `subscribe_customers` with the Tabsdata collection and then triggering its execution. You can read more about these steps in the [Tabsdata documentation](https://docs.tabsdata.com/latest/guide/04_working_with_functions/main_1.html).

The Tabsdata function `subscribe_customers` reads the `CUSTOMER_LEADS` table from Tabsdata, and writes it as `customer_leads.jsonl` in the local file system. It is defined in the `subscriber.py` file in the working directory, with the following Python code:

```
@td.subscriber(
    tables = ["CUSTOMER_LEADS"],
    destination = td.LocalFileDestination(os.path.join(os.getenv("TDX"), "output","customer_leads.jsonl")), 
)

def subscribe_customers(tf: td.TableFrame):
    return tf
```

where,

**tables** defines the name of the table (`CUSTOMER_LEADS`) to be read from the Tabsdata collection.

**destination** parameter defines the path to the folder, the file name, and the file format, to be written by the subscriber.

## Check the Subscriber Output:

Once executed, the subscriber would have generated the output file `customer_leads.jsonl` in the `output` directory.

Here is some sample data from `customer_leads.jsonl`:

```
{"IDENTIFIER":"74-93/03","GENDER":"Male","NATIONALITY":"Portuguese","LANGUAGE":"Italian","OCCUPATION":"Hod Carrier"}
{"IDENTIFIER":"68-52/94","GENDER":"Female","NATIONALITY":"Costa Rican","LANGUAGE":"Swati","OCCUPATION":"Aeronautical Engineer"}
{"IDENTIFIER":"37-41/89","GENDER":"Male","NATIONALITY":"Cuban","LANGUAGE":"Luxembourgish","OCCUPATION":"Telex Operator"}
```

As you see from the output file, only the columns selected from the `customers.csv` defined in `publisher.py` file have been exported, and the `jsonl` file is ready for consumption.

# Step 4: Automate Data Engineering

What happens when there is an update in your input data? How do you update the data used by the downstream users?

Let’s say there is an update in your CSV file, and 20 new customers get added to the CSV file. The `customers.csv` file in the `input_02` folder presents one such scenario. The file has 20 new customers in addition to the customers present in the `customers.csv` file in the `input` folder.

Here are details of 3 of these new customers from the 20 who have been added:

| IDENTIFIER | NAME       | SURNAME | FIRST_NAME | LAST_NAME | FULL_NAME       | GENDER | GENDER_CODE | GENDER_SYMBOL | SEX    | PHONE_NUMBER  | TELEPHONE      | EMAIL                          | BIRTHDATE  | NATIONALITY | LANGUAGE | LOCALE    | BLOOD_TYPE | HEIGHT | WEIGHT | UNIVERSITY                                         | ACADEMIC_DEGREE | TITLE | OCCUPATION           | POLITICAL_VIEWS | WORLDVIEW          | USERNAME          | PASSWORD     |
|-------------|------------|---------|-------------|-----------|------------------|--------|--------------|----------------|--------|----------------|-----------------|-------------------------------|------------|--------------|-----------|------------|-------------|--------|--------|-----------------------------------------------------|------------------|-------|----------------------|------------------|---------------------|--------------------|--------------|
| 21-12/62     | Dakota      | Baxter  | Louetta      | Myers     | Tracy Ball        | Other  | 1            | ♂               | Female | +12272974320   | +16146882188    | drainage2086@duck.com         | 2022-11-04 | Swiss        | Zulu      | Locale.EN  | A+          | 1.79   | 38     | Western Connecticut State University (WCSU)        | PhD               | Mr.   | Medical Technician     | Moderate          | Pantheism           | networks_1867       | Gvwp+R+N     |
| 97-89/11     | Christinia  | Espinoza| Elden        | Alvarado  | Gerald Wolfe      | Female | 0            | ⚲               | Other  | +1-402-266-2114| +1-479-878-9781 | livestock1811@example.org     | 2014-05-09 | Dominican    | Yiddish   | Locale.EN  | A+          | 1.80   | 74     | Florida Gulf Coast University (FGCU)               | PhD               | Ms.   | Maid                  | Socialist          | Atheism             | throw_1882          | }&<h*EYp     |
| 92-54/93     | Perry       | Herman  | Amina        | Montgomery| Lory Justice      | Other  | 0            | ♀               | Female | +1-817-696-6699| +1-213-091-1513 | dynamic2052@duck.com          | 2018-12-24 | Salvadorian  | Greek     | Locale.EN  | B+          | 1.66   | 42     | University of South Florida (USF)                   | Bachelor           | B.Sc  | Town Planner           | Libertarian        | Secular humanism    | excitement_1908      | ]X4&n9yn     |


To simulate the new customers data being available as input, you need to replace the `customers.csv` file in the `input` folder with the one in `input_02`. Now, the `customers.csv` in the `input` folder would also have the data of 20 new customers.

Once the new input file is available, you just need to execute the publisher `publish_customers` using the command below to update the data files used by the downstream users.

```
td fn trigger --collection CUSTOMERS --name publish_customers
```

Once the publisher executes, all the downstream functions that are dependent on the output table `CUSTOMER_LEADS` from `publish_customers` would get executed to generate their respective output data.

In our current example, since `susbcribe_customers` is dependent on the `CUSTOMER_LEADS` table, the subscriber would get executed to generate a new version of `customer_leads.jsonl` file in the local file system. You can read more about the automated dependency management in the Tabsdata documentation.

## Check the Output:

Once the publisher has been executed, you can check the `customer_leads.jsonl` file in the `output` folder to see if the changes are getting reflected.

Here is some sample data from the new `customer_leads.jsonl`:

```
{"IDENTIFIER":"21-12/62","GENDER":"Other","NATIONALITY":"Swiss","LANGUAGE":"Zulu","OCCUPATION":"Medical Technician"}
{"IDENTIFIER":"97-89/11","GENDER":"Female","NATIONALITY":"Dominican","LANGUAGE":"Yiddish","OCCUPATION":"Maid"}
{"IDENTIFIER":"92-54/93","GENDER":"Other","NATIONALITY":"Salvadorian","LANGUAGE":"Greek","OCCUPATION":"Town Planner"}
```

The above users were not present in the JSON file before, and have been added after the publisher was triggered with the new `customers.csv` file.

This implies that after executing the publisher with the new input data, changes percolated downstream. In a real world environment, this would ensure that all the teams within an organization are looking at the same version of data.

**Note:** If for any reason, the downstream team wishes to subscribe to the older version of the table, then can use simple Table commits syntax in Tabsdata to do that. You can read more about it in the Tabsdata documentation.


### Mission Accomplished!!

We have successfully implemented a Pub/Sub for Tables using Tabsdata. We published the data from a CSV file as a table after selecting certain columns from it. We then subscribed to the resultant table. We also automated data engineering by automatically updating the output data when the input data changed.


## Next Steps:

For the next steps, here are a couple of experiements you can try:

* Add a Tabsdata [transformer](https://docs.tabsdata.com/latest/guide/04_working_with_functions/working_with_transformers/main.html) in the mix. Perform complex transformations on ``CUSTOMER_LEADS`` table using a Tabsdata tranformer, and connect the output table from the transformer to a subscriber.
* Read files from and write files to different external systems beyond local file system. You can read more about them [here](https://docs.tabsdata.com/latest/guide/supported_sources_and_destinations/main.html).


I hope this gave you a good introduction to the Tabsdata system! I'd love to hear your thoughts—let us know how we can improve, what use cases you'd like us to cover in future blogs, or any other questions or feedback you have. Join the conversation on [Discord](https://discord.gg/XRC5XZWppc), [Github Discussions](https://github.com/tabsdata/tabsdata/discussions) or reach out to us [here](https://www.tabsdata.com/contact).