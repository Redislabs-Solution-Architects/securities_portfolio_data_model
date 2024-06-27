import redis
import time
import pandas as pd
from jproperties import Properties
import threading
import os
import traceback

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
            time.sleep(1)
        print("Trading recordset generated")
    except Exception as inst:
        print(type(inst))
        print("Exception occurred while generating pricing data"+data[priceCol][i])
        print(data)
        #raise Exception('Exception occurred while generating pricing data. Delete the corrupted data and try again')


if __name__ == '__main__':
    try:
        password = 'admin'#os.getenv('PASSWORD')
        if not (password and password.strip()):
            conn = redis.Redis(host=os.getenv('HOST', "localhost"),
                               port=os.getenv('PORT', 6379),
                               decode_responses=True)
        else:
            conn = redis.Redis(host=os.getenv('HOST', "localhost"),
                               port=os.getenv('PORT', 6379),
                               password=password,
                               decode_responses=True)
        conn.ping()
    except Exception:
        traceback.print_exc()
        raise Exception('Redis unavailable')

    price_stream_name = configs.get("PRICE_STREAM").data
    test_stocks = configs.get("TEST_STOCKS").data.split(',')

    for test_stock in test_stocks:
        stock = test_stock.strip()
        priceCol = stock + "EQN"
        t = threading.Thread(target=ingestionTask, args=(stock, price_stream_name, priceCol))
        t.start()
