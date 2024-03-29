from faker import Faker
from jproperties import Properties
import time
import pandas as pd
import os
import psycopg2

configs = Properties()
with open('./config/app-config.properties', 'rb') as config_file:
    configs.load(config_file)
Faker.seed(0)
fake = Faker('en_IN')

def generate_investor_account_data(conn):
    conn.autocommit = True
    curs = conn.cursor()
    investorIdPrefix = "INV1000"
    accountIdPrefix = "ACC1000"
    accountCount = int(configs.get("ACCOUNT_RECORD_COUNT").data)
    try:
       for accs in range(accountCount):
            investorId = investorIdPrefix + str(accs)
            accountNo = accountIdPrefix + str(accs)
            name = fake.name()
            address = fake.address()
            uid = fake.aadhaar_id()
            pan = fake.bothify("?????####?")
            email = fake.email()
            phone = fake.phone_number()
            pginvestor = curs.execute("INSERT INTO investor (id,name,uid,pan,email,phone,address) VALUES (%s, %s,%s,%s,%s,%s,%s)" , (investorId,name,uid,pan,email,phone,address))
            accountOpenDate =  str(fake.date_between(start_date='-3y', end_date='-2y'))
            accountCloseDate = ''
            retailInvestor = True
            pgaccount = curs.execute('INSERT INTO account (id,"investorId","accountNo","accountOpenDate","accountCloseDate","retailInvestor") values (%s,%s,%s,%s,%s,%s)' ,(accountNo,investorId,accountNo,accountOpenDate,accountCloseDate,retailInvestor))
            generate_trading_data(conn, "files/rdbbank.csv", "RDBBANK", accountNo)
            generate_trading_data(conn, "files/rdbfoods.csv", "RDBFOODS", accountNo)
            generate_trading_data(conn, "files/rdbmotors.csv", "RDBMOTORS", accountNo)
            generate_trading_data(conn, "files/rdbbank.csv", "RDBBANK", accountNo)
            print("Data generated - "+str(accs+1) +" of "+str(accountCount))
    except Exception as inst:
        print(type(inst))
        print("Exception occurred while generating investor & account data")


def generate_trading_data(conn, file, ticker, accountNo):
    conn.autocommit = True
    curs = conn.cursor()
    chance = 70
    try:
        stock = pd.read_csv(file)
        securityLotPrefix = "trading:securitylot:" + accountNo + ":"
        for i in stock.index:
            buy = fake.boolean(chance_of_getting_true=chance)
            chance = chance - 1
            if chance < 0:
                chance = 70
            if buy:
                dateInUnix = int(time.mktime(time.strptime(stock['Date '][i], "%d-%b-%Y")))
                buyingPrice = float(str(stock['OPEN '][i]).replace(',', '')) * 100
                quantity = fake.pyint(min_value=5, max_value=50)
                secLotId = fake.lexify("????").upper() + str(i) + str(fake.random_number(digits=8, fix_len=True))
                securityLot = {
                    "id": secLotId, "accountNo": accountNo, "ticker": ticker,
                    "date": dateInUnix, "price": buyingPrice, "quantity": quantity,
                    "lotValue": buyingPrice * quantity, "type": "EQUITY"
                }
                lotValue = buyingPrice * quantity
                type = "EQUITY"
                pgsecuritylot =  curs.execute("INSERT INTO securitylot  values (%s,%s,%s,%s,%s,%s,%s,%s)",(secLotId,accountNo,ticker,dateInUnix,buyingPrice,quantity,lotValue,type))
    except Exception as inst:
        print(type(inst))
        print("Exception occurred while generating trading data")



if __name__ == '__main__':
    conn = psycopg2.connect(
     database="<<DATABASE>>", user='<<USRE>>', password='<<PASSWORD>>', host='<<HOST>>', port= '<<PORT>>'
    )
    conn.autocommit = True
    cursor = conn.cursor()
    try:
        generate_investor_account_data(conn)
    except Exception as inst:
        print(type(inst))
        print(inst)
        raise Exception('Exception occurred while generating data. Delete the corrupted data and try again')
