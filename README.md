# Sample Securities Portfolio & data model

### Data model

In this repository, we are building a sample trading data model. The whole idea is to select a suitable  representational technique to store the data model
that is efficient and extensible at the same time. especially when we are building a trading application. Since it is imperative to guarantee minimal response time and higher throughput, we will use native data structures of Redis like JSON and will leverage the Query Engine for indexing and querying the data.
The following are some important entities in this sample application:

1. Investor: This would typically be any type of investor, like retail, corporation etc. Let's choose a retail investor for that matter.

  Key format: `trading:investor:<investorId>`

```json
    {
      "id": "INV10001", 
      "name": "Johny M.", 
      "uid": "35178235834", 
      "email": "johny.m@gmail.com",
      "address": "...",
      "pan": "AHUIOHO684" 
    }
```
    
       id -> unique identifier of the investor
       name -> Name of the investor
       uid -> Unique government ID (SSN, Aadhaar etc)
       pan -> Unique taxpayer ID provided by the government (in India)
       email -> Email address
   
2. Account: This is the unique trading account of the investor. An investor can have multiple accounts against which the investment might have been made. 
  We will stick to only one account per investor in this demo
  
    Key format: `trading:account:<accountNo>`
    ```json
    {
      "id": "ACC10001",
      "investorId": "INV10001",
      "accountNo": "ACC10001",
      "accountOpenDate": "20/11/2018",
      "accountCloseDate": "NA",
      "retailInvestor": true 
    }
    ```

       id -> unique identifier of the investor
       investorId -> Investor ID defined above
       accountNo -> Same as account number
       accountOpenDate -> Date on which this account was opened
       accountCloseDate -> Date on which this account was closed. 'NA' means active a/c
       retailInvestor -> 'true' means retail investor

3. Security lot: This provides the buying information of a security/stock at a particular point in time. An account may 
have multiple such lots at a given time the aggregation of which will provide the total portfolio value.

    Key format: `trading:securitylot:<accountNo>:<securityLotId>`
    ```json
    {
      "id": "SC61239693",
      "accountNo": "ACC10001", 
      "ticker": "ABCBANK",  
      "date": 1665082800, 
      "price": 14500.00, 
      "quantity": 10, 
      "lotValue": 145000,
      "type": "EQUITY"         
    }
    ```
   
       id -> unique identifier of the security lot
       accountNo -> Account number against which the lot was bought
       ticker -> Unique stock ticker code listed in stock exchange
       date -> Date on which this lot was bought
       price -> Price at which the lot was bought. This would be an integer. 
                We will use the lowest possible currency denomination (Cents, Paisa etc). For that, we will multiply the value by 100.
       quantity -> Total quantity of the lot
       lotValue -> Transaction value of the stocks (price * quantity)
       type -> Type of security. For our case, it would be 'EQUITY'
 

4. Stock: This holds the information of the security or stock listed at the stock exchange. We will hold very basic details like name, code etc

    Key format: `trading:stock:<stockId>`
```json
    {
      "id": "NSE623846333",
      "stockCode": "ABCBANK",
      "isin": "INE211111034",
      "stockName": "ABC Bank",
      "description": "Something about ABC bank",
      "dateOfListing": "08/11/1995",
      "active": true
    }
```

       id -> Unique identifier of the security stock
       stockCode -> Unique code of the stock used for trading
       stockName -> Name of the stock
       description -> Description of the stock
       active -> If the stock is available for trading
       
       
![class_trading drawio](https://user-images.githubusercontent.com/26322220/188601634-be8d8622-9d88-4973-9994-1113854cae05.png)



## Use cases

1. Create a DB on Redis Cloud subscription OR DB on Redis Software OR Redis Stack database.

2. Goto the home directory of the application and follow the below steps (Replace the HOST, PASSWORD & PASSWORD field with the correct values):

### Securities & portfolio management

In this scenario, we will create the aforementioned data models like investors, accounts, security_lot etc.
We will use `data_generators/generator_redis.py` to generate these entity models.

Component diagram:

![portfolio_transactions.png](files/images/portfolio_transactions.png)


The sequence of steps:

1. Install necessary libraries


    ```python
    source venv/bin/activate
    pip3 install -r requirements.txt
    ```

2. Ingest the sample security transaction records using the following python script:

   ```python
   HOST=localhost PASSWORD=admin PORT=6379 ACCOUNT_RECORD_COUNT=1000 python data_generators/generator_redis.py
   ```

   By default, 1k account data will be generated.
   To change this, modify '**ACCOUNT_RECORD_COUNT**' env variable
    
   The following files will be used to create the transaction records for the user:
    
    ```python
    files/for_tnxs/ABCBANK.csv
    files/for_tnxs/ABCMOTORS.csv
    ```
    
   Execute this script using Docker command:
    
    ```python
    docker run -e HOST=<HOST> -e PORT=<PORT> -e PASSWORD=<PASSWORD> -e ACCOUNT_RECORD_COUNT=1000 abhishekcoder/securities_portfolio_app:generator

    ```

3. Next, we would be leveraging Redis Query Engine to provide full-text indexing capabilities on JSON 
   documents. We will execute the following secondary indexes:


        FT.CREATE idx_trading_security_lot 
            on JSON PREFIX 1 trading:securitylot: 
        SCHEMA 
            $.accountNo as accountNo TEXT 
            $.ticker as ticker TAG 
            $.price as price NUMERIC SORTABLE 
            $.quantity as quantity NUMERIC SORTABLE 
            $.lotValue as lotValue NUMERIC SORTABLE 
            $.date as date NUMERIC SORTABLE


        FT.CREATE idx_trading_account 
            on JSON PREFIX 1 trading:account: 
        SCHEMA 
            $.accountNo as accountNo TEXT 
            $.retailInvestor as retail investor TAG 
            $.accountOpenDate as accountOpenDate TEXT    

4. Now, let's test the scenario by executing the following queries using either redis-cli or RedisInsight tool:

   * Get all the security lots by account number/ID

         FT.SEARCH idx_trading_security_lot '@accountNo: (ACC10001)'

   * Get all the security lots by account number/ID and ticker

         FT.SEARCH idx_trading_security_lot '@accountNo: (ACC10001) @ticker:{ABCMOTORS}'

   * Get the total quantity of all securities inside the investor's security portfolio

         FT.AGGREGATE idx_trading_security_lot '@accountNo: (ACC10001)' GROUPBY 1 @ticker REDUCE SUM 1 @quantity as totalQuantity

   * Get the total quantity of all securities inside the investor's security portfolio at a particular time

         FT.AGGREGATE idx_trading_security_lot '@accountNo:(ACC10001) @date: [0 1725186610]' GROUPBY 1 @ticker REDUCE SUM 1 @quantity as totalQuantity

   * Get the average cost price of the owned stock at a given date and time. If the current price of the stock is known, this can also provide the profit and loss information.

         FT.AGGREGATE idx_trading_security_lot '@accountNo:(ACC10001) @date:[0 1725186610]' groupby 1 @ticker reduce sum 1 @lotValue as totalLotValue reduce sum 1 @quantity as totalQuantity apply '(@totalLotValue/(@totalQuantity*100))' as avgPrice

   * Get total portfolio value across all the stocks owned by a given account number.

         FT.AGGREGATE idx_trading_security_lot '@accountNo:(ACC10001)' groupby 1 @ticker reduce sum 1 @lotValue as totalLotValue apply '(@totalLotValue/100)' as portfolioFolioValue


******************************************************

### Dynamic stock pricing - Streams & Time series

Stock price data is highly volatile and requires a real-time data platform to handle this use case. To address this requirement, we will use 
leverage Streams & Timeseries to store the historical and current stock prices.

The following files (for ABCBANK & ABCMOTORS) are used to push the pricing data into Streams in Redis:

    files/for_pricing_data/ABCBANK_intraday.csv
    files/for_pricing_data/ABCMOTORS_intraday.csv

The sequence of steps:
There are 2 parts here: Pricing data ingestion & Pricing data processing

The component diagram:

![stock_pricing.png](files/images/stock_pricing.png)

#### A. Pricing Data - Ingestion

1. Install the pre-requisites 


    ```python
    source venv/bin/activate
    pip3 install -r requirements.txt
    ```

2. We will ingest the intra-day price changes for these securities into Redis Enterprise.:

    ```python
    HOST=localhost PASSWORD=admin PORT=6379 TEST_STOCKS=ABCBANK,ABCMOTORS python price_producer/price_producer.py
    ```

   The files used to generate intra-day pricing data are presented here:

    ```python
    files/for_pricing_data/ABCBANK_intraday.csv
    files/for_pricing_data/ABCMOTORS_intraday.csv
    ```

   The above script will push pricing details into the `price_update_stream` stream.

    ```python
    XADD STREAMS * price_update_stream {"ticker":"ABCBANK", "datetime": "02/09/2022 9:00:07 AM", "price": 1440.0}
    ```


   Execute this script using Docker command:

    ```python
    docker run -e HOST=<HOST> -e PORT=<PORT> -e PASSWORD=<PASSWORD> abhishekcoder/securities_portfolio_app:price_producer
    ```
    


#### B. Pricing Data - Processing

These dynamic pricing data will be consumed asynchronously by a Streams consumer. The code for streams consumer is present
in the '/consumer/pricing-deaggregator' folder and written using Java 21 & Spring Boot.

The docker image for the consumer is: `abhishekcoder/securities_portfolio_app:deaggregator`

This consumer performs the following responsibilities:

      1. Consuming the pricing data, remodelling it and disaggregating it based on the stock ticker
      2. Create Timeseries compaction rules (Open, high, Close, Low) based on defined bucket size (default is 5 sec) 
      3. Pushes this pricing info to the RedisTimeSeries database in the following key format --> `'price_history_ts:<STOCK_TICKER>'`
      4. This also creates a price notification stream. This may be used by the notification engine to send pricing alerts to users.
      5. [Optional] Push the latest pricing info into a Pub-Sub channel so that the active clients/investors who have subscribed can get the latest pricing notifications

Docker command to execute processor:

```python
docker run -e SPRING_REDIS_HOST=<HOST> -e SPRING_REDIS_PORT=<PORT> -e SPRING_REDIS_PASSWORD=<PASSWORD> -e TEST_STOCKS=ABCBANK,ABCMOTORS abhishekcoder/securities_portfolio_app:deaggregator
```

Java command to execute the processor:
```python
java -jar consumer/pricing-deaggregator/target/demo.streams.consumer-0.0.1-SNAPSHOT.jar --env spring.redis.password=<PASSWORD> TEST_STOCKS=ABCBANK,ABCMOTORS
```

This consumer will create a Timeseries key for tracking the price for the security & update the pricing info in the Timeseries db whenever it arrives:

    TS.CREATE price_history_ts:ABCBANK ticker ABCBANK DUPLICATE_POLICY LAST
    TS.ADD price_history_ts:ABCBANK 1352332800 635.5

Since the RedisTimeSeries database contains all the pricing data for a particular security, we can write some RedisTimeSeries
queries to get the pricing trend, current price, and price aggregation over time. We can also use the downsampling feature to 
get the trend by days, weeks, months, years etc.

#### Get the latest price for a ticker

    TS.GET price_history_ts:ABCBANK

#### Get the price info between two dates/times for a ticker
    
    TS.RANGE price_history_ts:ABCBANK 1352332800 1392602800

#### Create a rule for the daily average price for a particular security

    TS.CREATERULE price_history_ts:ABCBANK price_history_ts:ABCBANK_AGGR AGGREGATION avg 86400000

******************************************************

### Historical ticker price & volume - Timeseries

One of the important use cases of the financial industry is to track and get deeper insights from the historical stock price
and the volume traded each trading day.
Time series data structure provided by Redis provides a real-time data structure using which we can achieve on-demand 
access to the pricing data at any point in time.

Component diagram:

![report.png](files/images/report.png)

The sequence of steps:


1. Install the pre-requisites 

    ```python
    source venv/bin/activate
    pip3 install -r requirements.txt
    ```

2. We will ingest the historic pricing data using this script:

    ```python
    HOST=localhost PASSWORD=admin PORT=6379 python data_generators/report.py
    ```

   The above script will ingest the data for the last 10 years for the following stocks in timeseries data structure:

    ```python
    files/for_report/ABCBANK.csv
    files/for_report/ABCMOTORS.csv
    ```

   Execute this script using Docker command:

    ```python
    docker run -e HOST=<HOST> -e PORT=<PORT> -e PASSWORD=<PASSWORD> abhishekcoder/securities_portfolio_app:report
    ```

******************************************************

### Visualise the complete app

To visualise this on the browser, run the `server.py` script included in this repo. When successfully executed, open 
[http://localhost:5555](http://localhost:5555) and observe the data in action. 
You will see the current price, day low, day high and the intra-day trend.

Execute as a Python script:

```python
HOST=localhost PASSWORD=admin PORT=6379 report=True ticker_trend=True notification=True transactions=True TEST_STOCKS=ABCBANK,ABCMOTORS python server.py
```

Execute this script using Docker command:

```python
docker run -e HOST=<HOST> -e PORT=<PORT> -e PASSWORD=<PASSWORD> \
            -e ticker_trend=True \
            -e report=True \
            -e notification=True \
            -e transactions=True \
            -e TEST_STOCKS=ABCBANK,ABCMOTORS \
abhishekcoder/securities_portfolio_app:server
```


The following diagram shows how data flows in and out of the system and how different pieces stitch 
together. 

![architecture.png](files/images/architecture.png)

******************************************************


### Run everything using docker-compose
We can execute the entire application stack using docker-compose. 
The `docker-compose.yaml` file is present in the application directory.
There are various env variables which can be set. 
Change the desired variables in the `docker-compose-redis-variables.env` file before executing the 'docker compose up' command. 

    HOST
    PASSWORD
    PORT

Apart from the above, the following feature flag can also be set. This will help to enable/disable a particular feature.
For instance, to disable the Notification and Reporting feature (historical pricing in timeseries), set these env variables:
    
    ticker_trend=True
    report=False
    notification=False
    transactions=True

Wait for a minute and 
open http://localhost:5555 to check the result.

`docker compose up`

To shut down the applications, execute this command:

`docker compose down`


