# # This is a sample Python script.
#
# # Press ⌃R to execute it or replace it with your code.
# # Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
import redis
from redis.commands.json.path import Path
import redis.commands.search.aggregation as aggregations
import redis.commands.search.reducers as reducers
from redis.commands.search.field import TextField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import NumericFilter, Query
from redis_om import (JsonModel, EmbeddedJsonModel)
from datetime import datetime
import pytz
import calendar, time

from pydantic import (PositiveInt, PositiveFloat, AnyHttpUrl, EmailStr)

from faker import Faker
import random
import pandas as pd
#
# # connections
conn = redis.Redis(host='localhost', port='6379')
if not conn.ping():
    raise Exception('Redis unavailable')


if __name__ == '__main__':
    print(str(datetime.now().date())+" 00:00:00")
    print(time.strptime('2022-09-05 09:00:00', '%Y-%m-%d %H:%M:%S'))

    print(int(time.mktime(time.strptime('2022-09-05 09:00:00', '%Y-%m-%d %H:%M:%S'))))
    print(datetime.fromtimestamp(time.mktime(time.strptime('2022-09-05 09:00:00', '%Y-%m-%d %H:%M:%S'))).strftime('%Y-%m-%d %H:%M:%S'))
