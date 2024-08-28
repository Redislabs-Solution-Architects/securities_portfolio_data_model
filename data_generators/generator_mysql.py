from faker import Faker
from jproperties import Properties
import time
import pandas as pd
import os
import mysql.connector
from mysql.connector import Error

configs = Properties()
with open('config/app-config.properties', 'rb') as config_file:
    configs.load(config_file)
Faker.seed(0)
fake = Faker('en_IN')

def generate_investor_account_data(conn):
    cursor = conn.cursor()
    investorIdPrefix = "INV1000"
    accountIdPrefix = "ACC1000"
    accountCount = os.getenv('ACCOUNT_RECORD_COUNT', 1000)
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
            cursor.execute("INSERT INTO investor (id,name,uid,pan,email,phone,address) VALUES (%s, %s,%s,%s,%s,%s,%s)", (investorId,name,uid,pan,email,phone,address))
            accountOpenDate =  str(fake.date_between(start_date='-3y', end_date='-2y'))
            accountCloseDate = ''
            retailInvestor = True
            cursor.execute('INSERT INTO account (id,investorId,accountNo,accountOpenDate,accountCloseDate,retailInvestor) values (%s,%s,%s,%s,%s,%s)' ,(accountNo,investorId,accountNo,accountOpenDate,accountCloseDate,retailInvestor))
            generate_trading_data(conn, "files/ABCBANK.csv", "HDFCBANK", accountNo)
            generate_trading_data(conn, "files/ABCFOOD.csv", "NESTLE", accountNo)
            generate_trading_data(conn, "files/ABCMOTORS.csv", "TATAMOTORS", accountNo)
            print("Data generated - "+str(accs+1) +" of "+str(accountCount))
       conn.commit()
    except Exception as inst:
        print(type(inst))
        print("Exception occurred while generating investor & account data")


def generate_trading_data(conn, file, ticker, accountNo):
    curs = conn.cursor()
    chance = 70
    try:
        stock = pd.read_csv(file)
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
                lotValue = buyingPrice * quantity
                curs.execute("INSERT INTO securitylot(id,accountNo,ticker,date,price,quantity,lotValue,type) values (%s,%s,%s,%s,%s,%s,%s,%s)",(secLotId,accountNo,ticker,dateInUnix,buyingPrice,quantity,lotValue,"EQUITY"))
        conn.commit()
    except Exception as inst:
        print(type(inst))
        print("Exception occurred while generating trading data")


if __name__ == '__main__':
    conn = None
    try:
        conn = mysql.connector.connect(
            host='localhost',
            database='stock_data',
            user='abhishek',
            password='admin')
        if conn.is_connected():
            print('Connected to MySQL database')
        generate_investor_account_data(conn)
    except Exception as inst:
        print(type(inst))
        print(inst)
        raise Exception('MySQL may not be available')
    finally:
        if conn.is_connected():
            conn.close()