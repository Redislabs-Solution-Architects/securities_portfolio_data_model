import time
import pandas as pd
from jproperties import Properties
import threading
import sys
import os
import numpy as np

sys.path.append(os.path.abspath('redis_connection'))
from connection import RedisConnection

configs = Properties()
with open('config/app-config.properties', 'rb') as config_file:
    configs.load(config_file)

def ingestionTask(stock, price_stream_name, priceCol):
    print(f"Pricing data is getting generated for {stock}")
    try:
        data = pd.read_csv("files/" + stock + "_intraday.csv")
        chunk = 500
        for i, row in data.iterrows():
            dateInUnix = int(time.mktime(time.strptime(row['DateTime'], configs.get("DATE_FORMAT").data)))
            conn.xadd(price_stream_name,
                      {"ticker": stock,
                       "datetime": row['DateTime'],
                       "dateInUnix": dateInUnix,
                       "price": row[priceCol]})
            chunk -= 1
            if chunk == 0:
                print(str(i+1)+" pricing record generated for "+stock)
                chunk = 500
            time.sleep(1)
        if chunk > 0:
            print(str(i + 1) + " pricing record generated for " + stock)
        print(f"*** Completed *** [Trading recordset generated for {stock}]")
    except Exception as inst:
        print(type(inst))
        print("Exception occurred while generating pricing data"+row[priceCol])
        print(data)
        raise Exception('Exception occurred while generating pricing data. Delete the corrupted data and try again')


if __name__ == '__main__':
    conn = RedisConnection().get_connection()
    price_stream_name = configs.get("PRICE_STREAM").data
    test_stocks = configs.get("TEST_STOCKS").data.split(',')
    for test_stock in test_stocks:
        stock = test_stock.strip()
        priceCol = stock + "EQN"
        t = threading.Thread(target=ingestionTask, args=(stock, price_stream_name, priceCol))
        t.start()
