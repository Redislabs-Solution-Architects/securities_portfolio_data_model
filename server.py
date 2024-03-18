import redis
from flask_sock import Sock
import time
import json
from datetime import datetime
from flask import Flask, redirect, url_for, request, render_template
from jproperties import Properties
import os
import copy
import logging

from redis.commands.search.field import NumericField, TextField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import NumericFilter, Query
import redis.commands.search.aggregation as aggregations
import redis.commands.search.reducers as reducers


global app


configs = Properties()
with open('./config/app-config.properties', 'rb') as config_file:
    configs.load(config_file)
r = redis.Redis(host=os.getenv('HOST', "localhost"),
                port=os.getenv('PORT', 6379),
                password=os.getenv('PASSWORD', "admin"),
                decode_responses=True)
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

    # totalSecurityCount
    req = (aggregations.AggregateRequest(f"@accountNo: ({account})")
           .group_by(['@ticker'], reducers.sum('@quantity').alias('totalQuantity')))
    res = r.ft("idx_trading_security_lot").aggregate(req).rows

    totalSecurityCount = []
    for rec in res:
        totalSecurityCount.append(rec[1] + " [" + format(int(rec[3]), ',')+"]</br>")
    result['totalSecurityCount'] = totalSecurityCount

    # totalSecurityCountByTime
    req = (aggregations.AggregateRequest(f"@accountNo: ({account}) @date: [0 1665082800]")
           .group_by(['@ticker'], reducers.sum('@quantity').alias('totalQuantity')))
    res = r.ft("idx_trading_security_lot").aggregate(req).rows
    totalSecurityCountByTime = []
    for rec in res:
        totalSecurityCountByTime.append(rec[1] + " [" + format(int(rec[3]), ',')+"]</br>")
    result['totalSecurityCountByTime'] = totalSecurityCountByTime

    # avgCostPriceByTime
    req = (aggregations.AggregateRequest(f"@accountNo: ({account}) @date: [0 1665498506]")
           .group_by('@ticker', reducers.sum('@lotValue').alias('totalLotValue'), reducers.sum('@quantity').alias('totalQuantity'))
           .apply(avgPrice="@totalLotValue/(@totalQuantity*100)"))

    res = r.ft("idx_trading_security_lot").aggregate(req).rows
    avgCostPriceByTime = []
    for rec in res:
        avgCostPriceByTime.append(rec[1] + " [INR " + format(float(rec[7]), ',.2f')+"]</br>")
    result['avgCostPriceByTime'] = avgCostPriceByTime

    # portfolioValue
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
            timeTrend.append(datetime.fromtimestamp(item[0]).strftime(configs.get("DATE_FORMAT").data))
            price.append(item[1])
        data = json.dumps({"price": price, "timeTrend": timeTrend})
        startTimeTs = endTime
        price = []
        timeTrend = []
        sock.send(data)
        time.sleep(3)


def createIndexes():
    # Creating index having definition::
    # FT.CREATE idx_trading_security_lot on JSON PREFIX 1 trading:securitylot:
    # SCHEMA $.accountNo as accountNo TEXT
    # $.ticker as ticker TAG
    # $.price as price NUMERIC SORTABLE
    # $.quantity as quantity NUMERIC SORTABLE
    # $.date as date NUMERIC SORTABLE
    schema = (TextField("$.accountNo", as_name="accountNo"),
              TagField("$.ticker", as_name="ticker"),
              NumericField("$.price", as_name="price", sortable=True),
              NumericField("$.quantity", as_name="quantity", sortable=True),
              NumericField("$.date", as_name="date", sortable=True))
    r.ft("idx_trading_security_lot").create_index(schema, definition=IndexDefinition(prefix=["trading:securitylot:"],
                                                                                     index_type=IndexType.JSON))
    # Creating index having definition::
    # FT.CREATE idx_trading_account on JSON PREFIX 1 trading:account:
    # SCHEMA $.accountNo as accountNo TEXT
    # $.address as address TEXT
    # $.retailInvestor as retailInvestor TAG
    # $.accountOpenDate as accountOpenDate TEXT
    schema = (TextField("$.accountNo", as_name="accountNo"),
              TextField("$.address", as_name="address"),
              TagField("$.retailInvestor", as_name="retailInvestor"),
              TextField("$.accountOpenDate", as_name="accountOpenDate"))
    r.ft("idx_trading_account").create_index(schema, definition=IndexDefinition(prefix=["trading:account:"],
                                                                                index_type=IndexType.JSON))
    print("Created indexes: idx_trading_security_lot, idx_trading_account")


if __name__ == '__main__':
    try:
        createIndexes()
    except Exception as inst:
        logging.warning("Exception occurred while creating indexes")
    app.run(host='0.0.0.0', debug=True, port=5555)
