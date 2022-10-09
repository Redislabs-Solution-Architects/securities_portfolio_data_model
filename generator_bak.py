import redis
from faker import Faker
from jproperties import Properties

configs = Properties()
with open('./config/app-config.properties', 'rb') as config_file:
    configs.load(config_file)
Faker.seed(0)
fake = Faker('en_IN')


def generate_trading_data(conn):
    investorId = "INV10001"
    accountNo = "ACC10001"
    securityLotPrefix = "trading:securitylot:" + accountNo + ":"
    investor = {
        "id": investorId, "name": fake.name(), "uid": fake.aadhaar_id(),
        "pan": fake.bothify("?????####?"), "email": fake.email(), "phone": fake.phone_number()
    }
    account = {
        "id": accountNo, "investorId": investorId, "accountNo": accountNo,
        "accountOpenDate": str(fake.date_between(start_date='-3y', end_date='today')),
        "accountCloseDate": '', "retailInvestor": True
    }

    # Other investor with no trading data
    investor2 = {
        "id": "INV10002", "name": fake.name(), "uid": fake.aadhaar_id(),
        "pan": fake.bothify("?????####?"), "email": fake.email(), "phone": fake.phone_number()
    }
    account2 = {
        "id": "ACC10002", "investorId": "INV10002", "accountNo": "ACC10002",
        "accountOpenDate": str(fake.date_between(start_date='-2y', end_date='today')),
        "accountCloseDate": '', "retailInvestor": True
    }

    conn.json().set("trading:investor:" + investorId, "$", investor)
    conn.json().set("trading:account:" + accountNo, "$", account)
    conn.json().set("trading:investor:INV10002", "$", investor2)
    conn.json().set("trading:account:ACC10002", "$", account2)

    price_telco = [16555, 29220, 29050, 29460, 29510, 30300, 29255]
    dates_telco = ["20/11/2020", "22/04/2021", "23/04/2021", "26/04/2021", "27/04/2021", "28/04/2021", "30/04/2021"]
    quantity_telco = [10, 20, 100, 25, 20, 10, 30]
    for index in range(7):
        secLotId = fake.lexify("????").upper() + str(fake.random_number(digits=6, fix_len=True))
        securityLot = {
            "id": secLotId, "accountNo": accountNo, "ticker": "TELCO",
            "date": dates_telco[index], "price": price_telco[index],
            "quantity": quantity_telco[index], "type": "EQUITY"
        }
        conn.json().set(securityLotPrefix + secLotId, "$", securityLot)

    price_stock1 = [139450, 158670, 135300]
    dates_stock1 = ["16/12/2020", "09/02/2021", "12/04/2021"]
    quantity_stock1 = [10, 20, 80]
    for index in range(3):
        secLotId = fake.lexify("????").upper() + str(fake.random_number(digits=6, fix_len=True))
        securityLot = {
            "id": secLotId, "accountNo": accountNo, "ticker": configs.get("TEST_STOCK").data,
            "date": dates_stock1[index], "price": price_stock1[index],
            "quantity": quantity_stock1[index], "type": "EQUITY"
        }
        conn.json().set(securityLotPrefix + secLotId, "$", securityLot)

    price_stock2 = [568145, 654500]
    dates_stock2 = ["30/06/2020", "28/04/2021"]
    quantity_stock2 = [12, 35]
    for index in range(2):
        secLotId = fake.lexify("????").upper() + str(fake.random_number(digits=6, fix_len=True))
        securityLot = {
            "id": secLotId, "accountNo": accountNo, "ticker": configs.get("TEST_STOCK2").data,
            "date": dates_stock2[index], "price": price_stock2[index],
            "quantity": quantity_stock2[index], "type": "EQUITY"
        }
        conn.json().set(securityLotPrefix + secLotId, "$", securityLot)


if __name__ == '__main__':
    conn = redis.Redis(host=configs.get("HOST").data, port=configs.get("PORT").data, password=configs.get("PASSWORD").data)
    if not conn.ping():
        raise Exception('Redis unavailable')
    try:
        generate_trading_data(conn)
        print("Trading recordset generated")
    except Exception as inst:
        print(type(inst))
        print(inst)
        raise Exception('Exception occurred while generating data. Delete the corrupted data and try again')