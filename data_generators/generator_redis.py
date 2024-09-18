from faker import Faker
from jproperties import Properties
import time
import pandas as pd
import os
import traceback
import sys

sys.path.append(os.path.abspath('redis_connection'))
from connection import RedisConnection


configs = Properties()
with open('config/app-config.properties', 'rb') as config_file:
    configs.load(config_file)
Faker.seed(0)
fake = Faker('en_IN')


def generate_investor_account_data():
    investorIdPrefix = "INV1000"
    accountIdPrefix = "ACC1000"
    accountCount = os.getenv('ACCOUNT_RECORD_COUNT', 500)
    try:
        for accs in range(int(accountCount)):
            investorId = investorIdPrefix + str(accs)
            accountNo = accountIdPrefix + str(accs)
            name = fake.name()
            address = fake.address()
            investor = {
                "id": investorId, "name": name, "uid": fake.aadhaar_id(),
                "pan": fake.bothify("?????####?"), "email": fake.email(), "phone": fake.phone_number(),
                "address": address
            }
            account = {
                "id": accountNo, "investorId": investorId, "accountNo": accountNo,
                "accountOpenDate": str(fake.date_between(start_date='-3y', end_date='-2y')),
                "accountCloseDate": '', "retailInvestor": True
            }
            conn.json().set("trading:investor:" + investorId, "$", investor)
            conn.json().set("trading:account:" + accountNo, "$", account)
            generate_trading_data(conn, accountNo)
        print(str(accountCount) + " portfolio records generated")
    except Exception as inst:
        print(type(inst))
        traceback.print_exc()
        print("Exception occurred while generating investor & account data")


def generate_trading_data(conn, accountNo):
    path = "files/for_tnxs/"
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    for file in files:
        df = pd.read_csv(path + file)
        ticker = file[:-4]
        for i, row in df.iterrows():
            chance = 10
            try:
                securityLotPrefix = "trading:securitylot:" + accountNo + ":"
                buy = fake.boolean(chance_of_getting_true=chance)
                chance = chance - 1
                if chance < 0:
                    chance = 10
                if buy:
                    dateInUnix = int(time.mktime(time.strptime(row['Date '], "%d-%b-%Y")))
                    buyingPrice = float(str(row['OPEN ']).replace(',', '')) * 100

                    max_value = fake.pyint(min_value=1, max_value=18)
                    quantity = fake.pyint(min_value=1, max_value=max_value)
                    secLotId = fake.lexify("????").upper() + str(i) + str(fake.random_number(digits=8, fix_len=True))
                    securityLot = {
                        "id": secLotId, "accountNo": accountNo, "ticker": ticker,
                        "date": dateInUnix, "price": buyingPrice, "quantity": quantity,
                        "lotValue": buyingPrice * quantity, "type": "EQUITY"
                    }
                    conn.json().set(securityLotPrefix + secLotId, "$", securityLot)
            except Exception as inst:
                print(type(inst))
                print("Exception occurred while generating trading data")


if __name__ == '__main__':
    conn = RedisConnection().get_connection()
    try:
        # Generate investor, account & trading data
        generate_investor_account_data()
    except Exception as inst:
        print(type(inst))
        print(inst)
        raise Exception('Exception occurred while generating data. Delete the corrupted data and try again')
