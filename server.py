import redis
from flask_sock import Sock
import time
import json
from datetime import datetime
from flask import Flask, redirect, url_for, request, render_template

global app


r = redis.Redis(host='localhost', port=6379, decode_responses=True)
app = Flask(__name__)
sock = Sock(app)
ts = r.ts()


@app.route('/')
def overview():
    return render_template('overview.html')


@sock.route('/price/<ticker>')
def price(sock, ticker):
    print(ticker)
    currentPrice = 0;
    minPrice = 0;
    maxPrice = 0
    while True:
        key = "price_history_ts:" + ticker
        currentPriceArr = ts.get(key)
        minPriceArr = ts.range(key=key, from_time="-", to_time="+", aggregation_type="min", bucket_size_msec=86400000)
        maxPriceArr = ts.range(key=key, from_time="-", to_time="+", aggregation_type="max", bucket_size_msec=86400000)
        if len(currentPriceArr) > 0:
            currentPrice = currentPriceArr[1]
        if len(minPriceArr) > 0:
            minPrice = minPriceArr[0][1]
        if len(maxPriceArr) > 0:
            maxPrice = maxPriceArr[0][1]
        # data = sock.receive()
        data = json.dumps(
            {"currentPrice": currentPrice, "minPrice": minPrice, "maxPrice": maxPrice, "stockSymbol": ticker})
        sock.send(data)
        time.sleep(3)


@sock.route('/intraday-trend/<ticker>')
def intraDayTrend(sock, ticker):
    print(ticker)
    price = []
    timeTrend = []
    startTime = str(datetime.now().date()) + " 09:00:00"
    startTimeTs = int(time.mktime(time.strptime(startTime, '%Y-%m-%d %H:%M:%S')))
    endTime = 0
    key = "price_history_ts:" + ticker
    while True:
        print("invloking TS.GET with " + str(startTimeTs))
        priceTrend = ts.range(key=key, from_time=startTimeTs, to_time='+')
        for item in priceTrend:
            endTime = item[0]
            timeTrend.append(datetime.fromtimestamp(item[0]).strftime('%Y-%m-%d %H:%M:%S'))
            price.append(item[1])
        data = json.dumps({"price": price, "timeTrend": timeTrend})
        startTimeTs = endTime
        price = []
        timeTrend = []
        sock.send(data)
        time.sleep(3)


if __name__ == '__main__':
    app.run(debug=True)
