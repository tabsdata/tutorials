# Tutorial 9: Publishing and Subscribing Salesforce Reports (`t09_salesforce_report_ingestion`)

This tutorial shows how Tabsdata can easily query Salesforce Reports and Subscribe them anywhere

If you get stuck, check our [Troubleshooting](https://docs.tabsdata.com/latest/guide/10_troubleshooting/main.html) guide or reach out on [Slack](https://join.slack.com/t/tabsdata-community/shared_invite/zt-322toyigx-ZGFioMV2Gbza4bJDAR7wSQ).

For more details on each step, see our initial tutorials ([1](https://github.com/tabsdata/tutorials/tree/main/t01_csv_pub_sub), [2](https://github.com/tabsdata/tutorials/tree/main/t02_postgres_pub_sub), [3](https://github.com/tabsdata/tutorials/tree/main/t03_csv_iceberg_pub_sub), [4](https://github.com/tabsdata/tutorials_staging/tree/main/t04_gsheet_neon), [5](https://github.com/tabsdata/tutorials_staging/tree/main/t05_oracle_cdc)).

## Prerequisites

- Python 3.12 or higher
- Tabsdata 1.3.0
- Snowflake Instance
- Salesforce Instance

## 1. Clone the GitHub Repository

```sh
git clone https://github.com/tabsdata/tutorials
cd tutorials/t09_salesforce_report_ingestion/functions
```

## 2. Set up Snowflake and MySQL credentials

Input your Snowflake and Salesforce credentials into the [source.sh](./source.sh) file

Then export all the variables into your current shell. The command below is specifically for bash, but modify the command and source script to suit your shell setup.
```sh
. ../source.sh
```

## 3. Setup Tabsdata Instance

### 3.1. Install Tabsdata
```sh
pip install tabsdata
pip install 'tabsdata[salesforce]'
pip install 'tabsdata[snowflake]'
```

### 3.2. [OPTIONAL] Quickstart Tabsdata Instance 

Tutorial steps 3.3 - 4 run through each command necessary to set up your instance below. However, we also have a quickstart that bundles all the commands into a shell script. If doing quickstart, you may skip to [step 4](#4-trigger-your-publisher-function)

The quickstart script:  
1. Creates your tabsdata instance. 
2. Registers all relevant functions for the workflow. 

<details>
<summary><h1>Quickstart Setup 💨</h1></summary>

> If you would like your workflow to subscribe your data into Snowflake, run the following command:
>
> ```sh
> source ../setup-tabsdata.sh snowflake
> ```
>
> If you do not want to connect with Snowflake and just have your data subscribed back into the [output folder](output) within localfile storage, run the following command:
>
> ```sh
> source ../setup-tabsdata.sh
> ```
</details>



### 3.3 Start the Server

```sh
tdserver start --instance salesforce
```

### 3.4 Login

```sh
td login --server localhost --user admin --role sys_admin --password tabsdata
```

### 3.5 Create a Collection

```sh
td collection create --name salesforce
```

### 3.6 Register Functions to Tabsdata

All function files must be registered into the tabsdata server with the `td fn register` CLI command.

Attached below is a detailed explanation of each function, what it's doing, and the CLI command to register it:

**Publishers:**
1. `01_salesforce_pub.py` publishes Salesforce Report into a Tabsdata Table called `sf_snapshot`

```sh
td fn register --coll salesforce --path 01_salesforce_pub.py::salesforce_pub
```

**Subscribers:**

3. `03_local_sub.py` subscribes the `sf_snapshot` table into the [output folder](output) within localfile storage

4. `02_snowflake_sub.py` subscribes the `sf_snapshot` table into Snowflake



To subscribe your data into localfile storage, run the following command

```sh
td fn register --coll salesforce --path 03_local_sub.py::local_sub
```

If you would also like to subscribe your data into Snowflake, run the following command:

```sh
td fn register --coll salesforce --path 02_snowflake_sub.py::snowflake_sub
```

## 4. Trigger your Publisher Function

Once all functions are registered, you just need to trigger your `salesforce_pub` publisher, and Tabsdata automatically runs everything downstream

```sh
td fn trigger --coll salesforce --name salesforce_pub
```

## 5. Monitor Output

### 5.1. Monitor Snowflake Output
After your function finishes running, you can access the status of your execution through our UI: http://localhost:2457/

### 5.2. Sample Tabsdata Table Output in Tabsdata UI
You can sample your Tabsdata Tables through the [Tabsdata UI](http://localhost:2457/). To access the UI, click the link and fill in the following credentials within the login page:

Username: admin  
Password: tabsdata  
Role: sys_admin  

Once logged in, you may sample any of the tables generated through the workflow, as well as any of their version history, [here](http://localhost:2457/collections/pii)

### 5.3. Sample Tabsdata Table Output in Tabsdata CLI
You may also sample your tables through the Tabsdata CLI

```sh
td table sample --coll salesforce --name INSERT_TABLE_NAME
```


## Need Help?

Check the [Troubleshooting Guide](https://docs.tabsdata.com/latest/guide/10_troubleshooting/main.html) or ask in our [Slack Community](https://join.slack.com/t/tabsdata-community/shared_invite/zt-322toyigx-ZGFioMV2Gbza4bJDAR7wSQ).

