import redis
import time
import pandas as pd
from jproperties import Properties
import threading
import os

configs = Properties()
with open('./config/app-config.properties', 'rb') as config_file:
    configs.load(config_file)

def ingestionTask(stock, price_stream_name, priceCol):
    try:
        data = pd.read_csv("files/" + stock + "_intraday.csv")
        for i in data.index:
            dateInUnix = int(time.mktime(time.strptime(data['DateTime'][i], configs.get("DATE_FORMAT").data)))
            conn.xadd(price_stream_name,
                      {"ticker": stock,
                       "datetime": data['DateTime'][i],
                       "dateInUnix": dateInUnix,
                       "price": data[priceCol][i]})
            print(str(i+1)+" pricing record generated for "+stock)
            time.sleep(0.5)
        print("Trading recordset generated")
    except Exception as inst:
        print(type(inst))
        print("Exception occurred while generating pricing data"+data[priceCol][i])
        print(data)
        #raise Exception('Exception occurred while generating pricing data. Delete the corrupted data and try again')


if __name__ == '__main__':

    conn = redis.Redis(host=os.getenv('HOST', "redis-14675.c301.ap-south-1-1.ec2.cloud.redislabs.com"),
                       port=os.getenv('PORT', 14675),
                       password=os.getenv('PASSWORD', "admin"))
    if not conn.ping():
        raise Exception('Redis unavailable')
    price_stream_name = configs.get("PRICE_STREAM").data
    test_stocks = configs.get("TEST_STOCKS").data.split(',')

    for test_stock in test_stocks:
        stock = test_stock.strip()
        priceCol = stock + "EQN"
        t = threading.Thread(target=ingestionTask, args=(stock, price_stream_name, priceCol))
        t.start()
