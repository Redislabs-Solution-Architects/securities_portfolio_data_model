use stock_data;
CREATE TABLE investor (
    id VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    uid VARCHAR(20),
    pan CHAR(10),
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    PRIMARY KEY (id)
);

CREATE TABLE account (
    id VARCHAR(255) NOT NULL,
    investorId VARCHAR(255) NOT NULL,
    accountNo VARCHAR(255) NOT NULL,
    accountOpenDate VARCHAR(50),
    accountCloseDate VARCHAR(50),
    retailInvestor BOOLEAN,
    PRIMARY KEY (id)
);

CREATE TABLE securitylot (
    id VARCHAR(255) NOT NULL,
    accountNo VARCHAR(255) NOT NULL,
    ticker VARCHAR(50),
    date BIGINT,
    price DECIMAL(10, 2),
    quantity BIGINT,
    lotValue DECIMAL(15, 2),
    type VARCHAR(50),
    PRIMARY KEY (id)
);

