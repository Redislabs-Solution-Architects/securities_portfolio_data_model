import time
import pandas as pd
from jproperties import Properties
import threading
import sys
import os

sys.path.append(os.path.abspath('redis_connection'))
from connection import RedisConnection

configs = Properties()
with open('config/app-config.properties', 'rb') as config_file:
    configs.load(config_file)


def ingestionTask(file, path):
    try:
        data = pd.read_csv(path+file)
        stock = file[:-4]
        for i, row in data.iterrows():
            dateInUnix = int(time.mktime(time.strptime(row['Date'], configs.get("DATE_FORMAT_REPORT").data)))
            ts.add("ts_historical_" + stock + ":o", dateInUnix*1000, row['Open'], duplicate_policy='last')
            ts.add("ts_historical_" + stock + ":c", dateInUnix*1000, row['Close'], duplicate_policy='last')
            ts.add("ts_historical_" + stock + ":h", dateInUnix*1000, row['High'], duplicate_policy='last')
            ts.add("ts_historical_" + stock + ":l", dateInUnix*1000, row['Low'], duplicate_policy='last')
        print(f"Historic prices for {stock} successfully loaded in Redis")
    except Exception as inst:
        print(type(inst))
        print(f"Exception occurred while loading pricing data for {stock}")
        print(row)
        raise Exception('Exception occurred while loading pricing data. Delete the corrupted data and try again')


if __name__ == '__main__':
    conn = RedisConnection().get_connection()
    ts = conn.ts()
    path = "files/for_report/"
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    for file in files:
        t = threading.Thread(target=ingestionTask, args=(file, path))
        t.start()
