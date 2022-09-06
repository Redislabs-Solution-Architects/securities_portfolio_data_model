# Sample Trading data model

### Data model

Here we will talk about a sample trading data model. The whole idea is what representational technique we choose to store our model
and how efficient that technique would be. Needless to mention, this decision becomes more critical when we are implementing the
trading system. Since, it is imperative to guarantee minimal response time, higher throughput and efficient data structures, we will 
use Redis Enterprise for this purpose. 
Specifically, RedisJSON as our modeling engine and RediSearch as full-text and secondary indexing engine.

1. Investor: This would typically be any type of investor, like retail, corporation etc. Let's choose a retail investor for that matter.
    ```json
    {
      "id": "INV10001", 
      "name": "Johny M.", 
      "uid": "35178235834", 
      "pan": "AHUIOHO684" 
    }
    ```

       id -> unique identifier of the investor
       name -> Name of the investor
       uid -> Unique government id (SSN, Aadhaar etc)
       pan -> Unique taxpayer id provided by government (in India)
   
2. Account: This is the unique trading account of the investor. An investor can have multiple account against which the investment might have been made. 
  We will stick to only one account per investor in this demo

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
       investorId -> Investor id defined above
       accountNo -> Same as account number
       accountOpenDate -> Date on which this account was opened
       accountCloseDate -> Date on which this account was closed. 'NA' means active a/c
       retailInvestor -> 'true' means retail investor

3. Security lot: This provides the buying information of a security/stock at a particular point in time. An account may 
have multiple such lots at a given time the aggregation of which will provide the total portfolio value.
    ```json
    {
      "id": "SC61239693",
      "accountNo": "ACC10001", 
      "ticker": "HDFCBANK",  
      "date": "20/11/2018", 
      "price": 14500, 
      "quantity": 10, 
      "type": "EQUITY"         
    }
    ```
   
       id -> unique identifier of the security lot
       accountNo -> Account number against which the lot was bought
       ticker -> Unique stock ticker code listed in stock exchange
       date -> Date on which this lot was bought
       price -> Price at which the lot was bought. This would be integer. 
                We will use lowest possible currency denomination (Cents, Paisa etc)
       quantity -> Total quantity of the lot
       type -> Type of security. For our case, it would be 'EQUITY'

4. Stock: This holds the information of the security or stock listed at the stock exchange. We will hold very basic details like name, code etc
```json
    {
      "id": "NSE623846333",
      "stockCode": "HDFCBANK",
      "isin": "INE040A01034",
      "stockName": "HDFC Bank",
      "description": "Something about HDFC bank",
      "dateOfListing": "08/11/1995",
      "active": true
    }
```

       id -> Unique identifier of the security stock
       stockCode -> Unique code of the stock used for trading
       stockName -> Name of the stock
       description -> Description of the stock
       active -> If the stock is available for trading

### Sample operations on the model 
In a typical trading use case, there can be and there will be multiple use cases. Where one hand we may have very trivial 
operations like fetching the investor details, getting account details etc then on the other hand we may see quite complicated queries as well like:
getting the value of the securities an investor holds at a time, getting average cost price of the stocks purchased and so on.
We will build queries for:
1. Get all the security lots by account number/id
2. Get all the security lots by account number/id and ticker
3. Get avg cost price and total quantity of all security inside investor's security portfolio

Above use cases can be solved if we create suitable RediSearch indexes in our Redis cluster.
Following are the 2 indexes and the corresponding queries which does that:

    FT.CREATE idx_trading_security_lot on JSON PREFIX 1 trading:securitylot: SCHEMA $.accountNo as accountNo TEXT 
    $.ticker as ticker TAG $.price as price NUMERIC $.quantity as quantity NUMERIC $.type as type TAG
    
    FT.CREATE idx_trading_account on JSON PREFIX 1 trading:account: SCHEMA $.accountNo as accountNo TEXT 
    $.retailInvestor as retailInvestor TAG $.accountOpenDate as accountOpenDate TEXT 

#### Queries 
1. Get all the security lots by account number/id
     * `FT.SEARCH idx_trading_security_lot '@accountNo: (ACC10001)' `
2. Get all the security lots by account number/id and ticker
     * `FT.SEARCH idx_trading_security_lot '@accountNo: (ACC10001) @ticker:{HDFCBANK}'` 
3. Get avg cost price and total quantity of all security inside investor's security portfolio
     * `FT.AGGREGATE idx_trading_security_lot '@accountNo: (ACC10001)' GROUPBY 1 @ticker REDUCE AVG 1 @price as avgPrice REDUCE SUM 1 @quantity as totalQuantity`


### Dynamic pricing and storage
Stock pricing data is very dynamic and changes a lot during while trade is active. To address this problem we will use 
RedisTimeSeries to store the historical and the current stock prices.

This repo contains the actual intra-day prices for few stocks (HDFCBANK, MARUTI) taken from https://www.nseindia.com/
in [files/HDFCBANK_intraday.csv](https://github.com/bestarch/sample_trading_data_model/blob/main/files/HDFCBANK_intraday.csv) 
and [files/MARUTI_intraday.csv](https://github.com/bestarch/sample_trading_data_model/blob/main/files/MARUTI_intraday.csv)

* Using [price_producer.py](https://github.com/bestarch/sample_trading_data_model/blob/main/price_producer.py) we will ingest the intra-day price changes for these securities into Redis Enterprise.

* The script will push these changes into Redis Streams in a common stream `price_update_stream`.


        XADD STREAMS * price_update_stream {"ticker":"HDFCBANK", "datetime": "02/09/2022 9:00:07 AM", "price": 1440.0}


* These dynamic pricing data will be consumed asynchronously by a Streams consumer. The code for streams consumer is present
in '/demo' folder and written using Java, Spring etc.
The docker image for the consumer is: `abhishekcoder/demo.streams.consumer`
This consumer performs following responsibilities:

  1. Consuming the pricing data, remodeling it and disaggregating it based on the stock ticker
  2. Pushes these pricing info to RedisTimeSeries database in the following key format --> `'price_history_ts:<STOCK_TICKER>'`
  3. Push the latest pricing info into a Pub-Sub channel so that the active clients/investors who have subscribed can get the latest pricing notifications


#### Create Time series key for tracking price for a security
    TS.CREATE price_history_ts:HDFCBANK ticker hdfcbank DUPLICATE_POLICY LAST

#### Adding pricing information for a security
    TS.ADD price_history_ts:HDFCBANK 1352332800 635.5

Now, since the RedisTimeSeries database contains all the pricing data for a particular security, we can write some RedisTimeSeries
queries to get the pricing trend, current price, aggregation of the price overtime. We can also use downsampling feature to 
get the trend by days, weeks, months, years etc.

#### Some common timeseries operations
Get latest price for a ticker

    TS.GET price_history_ts:HDFCBANK

Get the price info between two dates/times for a ticker
    
    TS.RANGE price_history_ts:HDFCBANK 1352332800 1392602800

Create rule for daily average price for a particular security

    TS.CREATERULE price_history_ts:HDFCBANK price_history_ts:HDFCBANK_AGGR AGGREGATION avg 86400000

## Data flow
Following diagram shows how data flows in and out of the system and how different pieces stitch 
together to provide the complete picture. 

![](/Users/abhishek/apps/BFSI/trading.drawio.png)


## Steps in sequence
Execute following steps to run this demo:

1. To test our investore, account, security_lot data models, we need to add some test data. For that purpose,
   let's execute `generator.py`. This will add some test intra-day data for HDFCBANK and MARUTI securities.

2. Next we will execute following RediSearch indexes before actually running any queries:


    FT.CREATE idx_trading_security_lot on JSON PREFIX 1 trading:securitylot: SCHEMA $.accountNo as accountNo TEXT $.ticker as ticker TAG $.price as price NUMERIC $.quantity as quantity NUMERIC $.type as type TAG
    
    FT.CREATE idx_trading_account on JSON PREFIX 1 trading:account: SCHEMA $.accountNo as accountNo TEXT $.retailInvestor as retailInvestor TAG $.accountOpenDate as accountOpenDate TEXT 

3. Now, we can execute the queries to test our data model. The first part of this exercise/demo is complete:
    1. Get all the security lots by account number/id
        * `FT.SEARCH idx_trading_security_lot '@accountNo: (ACC10001)' `
    2. Get all the security lots by account number/id and ticker
        * `FT.SEARCH idx_trading_security_lot '@accountNo: (ACC10001) @ticker:{HDFCBANK}'` 
    3. Get avg cost price and total quantity of all security inside investor's security portfolio
        * `FT.AGGREGATE idx_trading_security_lot '@accountNo: (ACC10001)' GROUPBY 1 @ticker REDUCE AVG 1 @price as avgPrice REDUCE SUM 1 @quantity as totalQuantity`

4. For the second part, we will test the dynamic pricing and storage use case of securities. 
   For that start the Redis Streams consumer using following docker command. (You may also execute directly via any IDE like STs,IntelliJ etc).
      If successfully started, this will wait for any pricing signals.


        docker run -p 127.0.0.1:8080:8080 -e SPRING_REDIS_HOST=<HOST> -e SPRING_REDIS_PORT=<PORT> -e SPRING_REDIS_PASSWORD=<PASSOWRD>> abhishekcoder/demo.streams.consumer:latest
5. Next, push the pricing changes into the Redis Streams. For this run the price_producer.py.
   If successfully started, it will start pushing the ticker prices into the Redis Streams.
6. You may notice, the stream consumer we started in step 1 will begin to process the messages and will push them 
   to RedisTimeSeries database.
7. Execute following command to get the latest price:


        TS.GET price_history_ts:HDFCBANK

8. Now since the historic prices are populated in timeseries database, we can get the price info between two dates/times for a ticker


        TS.RANGE price_history_ts:HDFCBANK 1352332800 1392602800
