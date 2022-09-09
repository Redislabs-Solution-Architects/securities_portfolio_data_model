import redis
import time
import pandas as pd
from jproperties import Properties


configs = Properties()
with open('./config/app-config.properties', 'rb') as config_file:
    configs.load(config_file)


if __name__ == '__main__':
    conn = redis.Redis(host=configs.get("HOST").data, port=configs.get("PORT").data)
    global data, i
    if not conn.ping():
        raise Exception('Redis unavailable')
    price_stream_name = configs.get("PRICE_STREAM").data
    data = pd.read_csv("files/" + configs.get("TEST_STOCK").data + "_intraday.csv")
    stock = configs.get("TEST_STOCK").data
    priceCol = stock + "EQN"
    try:
        for i in data.index:
            dateInUnix = int(time.mktime(time.strptime(data['DateTime'][i], configs.get("DATE_FORMAT").data)))
            conn.xadd(price_stream_name,
                      {"ticker": stock, "datetime": data['DateTime'][i], "dateInUnix": dateInUnix,
                       "price": data[priceCol][i]})
            print(str(i+1)+" pricing record generated for "+stock)
            time.sleep(0.5)
        print("Trading recordset generated")
    except Exception as inst:
        print(type(inst))
        print("Exception occurred while generating pricing data"+data[priceCol][i])
        print(data)
        #raise Exception('Exception occurred while generating pricing data. Delete the corrupted data and try again')
