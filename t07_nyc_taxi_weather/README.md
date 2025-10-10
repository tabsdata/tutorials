# Tutorial 7: Publishing and Subscribing NYC Taxi Data into AWS Glue (`t07_nyc_taxi_weather`)

This tutorial shows how Tabsdata can connect to non-standard external systems to ingest and transform data. In this tutorial, we ingest NYC Taxi Data from the [TLC](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) website and historical NYC weather data from a free weather API called [OpenMeteo](https://open-meteo.com/). Then, we aggregate our raw taxi data into daily metrics (trips per day, average trip duration, etc.) and enrich the aggregated metrics with weather metrics such as temperature, windspeed, and precipitation. 

If you get stuck, check our [Troubleshooting](https://docs.tabsdata.com/latest/guide/10_troubleshooting/main.html) guide or reach out on [Slack](https://join.slack.com/t/tabsdata-community/shared_invite/zt-322toyigx-ZGFioMV2Gbza4bJDAR7wSQ).

For more details on each step, see our initial tutorials ([1](https://github.com/tabsdata/tutorials/tree/main/t01_csv_pub_sub), [2](https://github.com/tabsdata/tutorials/tree/main/t02_postgres_pub_sub), [3](https://github.com/tabsdata/tutorials/tree/main/t03_csv_iceberg_pub_sub), [4](https://github.com/tabsdata/tutorials_staging/tree/main/t04_gsheet_neon), [5](https://github.com/tabsdata/tutorials_staging/tree/main/t05_oracle_cdc)).

## Prerequisites

- Python 3.12 or higher
- Tabsdata 1.0.0 or higher
- AWS Glue Database and S3 Bucket

## 1. Clone the GitHub Repository

```sh
git clone https://github.com/tabsdata/tutorials
cd tutorials/t07_nyc_taxi_weather/functions
```

## 2. Set up AWS credentials

Input your AWS credentials into the [source.sh](./source.sh) file

Then export all the variables into your current shell. The command below is specifically for bash, but modify the command and source script to suit your shell setup.
```sh
source ../source.sh
```

## 3. Setup Tabsdata Instance

### 3.1. Install Tabsdata
```sh
pip install tabsdata
```

### 3.2. [OPTIONAL] Quickstart Tabsdata Instance 

Tutorial steps run through each command necessary to set up your instance below. However, we also have a quickstart that bundles all the commands into a shell script. If doing quickstart, you may skip to [step 4](#4-trigger-your-publisher-function)

<details>
<summary><h1>Quickstart Setup 💨</h1></summary>

> If you would like your workflow to subscribe your data into AWS Glue, run the following command:
>
> ```sh
> source ../setup-tabsdata.sh aws
> ```
>
> If you do not want to connect with AWS and just have your data subscribed into the [output](./output) folder on your local file system, run the following command:
>
> ```sh
> source ../setup-tabsdata.sh
> ```
</details>


### 3.3 Start the Server

```sh
tdserver start --instance nyc_taxi
```

### 3.4 Login

```sh
td login --server localhost --user admin --role sys_admin --password tabsdata
```

### 3.5 Create a Collection

```sh
td collection create --name taxi
```

### 3.6 Register Functions to Tabsdata

All function files must be registered into the tabsdata server with the `td fn register` CLI command.

Attached below is a detailed explanation of each function and what it's doing:

**Publishers:**
1. `01_nyc_taxi_pub.py` uses a custom connector to ingest data from the NYC TLC commission website and store it in a Tabsdata Table called `nyc_taxi_stats`

3. `03_weather_pub.py` uses a custom connector to ingest data from a free weather api called OpenMeteo and store it in a Tabsdata Table called `nyc_weather`

```sh
td fn register --coll taxi --path 01_nyc_taxi_pub.py::nyc_taxi_pub
td fn register --coll taxi --path 03_weather_pub.py::weather_pub

```

**Transformers:**

2. `02_agg_taxi_metrics_trf.py` aggregates the raw nyc taxi data into daily metrics and writes the data into a Tabsdata Table called `daily_taxi_metrics`

4. `04_join_weather_trf.py` enriches daily taxi metrics with weather data and stores it in a Tabsdata Table called `taxi_metrics_with_weather`

```sh
td fn register --coll taxi --path 02_agg_taxi_metrics_trf.py::agg_taxi_metrics_trf
td fn register --coll taxi --path 04_join_weather_trf.py::join_weather_trf
```

**Subscribers:**

6. `05_s3_sub.py` subscribes the `taxi_metrics_with_weather` table into AWS Glue

7. `05_local_sub.py` subscribes the `taxi_metrics_with_weather` table into the [output](./output) folder


If you would like to subscribe your data into AWS, run the following command:

```sh
    td fn register --coll taxi --path 05_s3_sub.py::s3_sub
```

If you don't want to connect with AWS and simply write the data back into your local file system, run the following command: 

```sh
    td fn register --coll taxi --path 05_local_sub.py::local_sub
```

## 4. Trigger your Publisher Function

Once all functions are registered, you just need to trigger your `nyc_taxi_pub` publisher, and Tabsdata automatically runs everything downstream

```sh
td fn trigger --coll taxi --name nyc_taxi_pub
```

## 7. Monitor Output

### 7.1. Monitor AWS Output
After your function finishes running, you can access the status of your execution through our UI: http://localhost:2457/

### 7.2. Sample Tabsdata Table Output in Tabsdata UI
You can sample your Tabsdata Tables through the [Tabsdata UI](http://localhost:2457/). To access the UI, click the link and fill in the following credentials within the login page:

Username: admin  
Password: tabsdata  
Role: sys_admin  

Once logged in, you may sample any of the tables generated through the workflow, as well as any of their version history, [here](http://localhost:2457/collections/claim_processing)

### 7.3. Sample Tabsdata Table Output in Tabsdata CLI
You may also sample your tables through the Tabsdata CLI

```sh
td table sample --coll taxi --name INSERT_TABLE_NAME
```


## Need Help?

Check the [Troubleshooting Guide](https://docs.tabsdata.com/latest/guide/10_troubleshooting/main.html) or ask in our [Slack Community](https://join.slack.com/t/tabsdata-community/shared_invite/zt-322toyigx-ZGFioMV2Gbza4bJDAR7wSQ).

