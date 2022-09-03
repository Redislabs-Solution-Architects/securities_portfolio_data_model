import redis
from faker import Faker

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

    conn.json().set("trading:investor:" + investorId, "$", investor2)
    conn.json().set("trading:account:" + accountNo, "$", account2)
    conn.json().set("trading:investor:INV10002", "$", investor)
    conn.json().set("trading:account:ACC10002", "$", account)

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

    price_hdfc = [139450, 158670, 135300]
    dates_hdfc = ["16/12/2020", "09/02/2021", "12/04/2021"]
    quantity_hdfc = [10, 20, 80]
    for index in range(3):
        secLotId = fake.lexify("????").upper() + str(fake.random_number(digits=6, fix_len=True))
        securityLot = {
            "id": secLotId, "accountNo": accountNo, "ticker": "HDFCBANK",
            "date": dates_hdfc[index], "price": price_hdfc[index],
            "quantity": quantity_hdfc[index], "type": "EQUITY"
        }
        conn.json().set(securityLotPrefix + secLotId, "$", securityLot)

    price_maruti = [568145, 654500]
    dates_maruti = ["30/06/2020", "28/04/2021"]
    quantity_maruti = [12, 35]
    for index in range(2):
        secLotId = fake.lexify("????").upper() + str(fake.random_number(digits=6, fix_len=True))
        securityLot = {
            "id": secLotId, "accountNo": accountNo, "ticker": "MARUTI",
            "date": dates_maruti[index], "price": price_maruti[index],
            "quantity": quantity_maruti[index], "type": "EQUITY"
        }
        conn.json().set(securityLotPrefix + secLotId, "$", securityLot)


if __name__ == '__main__':
    conn = redis.Redis(host='localhost', port=6379)
    if not conn.ping():
        raise Exception('Redis unavailable')
    try:
        generate_trading_data(conn)
        print("Trading recordset generated")
    except Exception as inst:
        print(type(inst))
        print(inst)
        raise Exception('Exception occurred while generating data. Delete the corrupted data and try again')