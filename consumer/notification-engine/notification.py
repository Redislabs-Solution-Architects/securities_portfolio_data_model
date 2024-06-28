from jproperties import Properties
import threading
import sys
import os
import logging

import uuid
sys.path.append(os.path.abspath('redis_connection'))
from connection import RedisConnection


configs = Properties()
logger = logging.getLogger(__name__)
logging.basicConfig(encoding='utf-8', level=logging.INFO)

with open('config/app-config.properties', 'rb') as config_file:
    configs.load(config_file)
r = RedisConnection().get_connection()


def consumeFromPriceStream():
    logging.info(f"Starting notification rule engine.")
    streamName = configs.get("PRICE_STREAM").data
    groupName = "stock_price_alert_group"
    logging.info(f"Message will be consumed from {streamName} with group name {groupName}")
    while True:
        try:
            # Read messages from the price stream
            messages = r.xreadgroup(groupName, "alert_consumer", {streamName: '>'}, block=5000, count=10)

            for message in messages:
                for message_id, fields in message[1]:
                    print(f"Alert consumer:: Message ID: {message_id}")
                    stock = fields.get('ticker')
                    price = fields.get('price')

                    rule = r.json().get(f'alert:rule:{stock}')
                    notification = ''
                    if not (rule is None):
                        triggerPrice = r.json().get(f'alert:rule:{stock}', "triggerPrice")
                        triggerType = r.json().get(f'alert:rule:{stock}', "triggerType")

                        if 'GT_TRIGGER_PRICE' == triggerType:
                            if price > triggerPrice:
                                notification = {
                                    'message': f'Stock has surpassed the trigger price of {triggerPrice}. '
                                               f'Stock price: {price}'}
                                r.xadd(configs.get("NOTIFICATION_STREAM").data, notification)

                        elif 'LT_TRIGGER_PRICE' == triggerType:
                            if price < triggerPrice:
                                notification = {
                                    'message': f'Stock has fallen below the trigger price of {triggerPrice}. '
                                               f'Stock price: {price}'}
                                r.xadd(configs.get("NOTIFICATION_STREAM").data, notification)

                        elif 'EQ_TRIGGER_PRICE' == triggerType:
                            if price == triggerPrice:
                                notification = {
                                    'message': f'Stock has fallen below the trigger price of {triggerPrice}. '
                                               f'Stock price: {price}'}
                                r.xadd(configs.get("NOTIFICATION_STREAM").data, notification)

                    r.xack(streamName, groupName, message_id)
        except Exception as e:
            print(f"Error: {e}")
            break


if __name__ == '__main__':
    consumeFromPriceStream()
