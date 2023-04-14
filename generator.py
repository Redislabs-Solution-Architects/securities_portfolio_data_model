import redis
from faker import Faker
from jproperties import Properties
import time
import pandas as pd
import os

configs = Properties()
with open('./config/app-config.properties', 'rb') as config_file:
    configs.load(config_file)
Faker.seed(0)
fake = Faker('en_IN')


def generate_trading_data(conn, file, ticker):
    chance = 70
    investorIdPrefix = "INV1000"
    accountIdPrefix = "ACC1000"
    accountCount = int(configs.get("ACCOUNT_COUNT").data)
    try:
        for accs in range(accountCount):
            investorId = investorIdPrefix + str(accs)
            accountNo = accountIdPrefix + str(accs)
            securityLotPrefix = "trading:securitylot:" + accountNo + ":"
            investor = {
                "id": investorId, "name": fake.name(), "uid": fake.aadhaar_id(),
                "pan": fake.bothify("?????####?"), "email": fake.email(), "phone": fake.phone_number()
            }
            account = {
                "id": accountNo, "investorId": investorId, "accountNo": accountNo,
                "accountOpenDate": str(fake.date_between(start_date='-3y', end_date='-2y')),
                "accountCloseDate": '', "retailInvestor": True
            }
            conn.json().set("trading:investor:" + investorId, "$", investor)
            conn.json().set("trading:account:" + accountNo, "$", account)
            stock = pd.read_csv(file)
            for i in stock.index:
                buy = fake.boolean(chance_of_getting_true=chance)
                chance = chance - 1
                if chance < 0:
                    chance = 70
                if buy:
                    dateInUnix = int(time.mktime(time.strptime(stock['Date '][i], "%d-%b-%Y")))
                    buyingPrice = float(str(stock['OPEN '][i]).replace(',', ''))*100

                    quantity = fake.pyint(min_value=5, max_value=100)
                    secLotId = fake.lexify("????").upper() + str(i) + str(fake.random_number(digits=8, fix_len=True))
                    securityLot = {
                        "id": secLotId, "accountNo": accountNo, "ticker": ticker,
                        "date": dateInUnix, "price": buyingPrice, "quantity": quantity,
                        "lotValue": buyingPrice*quantity, "type": "EQUITY"
                    }
                    conn.json().set(securityLotPrefix + secLotId, "$", securityLot)
            print("Generated data for account "+str(accs+1) +" of "+str(accountCount))
    except Exception as inst:
        print(type(inst))
        print("Exception occurred while generating trading data")


if __name__ == '__main__':
    conn = redis.Redis(host=os.getenv('HOST', "localhost"),
                       port=os.getenv('PORT', 6379),
                       password=os.getenv('PASSWORD', "admin"))
    if not conn.ping():
        raise Exception('Redis unavailable')
    try:
        # Generating trading data for 2 stocks: RDBFOODS and RDBMOTORS
        generate_trading_data(conn, "files/rdbfoods.csv", "RDBFOODS")
        print("Trading recordset generated for RDBFOODS")
        generate_trading_data(conn, "files/rdbmotors.csv", "RDBMOTORS")
        print("Trading recordset generated for RDBMOTORS")
    except Exception as inst:
        print(type(inst))
        print(inst)
        raise Exception('Exception occurred while generating data. Delete the corrupted data and try again')