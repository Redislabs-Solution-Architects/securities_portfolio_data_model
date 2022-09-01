# sample_trading_data_model

### Data model

# investor:
```json
{
  "id": "",
  "name": "",
  "uid": "",
  "pan": ""
}
```

# SecurityLot
```json
{
  "id": "LOT-9001",
  "account_no": "lotids:ACC-1001",
  "ticker": "AAPL",
  "date": "2022-08-29T14:16:44.482Z",
  "price": 12556,
  "quantity": 200,
  "type": "EQUITY"
}
```
```json
{
  "id": "LOT-9002",
  "account_no": "lotids:ACC-1001",
  "ticker": "CAT",
  "date": "2022-08-29T14:16:44.482Z",
  "price": 18063,
  "quantity": 1200,
  "type": "EQUITY"
}
```


### Search indexes
FT.CREATE idx_trading_security_lot on JSON PREFIX 1 trading:securitylot: SCHEMA $.accountNo as accountNo TEXT 
$.ticker as ticker TAG $.price as price NUMERIC $.quantity as quantity NUMERIC $.type as type TAG

FT.CREATE idx_trading_account on JSON PREFIX 1 trading:account: SCHEMA $.accountNo as accountNo TEXT 
$.retailInvestor as retailInvestor TAG $.accountOpenDate as accountOpenDate TEXT 

### Queries
1. Get all the security lots by account number/id
          - FT.SEARCH idx_trading_security_lot '@accountNo: (ACC10001)' 
2. Get all the security lots by account number/id and ticker
          - FT.SEARCH idx_trading_security_lot '@accountNo: (ACC10001) @ticker:{HDFCBANK}' 
3. Get avg cost price and total quantity of all security inside investor's security portfolio
          - FT.AGGREGATE idx_trading_security_lot '@accountNo: (ACC10001)' GROUPBY 1 @ticker REDUCE AVG 1 @price as avgPrice REDUCE SUM 1 @quantity as totalQuantity


