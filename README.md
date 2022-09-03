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
      "id": "INV10001", # unique identifier of the investor
      "name": "Johny M.", --> Name of the investor
      "uid": "", --> Unique government id (SSN, Aadhaar etc)
      "pan": "" --> Unique taxpayer id provided by government (in India)
    }
    ```
2. Account: This is the unique trading account of the investor. An investor can have multiple account against which the investment might have been made. 
  We will stick to only one account per investor in this demo

    ```json
    {
      "id": "ACC10001", # unique identifier of the investor,
      "investorId": "INV10001", --> Investor id defined above,
      "accountNo": "ACC10001", --> Same as account number
      "accountOpenDate": "20/11/2018", --> Date on which this account was opened
      "accountCloseDate": "NA", --> Date on which this account was closed. 'NA' means active a/c
      "retailInvestor": true --> 'true' means retail investor
    }
    ```
3. Security lot: This provides the buying information of a security/stock at a particular point in time. An account may 
have multiple such lots at a given time the aggregation of which will provide the total portfolio value.
    ```json
    {
      "id": "SC61239693", --> unique identifier of the security lot,
      "accountNo": "ACC10001", --> Account number against which the lot was bought,
      "ticker": "HDFCBANK", --> Unique stock ticker code listed in stock exchange 
      "date": "20/11/2018", --> Date on which this lot was bought
      "price": 14500, --> Price at which the lot was bought. This would be integer. 
                          We will use lowest possible currency denomination (Cents, Paisa etc)
      "quantity": 10,--> Total quantity of the lot
      "type": "EQUITY" --> Type of security. For our case, it would be 'EQUITY'        
    }
    ```
4. Stock: This holds the information of the security or stock listed at the stock exchange. We will hold very basic details like name, code etc
```json
{
  "id": "NSE623846333", --> Unique identifier of the security stock
  "stockCode": "HDFCBANK" --> Unique code of the stock used for trading
  "stockName": "HDFC Bank" --> Name of the stock   
  "description": "Something about HDFC bank" --> Description of the stock
  "active": true --> If the stock is available for trading 
}
```

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
This consumer performs following responsibilities:
1. Consuming the pricing data, remodeling it and disaggregating it based on the stock ticker
2. Pushes these pricing info to RedisTimeSeries database in the following key format --> `'price_history_ts:<STOCK_TICKER>'`

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

