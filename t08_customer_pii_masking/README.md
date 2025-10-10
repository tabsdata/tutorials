# Tutorial 8: Masking and Subscribing Customer Data with Tabsdata (`t08_customer_pii_masking`)

This tutorial shows how Tabsdata can be used to mask and redact PII data from customer datasets. 

If you get stuck, check our [Troubleshooting](https://docs.tabsdata.com/latest/guide/10_troubleshooting/main.html) guide or reach out on [Slack](https://join.slack.com/t/tabsdata-community/shared_invite/zt-322toyigx-ZGFioMV2Gbza4bJDAR7wSQ).

For more details on each step, see our initial tutorials ([1](https://github.com/tabsdata/tutorials/tree/main/t01_csv_pub_sub), [2](https://github.com/tabsdata/tutorials/tree/main/t02_postgres_pub_sub), [3](https://github.com/tabsdata/tutorials/tree/main/t03_csv_iceberg_pub_sub), [4](https://github.com/tabsdata/tutorials_staging/tree/main/t04_gsheet_neon), [5](https://github.com/tabsdata/tutorials_staging/tree/main/t05_oracle_cdc)).

## Prerequisites

- Python 3.12 or higher
- Tabsdata 1.3.0
- AWS Glue Database and S3 Bucket
- MySQL Database

## 1. Clone the GitHub Repository

```sh
git clone https://github.com/tabsdata/tutorials
cd tutorials/t08_customer_pii_masking/functions
```

## 2. Set up AWS and MySQL credentials

Input your AWS credentials into the [source.sh](./source.sh) file

Then export all the variables into your current shell. The command below is specifically for bash, but modify the command and source script to suit your shell setup.
```sh
source ../source.sh
```

## 3. Setup Tabsdata Instance

### 3.1. Install Tabsdata
```sh
pip install tabsdata
pip install mysql-connector-python==9.3.0
```

### 3.2. [OPTIONAL] Quickstart Tabsdata Instance 

Tutorial steps 3.3 - 4 run through each command necessary to set up your instance below. However, we also have a quickstart that bundles all the commands into a shell script. If doing quickstart, you may skip to [step 4](#4-trigger-your-publisher-function)

The quickstart script:
1. Creates the MySQL table and loads the data within [customer_data.csv](input/customer_data.csv) into it
2. Creates your tabsdata instance
3. Registers all relevant functions for the workflow

<details>
<summary><h1>Quickstart Setup 💨</h1></summary>

> If you would like your workflow to subscribe your data into AWS Glue, run the following command:
>
> ```sh
> source ../setup-tabsdata.sh aws
> ```
>
> If you do not want to connect with AWS and just have your data subscribed back into mysql, run the following command:
>
> ```sh
> source ../setup-tabsdata.sh
> ```
</details>



### 3.3 Start the Server

```sh
tdserver start --instance pii
```

### 3.4 Login

```sh
td login --server localhost --user admin --role sys_admin --password tabsdata
```

### 3.5 Create a Collection

```sh
td collection create --name pii
```

### 3.3 Create raw_customer_data Table in MySQL

This tutorial includes a Tabsdata publisher and subscriber that handles the creation and loading of the MySQL table for you. Run the following commands to execute those functions:

```sh
td fn register --coll pii --path 00_mysql_setup_pub.py::mysql_setup_pub
td fn register --coll pii --path 00_mysql_setup_sub.py::mysql_setup_sub
td fn trigger --coll pii --name mysql_setup_pub 
echo delete | td fn delete --coll pii --name mysql_setup_pub
echo delete | td fn delete --coll pii --name mysql_setup_sub
echo delete | td table delete --coll pii --name input_data
```

If you would like to handle the import of data into MySQL manually, load the data in [customer_data.csv](input/customer_data.csv) into a MySQL table of the following schema

```sql
CREATE TABLE raw_customer_data (
  id BIGINT,
  first_name TEXT,
  last_name TEXT,
  email TEXT,
  gender TEXT,
  ip_address TEXT,
  phone_number TEXT,
  date_of_birth TEXT,
  SSN TEXT,
  Address TEXT,
  City TEXT,
  State TEXT,
  Postal_Code TEXT,
  Country TEXT,
  Account_Balance BIGINT,
  loyalty_points BIGINT,
  signup_date TEXT,
  notes_extra TEXT
);
```

### 3.6 Register Functions to Tabsdata

All function files must be registered into the tabsdata server with the `td fn register` CLI command.

Attached below is a detailed explanation of each function and what it's doing:

**Publishers:**
1. `01_mysql_pub.py` publishes customer data from MySQL into  it in a Tabsdata Table called `raw_customer_data`

```sh
td fn register --coll pii --path 01_mysql_pub.py::mysql_pub
```

**Transformers:**

2. `02_mask_trf.py` masks all pii data within `raw_customer_data` and writes the result into a table called `masked_customer_data`

```sh
td fn register --coll pii --path 02_mask_trf.py::mask_trf
```

**Subscribers:**

3. `03_s3_sub.py` subscribes the `masked_customer_data` table into AWS Glue

4. `04_mysql_sub.py` subscribes the `masked_customer_data` table into MySQL



To subscribe your data into MySQL, run the following command

```sh
td fn register --coll pii --path 04_mysql_sub.py::mysql_sub
```

If you would also like to subscribe your data into AWS, run the following command:

```sh
td fn register --coll pii --path 03_s3_sub.py::s3_sub
```

## 4. Trigger your Publisher Function

Once all functions are registered, you just need to trigger your `mysql_pub` publisher, and Tabsdata automatically runs everything downstream

```sh
td fn trigger --coll pii --name mysql_pub
```

## 7. Monitor Output

### 7.1. Monitor AWS Output
After your function finishes running, you can access the status of your execution through our UI: http://localhost:2457/

### 7.2. Sample Tabsdata Table Output in Tabsdata UI
You can sample your Tabsdata Tables through the [Tabsdata UI](http://localhost:2457/). To access the UI, click the link and fill in the following credentials within the login page:

Username: admin  
Password: tabsdata  
Role: sys_admin  

Once logged in, you may sample any of the tables generated through the workflow, as well as any of their version history, [here](http://localhost:2457/collections/pii)

### 7.3. Sample Tabsdata Table Output in Tabsdata CLI
You may also sample your tables through the Tabsdata CLI

```sh
td table sample --coll pii --name INSERT_TABLE_NAME
```


## Need Help?

Check the [Troubleshooting Guide](https://docs.tabsdata.com/latest/guide/10_troubleshooting/main.html) or ask in our [Slack Community](https://join.slack.com/t/tabsdata-community/shared_invite/zt-322toyigx-ZGFioMV2Gbza4bJDAR7wSQ).

