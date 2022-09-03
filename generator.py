import redis
import calendar
import time
import pandas as pd

from faker import Faker

Faker.seed(0)
fake = Faker('en_IN')

if __name__ == '__main__':
    #d = calendar.timegm(time.strptime('2021-02-24', '%Y-%m-%d'))

    d = calendar.timegm(time.strptime('02/09/22 9:00', '%d/%m/%y %H:%M'))

    print(d)
