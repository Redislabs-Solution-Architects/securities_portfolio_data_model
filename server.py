import redis
from flask_sock import Sock
import time
from datetime import datetime, timedelta
import json
from datetime import datetime
from flask import Flask, redirect, url_for, request, render_template
from jproperties import Properties
import copy
import logging
import sys
import os

import uuid
sys.path.append(os.path.abspath('redis_connection'))
from connection import RedisConnection

from redis.commands.search.field import NumericField, TextField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import NumericFilter, Query
import redis.commands.search.aggregation as aggregations
import redis.commands.search.reducers as reducers

global app

configs = Properties()
logger = logging.getLogger(__name__)
logging.basicConfig(encoding='utf-8', level=logging.INFO)

with open('config/app-config.properties', 'rb') as config_file:
    configs.load(config_file)

r = RedisConnection().get_connection()
app = Flask(__name__)
sock = Sock(app)
ts = r.ts()


@app.route('/')
def overview():
    return render_template('overview.html')

@app.route('/stock-stats',methods = ['POST'])
def getstats():
    stock = request.form['stockSelector']
    return render_template('overview.html', stock=stock)

@app.route('/portfolio-detail')
def portfolioDetail():
    return render_template('portfolio.html')


@app.route('/alerts')
def alerts():
    return render_template('alerts.html')


@app.route('/newAlert', methods=['POST'])
def newAlert():
    stock = request.form['stock']
    triggerType = request.form['triggerType']
    triggerPrice = request.form['triggerPrice']
    alert = {
        "stock": stock,
        "triggerType": triggerType,
        "triggerPrice": triggerPrice,
        "dateTime": int(time.time()),
        "active": True
    }
    print(f"Creating {triggerType} alert for {stock} with trigger price {triggerPrice} --> {json.dumps(alert)}.")
    r.json().set(f'alert:rule:{stock}', "$", alert)
    # r.set("stocks_with_rules", stock)
    return redirect(url_for('alerts'))


@app.route('/deleteRule', methods=['POST'])
def deleteRule():
    ruleId = request.form['ruleId']
    print(f"Deleting rule having Id {ruleId}")
    r.delete(ruleId)
    # r.srem("stocks_with_rules", ruleId.split(":")[2])
    return redirect(url_for('alerts'))


@app.route('/system-alerts')
def systemAlerts():
    keys = []
    cursor = 0
    while True:
        cursor, alertKey = r.scan(cursor, match="alert:rule:*", count=10)
        keys.extend(alertKey)
        if cursor == 0:
            break

    results = []
    for k in keys:
        doc = r.json().get(k)
        doc.update({"key": k})
        results.append(doc)

    results = {'data': results}
    print(results)
    json_data = json.dumps(results)
    return json_data


def tnxResultsTemp(request):
    account = request.args.get("account")
    stock = request.args.get("stock")
    investor = request.args.get("investor")
    results = []
    result = {}
    result['accountNo'] = account
    result['accHolderName'] = 'M Radha'
    result['ticker'] = stock
    result['date'] = '20/11/2020'
    result['price'] = '2500'
    result['quantity'] = '100'
    for i in range(20):
        results.append(copy.deepcopy(result))
    results = {'data': results}
    json_data = json.dumps(results)
    return json_data


def tnxResults(request):
    #########################################
    ## Query used: FT.SEARCH idx_trading_security_lot '@accountNo: (ACC10001) @ticker:{RDBMOTORS}'
    #########################################
    account = request.args.get("account")
    stock = request.args.get("stock")
    #investor = request.args.get("investor")
    qry = ''
    if account:
        qry = f"@accountNo: ({account}*)"
    if stock:
        qry = qry + " @ticker: {"+stock+"*}"

    print("Generated query string: "+qry)
    query = (Query(qry).paging(0, 100))
    time1 = time.time()
    docs = r.ft("idx_trading_security_lot").search(query).docs
    time2 = time.time()
    print(f"List of transactions retrieved in {(time2-time1):.3f} seconds")

    result = []
    for doc in docs:
        result.append(json.loads(doc.json))
    #print(result)
    result = {'data': result}
    return result


@app.route('/transactions')
def transactions():
    return tnxResults(request)

@app.route('/accountstats')
def accountstats():
    account = request.args.get("account")
    result = {}

    ## Get the count of securities for a given account number
    ## Query used:
    ##       FT.AGGREGATE idx_trading_security_lot '@accountNo: (ACC10001)' GROUPBY 1 @ticker REDUCE SUM 1 @quantity as totalQuantity
    req = (aggregations.AggregateRequest(f"@accountNo: ({account})")
           .group_by(['@ticker'], reducers.sum('@quantity').alias('totalQuantity')))
    res = r.ft("idx_trading_security_lot").aggregate(req).rows

    totalSecurityCount = []
    for rec in res:
        totalSecurityCount.append(rec[1] + " [" + format(int(rec[3]), ',')+"]</br>")
    result['totalSecurityCount'] = totalSecurityCount

    ## Get the count of securities upto a given time for a provided account number
    ## Query used:
    ##       FT.AGGREGATE idx_trading_security_lot '@accountNo:(ACC10001) @date: [0 1665082800]' GROUPBY 1 @ticker REDUCE SUM 1 @quantity as totalQuantity
    req = (aggregations.AggregateRequest(f"@accountNo: ({account}) @date: [0 1665082800]")
           .group_by(['@ticker'], reducers.sum('@quantity').alias('totalQuantity')))
    res = r.ft("idx_trading_security_lot").aggregate(req).rows
    totalSecurityCountByTime = []
    for rec in res:
        totalSecurityCountByTime.append(rec[1] + " [" + format(int(rec[3]), ',')+"]</br>")
    result['totalSecurityCountByTime'] = totalSecurityCountByTime

    ## Get the average cost of each stocks for a given account number and time-frame
    ## Query used:
    ##       FT.AGGREGATE idx_trading_security_lot '@accountNo:(ACC10001) @date:[0 1665498506]' groupby 1 @ticker
    ##       reduce sum 1 @lotValue as totalLotValue reduce sum 1 @quantity as totalQuantity apply '(@totalLotValue/(@totalQuantity*100))' as avgPrice
    req = (aggregations.AggregateRequest(f"@accountNo: ({account}) @date: [0 1665498506]")
           .group_by('@ticker', reducers.sum('@lotValue').alias('totalLotValue'), reducers.sum('@quantity').alias('totalQuantity'))
           .apply(avgPrice="@totalLotValue/(@totalQuantity*100)"))

    res = r.ft("idx_trading_security_lot").aggregate(req).rows
    avgCostPriceByTime = []
    for rec in res:
        avgCostPriceByTime.append(rec[1] + " [INR " + format(float(rec[7]), ',.2f')+"]</br>")
    result['avgCostPriceByTime'] = avgCostPriceByTime

    ## get the total portfolio value for a given account number
    ## Query used:
    ##       FT.AGGREGATE idx_trading_security_lot '@accountNo:(ACC1000)' groupby 1 @ticker
    ##       reduce sum 1 @lotValue as totalLotValue apply '(@totalLotValue/100)' as portfolioFolioValue

    req = (aggregations.AggregateRequest(f"@accountNo: ({account})")
           .group_by([], reducers.sum('@lotValue').alias('totalLotValue'))
           .apply(portfolioValue="@totalLotValue/100"))

    res = r.ft("idx_trading_security_lot").aggregate(req).rows
    portfolioValue = []
    for rec in res:
        portfolioValue.append("INR " + format(float(rec[3]), ',.2f'))
    result['portfolioValue'] = portfolioValue

    data = json.dumps(result)
    return data

@sock.route('/price/<ticker>')
def price(sock, ticker):
    print(ticker)
    currentPrice = 0
    minPrice = 0
    maxPrice = 0
    key = configs.get("PRICE_HISTORY_TS").data + ":" + ticker
    while True:
        currentPriceArr = ts.get(key)
        minPriceArr = ts.range(key=key, from_time="-", to_time="+", aggregation_type="min", bucket_size_msec=86400000)
        maxPriceArr = ts.range(key=key, from_time="-", to_time="+", aggregation_type="max", bucket_size_msec=86400000)
        if len(currentPriceArr) > 0:
            currentPrice = currentPriceArr[1]
        if len(minPriceArr) > 0:
            minPrice = minPriceArr[0][1]
        if len(maxPriceArr) > 0:
            maxPrice = maxPriceArr[0][1]
        data = json.dumps(
            {"currentPrice": currentPrice, "minPrice": minPrice, "maxPrice": maxPrice, "stockSymbol": ticker})
        sock.send(data)
        time.sleep(3)


@sock.route('/intraday-trend/<ticker>')
def intraDayTrend(sock, ticker):
    print(ticker)
    price = []
    timeTrend = []
    #startTime = str(datetime.now().date()) + " 09:00:00"
    startTime = configs.get("START_TIME").data
    startTimeTs = int(time.mktime(time.strptime(startTime, configs.get("DATE_FORMAT").data)))
    endTime = 0
    key = configs.get("PRICE_HISTORY_TS").data + ":" + ticker
    while True:
        print("invoking TS.GET with " + str(startTimeTs))
        priceTrend = ts.range(key=key, from_time=startTimeTs, to_time='+')
        for item in priceTrend:
            endTime = item[0]
            timeTrend.append(datetime.fromtimestamp(int(item[0]/1000)).strftime(configs.get("DATE_FORMAT").data))
            price.append(item[1])
        data = json.dumps({"price": price, "timeTrend": timeTrend})
        startTimeTs = endTime
        price = []
        timeTrend = []
        sock.send(data)
        time.sleep(2)


@sock.route('/ohlc/<ticker>')
def candleStickChart(sock, ticker):
    print(f"Ticker selected:: {ticker}")
    key_prefix = "price_history_ts:" + ticker + ":"
    date_format = configs.get("DATE_FORMAT").data
    start_datetime_str = configs.get("START_TIME").data
    start_timestamp_millis = datetime.strptime(start_datetime_str, date_format).timestamp()*1000
    end_timestamp_millis = datetime.strptime("2024-07-04 15:15:00", date_format).timestamp()*1000

    #specific_datetime = datetime(2024, 7, 5, 9, 15, 0)
    #data = getTestData(specific_datetime)

    while True and start_timestamp_millis < end_timestamp_millis:
        datapoints_h = ts.range(key_prefix + "h", start_timestamp_millis, start_timestamp_millis+5)
        datapoints_l = ts.range(key_prefix + "l", start_timestamp_millis, start_timestamp_millis+5)
        datapoints_o = ts.range(key_prefix + "o", start_timestamp_millis, start_timestamp_millis+5)
        datapoints_c = ts.range(key_prefix + "c", start_timestamp_millis, start_timestamp_millis+5)

        if datapoints_h:
            ts_h, val_h = datapoints_h[0]
            ts_l, val_l = datapoints_l[0]
            ts_o, val_o = datapoints_o[0]
            ts_c, val_c = datapoints_c[0]

            item = {"x": ts_h, "o": val_o, "h": val_h, "l": val_l, "c": val_c}
            sock.send(json.dumps(item))
            time.sleep(2)

        start_timestamp_millis += 5


def getTestData(specific_datetime):
    data = [
        {"x": (specific_datetime + timedelta(seconds=10)).timestamp() * 1000, "o": 100, "h": 105, "l": 95, "c": 102},
        {"x": (specific_datetime + timedelta(seconds=20)).timestamp() * 1000, "o": 102, "h": 110, "l": 101, "c": 108},
        {"x": (specific_datetime + timedelta(seconds=30)).timestamp() * 1000, "o": 108, "h": 112, "l": 107, "c": 110},
        {"x": (specific_datetime + timedelta(seconds=40)).timestamp() * 1000, "o": 110, "h": 115, "l": 108, "c": 112},
        {"x": (specific_datetime + timedelta(seconds=50)).timestamp() * 1000, "o": 112, "h": 118, "l": 108, "c": 114},
        {"x": (specific_datetime + timedelta(seconds=60)).timestamp() * 1000, "o": 114, "h": 115, "l": 102, "c": 106},
        {"x": (specific_datetime + timedelta(seconds=70)).timestamp() * 1000, "o": 106, "h": 108, "l": 105, "c": 107},
        {"x": (specific_datetime + timedelta(seconds=80)).timestamp() * 1000, "o": 107, "h": 119, "l": 108, "c": 112},
    ]
    return data


@sock.route('/notification')
def notification(sock):
    streamName = configs.get("NOTIFICATION_STREAM").data
    notification_group = configs.get("NOTIFICATION_GROUP_NAME").data
    while True:
        try:
            # Read messages from the notification stream
            notifications = r.xreadgroup(notification_group, "notification_consumer", {streamName: '>'}, block=5000,
                                         count=5)
            temp = []
            for message in notifications:
                for message_id, fields in message[1]:
                    print(f"notification consumer:: Message ID: {message_id}")
                    message = fields.get('message')
                    temp.append(message)
                    r.xack(streamName, notification_group, message_id)
            data = json.dumps({"messages": temp, "count": len(temp)})
            sock.send(data)
            time.sleep(5)
        except Exception as e:
            print(f"Error: {e}")
            break


def createIndexes():
    try:
        # FT.CREATE idx_trading_security_lot on JSON PREFIX 1 trading:securitylot:
        # SCHEMA
        #   $.accountNo as accountNo TEXT
        #   $.ticker as ticker TAG
        #   $.price as price NUMERIC SORTABLE
        #   $.quantity as quantity NUMERIC SORTABLE
        #   $.lotValue as lotValue NUMERIC SORTABLE
        #   $.date as date NUMERIC SORTABLE
        schema = (TextField("$.accountNo", as_name="accountNo"),
                  TagField("$.ticker", as_name="ticker"),
                  NumericField("$.price", as_name="price", sortable=True),
                  NumericField("$.quantity", as_name="quantity", sortable=True),
                  NumericField("$.lotValue", as_name="lotValue", sortable=True),
                  NumericField("$.date", as_name="date", sortable=True))
        r.ft("idx_trading_security_lot").create_index(schema, definition=IndexDefinition(prefix=["trading:securitylot:"],
                                                                                         index_type=IndexType.JSON))
        # Creating index having definition::
        # FT.CREATE idx_trading_account on JSON PREFIX 1 trading:account:
        # SCHEMA
        #   $.accountNo as accountNo TEXT
        #   $.address as address TEXT
        #   $.retailInvestor as retailInvestor TAG
        #   $.accountOpenDate as accountOpenDate TEXT
        schema = (TextField("$.accountNo", as_name="accountNo"),
                  TextField("$.address", as_name="address"),
                  TagField("$.retailInvestor", as_name="retailInvestor"),
                  TextField("$.accountOpenDate", as_name="accountOpenDate"))
        r.ft("idx_trading_account").create_index(schema, definition=IndexDefinition(prefix=["trading:account:"],
                                                                                    index_type=IndexType.JSON))
        print("Created indexes: idx_trading_security_lot, idx_trading_account")
    except Exception as inst:
        logging.warning("Exception occurred while creating indexes")


def createNotificationStream():
    # Create the alert stream and the consumer group if they don't exist
    streamName = configs.get("NOTIFICATION_STREAM").data
    groupName = configs.get("NOTIFICATION_GROUP_NAME").data
    logging.info(f"Creating notification stream {streamName}")
    try:
        r.xgroup_create(streamName, groupName, id='0', mkstream=True)
    except redis.exceptions.ResponseError as e:
        # Ignore the error if the group already exists
        logging.warning("Exception occurred while creating notification stream")
        # traceback.print_exc()
        if "BUSYGROUP Consumer Group name already exists" not in str(e):
            raise


if __name__ == '__main__':
    createIndexes()
    createNotificationStream()
    app.run(host='0.0.0.0', debug=True, port=5555)
