import redis
from flask_sock import Sock
import time
import json
from datetime import datetime
from flask import Flask, redirect, url_for, request, render_template
from jproperties import Properties
import os

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
        print("invloking TS.GET with " + str(startTimeTs))
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5555)
