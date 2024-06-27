import traceback
from jproperties import Properties
import redis
import os
import threading

configs = Properties()
with open('../config/app-config.properties', 'rb') as config_file:
    configs.load(config_file)

try:
    password = 'admin'  # os.getenv('PASSWORD')
    if not (password and password.strip()):
        r = redis.Redis(host=os.getenv('HOST', "localhost"),
                        port=os.getenv('PORT', 6379),
                        decode_responses=True)
    else:
        r = redis.Redis(host=os.getenv('HOST', "localhost"),
                        port=os.getenv('PORT', 6379),
                        password=password,
                        decode_responses=True)
    r.ping()
except Exception:
    traceback.print_exc()
    raise Exception('Redis unavailable for alert.py')


def consumeFromPriceStream():
    streamName = configs.get("PRICE_STREAM").data
    groupName = "stock_price_alert_group"
    while True:
        try:
            # Read messages from the price stream
            messages = r.xreadgroup(groupName, "alert_consumer", {streamName: '>'}, block=5000, count=10)

            # key, ticker, datetime,
            # dateInUnix, price

            keys = []
            cursor = 0
            while True:
                cursor, alertKey = r.scan(cursor, match="alert:rule:*", count=10)
                keys.extend(alertKey)
                if cursor == 0:
                    break

            for message in messages:
                for message_id, fields in message[1]:
                    print(f"Alert consumer:: Message ID: {message_id}")
                    for field, value in fields.items():
                        print(f" Received from price stream  {field}: {value}")
                    # Acknowledge the message
                    notification = {'content': fields.items()}
                    r.xadd(configs.get("NOTIFICATION_STREAM").data, notification)
                    r.xack(streamName, groupName, message_id)
        except Exception as e:
            print(f"Error: {e}")
            break


def consumeFromNotificationStream():
    streamName = configs.get("NOTIFICATION_STREAM").data
    notification_group = configs.get("NOTIFICATION_GROUP_NAME").data
    while True:
        try:
            # Read messages from the price stream
            notifications = r.xreadgroup(notification_group, "notification_consumer", {streamName: '>'}, block=5000, count=10)
            for message in notifications:
                for message_id, fields in message[1]:
                    print(f"notification consumer:: Message ID: {message_id}")
                    for field, value in fields.items():
                        print(f" Received from notification stream  {field}: {value}")
                    # Acknowledge the message
                    r.xack(streamName, notification_group, message_id)
        except Exception as e:
            print(f"Error: {e}")
            break


if __name__ == '__main__':
    t1 = threading.Thread(target=consumeFromPriceStream)
    t2 = threading.Thread(target=consumeFromNotificationStream)
    t1.start()
    t2.start()
