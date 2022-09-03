import redis
import calendar
import time
import pandas as pd


if __name__ == '__main__':
    conn = redis.Redis(host='localhost', port=6379)
    if not conn.ping():
        raise Exception('Redis unavailable')
    price_stream_name = "price_update_stream"

    try:
        data = pd.read_csv("files/HDFCBANK_intraday.csv")
        for i in data.index:
            dateInUnix = calendar.timegm(time.strptime(data['DateTime'][i], '%d/%m/%y %H:%M'))
            conn.xadd(price_stream_name,
                      {"ticker": "HDFCBANK", "datetime": data['DateTime'][i], "dateInUnix": dateInUnix,
                       "price": data['Price'][i]})
            time.sleep(2)
        print("Trading recordset generated")
    except Exception as inst:
        print(type(inst))
        print(inst)
        raise Exception('Exception occurred while generating pricing data. Delete the corrupted data and try again')
